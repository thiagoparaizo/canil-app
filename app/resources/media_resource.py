import uuid
from flask import request, send_file, current_app, g # Import g for tenant_id
from flask_restx import Namespace, Resource, fields, reqparse, abort
from werkzeug.datastructures import FileStorage
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import date # Needed for date conversion if payload contains date strings

from app import db
from app.models.media import Arquivo, ImagemAnimal, VideoAnimal, DocumentoAnimal
from app.models.animal import Animal
from app.services.media_service import DropboxService

media_ns = Namespace('media', description='Media file operations')

# Request Parser for file uploads
file_upload_parser = reqparse.RequestParser()
file_upload_parser.add_argument('file', type=FileStorage, location='files', required=True, help='File to upload')
file_upload_parser.add_argument('animal_id', type=int, location='form', required=False, help='ID of the associated animal')
file_upload_parser.add_argument('categoria', type=str, location='form', required=False, help='Category of the file (e.g., photo, video, document)')
file_upload_parser.add_argument('descricao', type=str, location='form', required=False, help='Description of the file')
file_upload_parser.add_argument('tipo_documento', type=str, location='form', required=False, help='Type of document (if category is document)')
file_upload_parser.add_argument('data_emissao', type=str, location='form', required=False, help='Issue date for document')
file_upload_parser.add_argument('data_validade', type=str, location='form', required=False, help='Expiry date for document')
file_upload_parser.add_argument('orgao_emissor', type=str, location='form', required=False, help='Issuing authority for document')
file_upload_parser.add_argument('principal', type=bool, location='form', required=False, help='Is this the principal image (if category is photo)')
file_upload_parser.add_argument('ordem', type=int, location='form', required=False, help='Order for images')
file_upload_parser.add_argument('duracao', type=float, location='form', required=False, help='Duration of the video in seconds') # Assuming float for seconds
file_upload_parser.add_argument('qualidade', type=str, location='form', required=False, help='Quality of the video (e.g., SD, HD)')


# API Model for Arquivo response
arquivo_model = media_ns.model('Arquivo', {
    'id': fields.Integer(readOnly=True),
    'nome': fields.String(required=True),
    'nome_original': fields.String(required=True),
    'caminho': fields.String(required=True),
    'tipo': fields.String(required=True),
    'tamanho': fields.Float(required=True),
    'data_upload': fields.DateTime(required=True),
    'descricao': fields.String,
    'publico': fields.Boolean,
    'hash': fields.String,
    'animal_id': fields.Integer,
    'categoria': fields.String, # For ImageAnimal/VideoAnimal
    'ordem': fields.Integer, # For ImageAnimal
    'principal': fields.Boolean, # For ImageAnimal
    'duracao': fields.Float, # For VideoAnimal
    'qualidade': fields.String, # For VideoAnimal
    'tipo_documento': fields.String, # For DocumentoAnimal
    'data_emissao': fields.Date, # For DocumentoAnimal
    'data_validade': fields.Date, # For DocumentoAnimal
    'orgao_emissor': fields.String, # For DocumentoAnimal
    'verificado': fields.Boolean, # For DocumentoAnimal
    'url': fields.String(readOnly=True, description='Shareable link from Dropbox')
})

# Helper to get current tenant ID (replace with actual logic based on your setup)
# This assumes tenant_id is stored in Flask g context after middleware runs.
def get_current_tenant_id():
    if hasattr(g, 'current_tenant_id'):
        return g.current_tenant_id
    # Fallback or error handling if tenant_id is not in g
    current_app.logger.error("Tenant context not available in Flask g.")
    abort(500, "Internal server error: Tenant context missing.")


@media_ns.route('/arquivos')
class ArquivoList(Resource):
    @media_ns.expect(file_upload_parser)
    @media_ns.marshal_with(arquivo_model, code=201)
    def post(self):
        """Upload a new file"""
        try:
            current_tenant_id = get_current_tenant_id()

            args = file_upload_parser.parse_args(strict=True) # Use strict=True for reqparse
            uploaded_file = args['file']
            animal_id = args.get('animal_id')
            categoria = args.get('categoria')
            descricao = args.get('descricao')
            tipo_documento = args.get('tipo_documento')
            data_emissao_str = args.get('data_emissao')
            data_validade_str = args.get('data_validade')
            orgao_emissor = args.get('orgao_emissor')
            principal = args.get('principal')
            ordem = args.get('ordem')
            duracao = args.get('duracao')
            qualidade = args.get('qualidade')

            if not uploaded_file:
                # This check is also done by required=True in reqparse, but can be a safeguard
                media_ns.abort(400, message='No file provided')

            # Read file content and get metadata
            file_content = uploaded_file.read()
            original_filename = uploaded_file.filename
            file_size = len(file_content)
            file_type = uploaded_file.mimetype or 'application/octet-stream'

            # --- Start Validation ---
            if animal_id:
                 animal = Animal.query.filter_by(id=animal_id, tenant_id=current_tenant_id).first()
                 if not animal:
                     media_ns.abort(404, message=f"Animal with ID {animal_id} not found for this tenant.")

            valid_categories = ['photo', 'video', 'document', None]
            if categoria not in valid_categories:
                 media_ns.abort(400, message=f"Invalid category. Must be one of: {', '.join([c for c in valid_categories if c is not None])}.")

            if categoria == 'document':
                 if not tipo_documento:
                      media_ns.abort(400, message="tipo_documento is required for category 'document'.")
                 try:
                     data_emissao = date.fromisoformat(data_emissao_str) if data_emissao_str else None
                 except ValueError:
                     media_ns.abort(400, message="Invalid date format for data_emissao. Use YYYY-MM-DD.")
                 try:
                     data_validade = date.fromisoformat(data_validade_str) if data_validade_str else None
                 except ValueError:
                     media_ns.abort(400, message="Invalid date format for data_validade. Use YYYY-MM-DD.")
                 # Add validation for orgao_emissor if needed (e.g., min length)

            elif categoria == 'photo':
                 if principal is not None and not isinstance(principal, bool):
                      media_ns.abort(400, message="principal must be a boolean (true/false).")
                 if ordem is not None and (not isinstance(ordem, int) or ordem < 0):
                      media_ns.abort(400, message="ordem must be a non-negative integer.")

            elif categoria == 'video':
                 if duracao is not None and (not isinstance(duracao, (int, float)) or duracao < 0):
                      media_ns.abort(400, message="duracao must be a non-negative number.")
                 if qualidade is not None and not isinstance(qualidade, str):
                      media_ns.abort(400, message="qualidade must be a string.")

            # --- End Validation ---

            # Determine destination path in Dropbox (includes tenant_id)
            destination_folder = f"/{current_tenant_id}"
            if animal_id:
                 destination_folder += f"/animals/{animal_id}"
            else:
                 destination_folder += "/general" # For files not linked to an animal

            # Generate a unique filename to avoid conflicts
            unique_filename = f"{uuid.uuid4()}_{original_filename}"
            destination_path = f"{destination_folder}/{unique_filename}"

            dropbox_service = DropboxService() # Instantiate the service

            # Upload file to Dropbox (service includes tenant_id in path)
            # The service method should handle prepending the tenant_id path
            # Assuming upload_file now expects tenant_id, file_content, and relative_path
            dropbox_metadata = dropbox_service.upload_file(file_content, destination_path) # Service adds tenant_id internally


            # Prepare data for model instantiation
            model_data = {
                'nome': unique_filename,
                'nome_original': original_filename,
                'caminho': destination_path, # Full path including tenant_id
                'tipo': file_type,
                'tamanho': file_size,
                'data_upload': datetime.utcnow(), # Assuming datetime import
                'descricao': descricao,
                'publico': False, # Default public status
                'animal_id': animal_id,
                'tenant_id': current_tenant_id # Explicitly assign tenant_id
            }


            # Instantiate the correct class based on category
            if categoria == 'photo':
                new_arquivo = ImagemAnimal(**model_data, principal=principal, ordem=ordem)
            elif categoria == 'video':
                 new_arquivo = VideoAnimal(**model_data, duracao=duracao, qualidade=qualidade)
            elif categoria == 'document':
                 new_arquivo = DocumentoAnimal(**model_data, tipo_documento=tipo_documento,
                                               data_emissao=data_emissao, data_validade=data_validade,
                                               orgao_emissor=orgao_emissor, verificado=False) # Default verificado
            else:
                 new_arquivo = Arquivo(**model_data)


            db.session.add(new_arquivo)
            db.session.commit()

            # Optionally, get the shareable link immediately after saving to DB
            # This adds another Dropbox call, might be better to get on demand in GET
            # new_arquivo.url = dropbox_service.get_shareable_link(new_arquivo.caminho) # Use full path


            # Refresh the object to ensure relationships/calculated fields are available if needed
            db.session.refresh(new_arquivo)

            return new_arquivo, 201

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during file upload: {e}")
            media_ns.abort(500, message='Database error occurred during file upload.')
        except Exception as e:
            # Catch Dropbox API errors or other exceptions
            db.session.rollback() # Rollback in case a DB object was created before Dropbox error
            current_app.logger.error(f"An unexpected error occurred during file upload: {e}")
            media_ns.abort(500, message=f'An error occurred during file upload: {e}')


@media_ns.route('/arquivos/<int:id>')
@media_ns.param('id', 'The file identifier')
class ArquivoResource(Resource):
    @media_ns.marshal_with(arquivo_model)
    def get(self, id):
        """Retrieve a file by ID"""
        try:
            current_tenant_id = get_current_tenant_id()

            # Filter by tenant_id
            arquivo = Arquivo.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                description=f"File with ID {id} not found for this tenant"
            )

            dropbox_service = DropboxService()
            # get_shareable_link service method should handle full path
            arquivo.url = dropbox_service.get_shareable_link(arquivo.caminho)
            return arquivo

        except Exception as e:
            current_app.logger.error(f"An error occurred retrieving file {id}: {e}")
            media_ns.abort(500, message=f'An error occurred retrieving the file: {e}')

    @media_ns.expect(arquivo_model, validate=False) # validate=False allows partial updates
    @media_ns.marshal_with(arquivo_model)
    def put(self, id):
        """Update file metadata by ID"""
        try:
            current_tenant_id = get_current_tenant_id()

            # Filter by tenant_id to get the file
            arquivo = Arquivo.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"File with ID {id} not found for this tenant"
            )

            update_data = media_ns.payload

            # Define fields that are allowed to be updated
            allowed_update_fields = [
                'descricao', 'publico',
                # Subclass specific fields - check type before applying
                'categoria', 'ordem', 'principal', # ImageAnimal
                'duracao', 'qualidade', # VideoAnimal
                'tipo_documento', 'data_emissao', 'data_validade', 'orgao_emissor', 'verificado' # DocumentoAnimal
            ]

            # Explicitly prevent updates to immutable fields
            immutable_fields = ['id', 'nome', 'nome_original', 'caminho', 'tipo', 'tamanho', 'data_upload', 'hash', 'tenant_id']
            # Add 'animal_id' to immutable if re-association is not allowed via PUT
            # immutable_fields.append('animal_id') # Uncomment if animal_id cannot be changed

            for field in immutable_fields:
                if field in update_data:
                    media_ns.abort(400, message=f"Field \'{field}\' cannot be updated.")

            # Handle potential update to animal_id separately if allowed
            if 'animal_id' in update_data:
                 new_animal_id = update_data['animal_id']
                 if new_animal_id is not None:
                     # Validate if the new animal exists and belongs to the current tenant
                     new_animal = Animal.query.filter_by(id=new_animal_id, tenant_id=current_tenant_id).first()
                     if not new_animal:
                         media_ns.abort(404, message=f"New Animal ID {new_animal_id} not found for this tenant for re-association.")
                     arquivo.animal_id = new_animal_id
                 else:
                      # Allow setting animal_id to None
                      arquivo.animal_id = None

            # Apply updates for allowed fields
            for field in allowed_update_fields:
                if field in update_data:
                    value = update_data[field]

                    # --- Start Validation for Update Data ---
                    if field in ['data_emissao', 'data_validade']:
                         if isinstance(value, str):
                             if value: # Check if string is not empty
                                 try:
                                     setattr(arquivo, field, date.fromisoformat(value))
                                 except ValueError:
                                     media_ns.abort(400, message=f"Invalid date format for {field}. Use YYYY-MM-DD.")
                             else:
                                 setattr(arquivo, field, None) # Set to None if empty string was provided
                         elif value is not None:
                              # Allow None or actual Date objects if API client sends them
                              setattr(arquivo, field, value)
                         else:
                              setattr(arquivo, field, None) # Allow setting to None


                    elif field == 'principal':
                         if not isinstance(value, bool):
                              media_ns.abort(400, message="principal must be a boolean.")
                         setattr(arquivo, field, value)

                    elif field == 'ordem':
                         if not isinstance(value, int) or value < 0:
                              media_ns.abort(400, message="ordem must be a non-negative integer.")
                         setattr(arquivo, field, value)

                    elif field == 'duracao':
                         if not isinstance(value, (int, float)) or value < 0:
                              media_ns.abort(400, message="duracao must be a non-negative number.")
                         setattr(arquivo, field, value)

                    elif field == 'qualidade':
                         if not isinstance(value, str):
                              media_ns.abort(400, message="qualidade must be a string.")
                         setattr(arquivo, field, value)

                    # Add other specific field validations here

                    else:
                        # For other allowed fields, just set the value
                        setattr(arquivo, field, value)
                    # --- End Validation for Update Data ---


            db.session.commit()
            return arquivo, 200

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during file update {id}: {e}")
            media_ns.abort(500, message='Database error occurred during file update.')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during file update {id}: {e}")
            media_ns.abort(500, message=f'An error occurred during file update: {e}')


    def delete(self, id):
        """Delete a file by ID"""
        try:
            current_tenant_id = get_current_tenant_id()

            # Filter by tenant_id to get the file
            arquivo = Arquivo.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"File with ID {id} not found for this tenant"
            )

            dropbox_service = DropboxService()

            # Delete file from Dropbox first (service handles full path)
            # Pass tenant_id to the service method if needed
            dropbox_service.delete_file(arquivo.caminho) # Service should handle tenant_id internally


            # If Dropbox deletion is successful, delete from database
            db.session.delete(arquivo)
            db.session.commit()

            return '', 204 # 204 No Content on successful deletion

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during file deletion {id}: {e}")
            media_ns.abort(500, message='Database error occurred during file deletion.')
        except Exception as e:
             db.session.rollback() # Rollback if DB deletion fails after Dropbox deletion
             current_app.logger.error(f"An unexpected error occurred during file deletion {id}: {e}")
             media_ns.abort(500, message=f'An error occurred during file deletion: {e}')

# Helper endpoint for direct download if needed (optional, distinct from GET)
@media_ns.route('/arquivos/<int:id>/download')
class ArquivoDownload(Resource):
    def get(self, id):
        """Download a file by ID (via Dropbox)"""
        try:
            current_tenant_id = get_current_tenant_id()

            # Filter by tenant_id to get the file
            arquivo = Arquivo.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"File with ID {id} not found for this tenant"
            )

            dropbox_service = DropboxService()
            # download_file service method should handle full path
            file_content = dropbox_service.download_file(arquivo.caminho) # Service should handle tenant_id internally

            # Return the file content as a response
            # Ensure you have the correct mimetype
            return send_file(
                file_content,
                mimetype=arquivo.tipo,
                as_attachment=True,
                download_name=arquivo.nome_original,
                 # Use BytesIO if file_content is a bytes object
                # If file_content is bytes, wrap it: from io import BytesIO; BytesIO(file_content)
                # This depends on what dropbox_service.download_file returns
                # Assuming it returns bytes, wrap it:
                # from io import BytesIO
                # BytesIO(file_content)
                # If it returns a file-like object, use as is.
                # Let's assume it returns bytes and wrap it for send_file
                 data=file_content # Use data= for Flask 2.0+ send_file from bytes
            )

        except Exception as e:
            current_app.logger.error(f"An error occurred during download {id}: {e}")
            media_ns.abort(500, message=f'An error occurred during download: {e}')