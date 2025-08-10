import uuid
from flask import request, send_file, current_app
from flask_restx import Namespace, Resource, fields, reqparse, abort
from werkzeug.datastructures import FileStorage
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError
from datetime import date  # Needed for date conversion if payload contains date strings
from flask_jwt_extended import get_jwt_identity # Assuming tenant_id can be obtained from JWT identity
from sqlalchemy import or_ # Import or_ for search functionality
import numbers # Import numbers for numeric type checking


# Configure logging (basic example)
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


from app import db
from app.models.animal import Animal, Matriz, Reprodutor, Filhote


animal_ns = Namespace('animals', description='Animal related operations')

# Define a model for the Animal resource representation
# Added tipo_animal field for creation and tenant_id for clarity
animal_model = animal_ns.model('Animal', {
    'id': fields.Integer(readOnly=True, description='The animal unique identifier'),
    'nome': fields.String(required=True, description='The animal\'s name'),
    'microchip': fields.String(description='The animal\'s microchip ID'),
    'pedigree': fields.String(description='The animal\'s pedigree information'),
    'data_nascimento': fields.Date(required=True, description='The animal\'s date of birth', example='YYYY-MM-DD'),
    'sexo': fields.String(required=True, description='The animal\'s sex (M/F)'),
    'cor': fields.String(description='The animal\'s color'),
    'peso': fields.Float(description='The animal\'s weight'),
    'altura': fields.Float(description='The animal\'s height'),
    'status': fields.String(description='The animal\'s status (e.g., Ativo, Vendido)'),
    'origem': fields.String(description='The animal\'s origin'),
    'data_aquisicao': fields.Date(description='The animal\'s acquisition date', example='YYYY-MM-DD'),
    'valor_aquisicao': fields.Float(description='The animal\'s acquisition value'),
    'observacoes': fields.String(description='Additional observations about the animal'),
    'ativo': fields.Boolean(description='Is the animal currently active?'),
    'tenant_id': fields.Integer(readOnly=True, description='The ID of the tenant this animal belongs to'), # Include tenant_id in model
    'tipo_animal': fields.String(required=True, description='The type of animal (Animal, Matriz, Reprodutor, Filhote)') # Added for creation
    # Relationships could be represented as nested models or links
})

# Model for paginated response
pagination_meta = animal_ns.model('PaginationMetadata', {
    'total': fields.Integer,
    'pages': fields.Integer,
    'page': fields.Integer,
    'per_page': fields.Integer
})

paginated_animal_model = animal_ns.model('PaginatedAnimalList', {
    'items': fields.List(fields.Nested(animal_model)),
    '_meta': fields.Nested(pagination_meta)
})


# Helper to get current tenant ID (replace with actual logic based on your setup)
# This assumes get_jwt_identity returns the tenant ID, adjust if needed.
def get_current_tenant_id():
    # In a real application, the tenant ID would be stored in the request context
    # or derived from the authenticated user's information after the tenant middleware runs.
    # For now, we'll use a placeholder or get it from JWT if applicable to your auth flow.
    # tenant_id = g.current_tenant_id # Example using Flask g context
    # tenant_id = get_jwt_identity() # If JWT identity is the tenant_id
    # You need to ensure your JWT setup correctly includes the tenant_id as identity or claim
    # For demonstration, assuming identity *is* the tenant_id
    try:
        # This requires @jwt_required() on the endpoint or a similar mechanism
        # to ensure get_jwt_identity() returns a valid identity.
        return get_jwt_identity()
    except Exception as e:
        # Handle case where JWT is not provided or invalid if endpoint is not protected
        # Or if the tenant_id is expected from another source (e.g., g)
        current_app.logger.error(f"Error getting tenant context: {e}")
        abort(401, f"Tenant context not available. Authentication required or tenant not identified.")


# Request parser for pagination and filtering
animal_list_parser = reqparse.RequestParser()
animal_list_parser.add_argument('page', type=int, default=1, help='Page number')
animal_list_parser.add_argument('per_page', type=int, default=10, help='Items per page (max 100)', location='args')
animal_list_parser.add_argument('nome', type=str, help='Filter by animal name (partial match)', location='args')
animal_list_parser.add_argument('sexo', type=str, help='Filter by animal sex (M/F)', location='args')
animal_list_parser.add_argument('status', type=str, help='Filter by animal status', location='args')
animal_list_parser.add_argument('search', type=str, help='Search term across multiple fields (nome, microchip, pedigree, cor, status, origem)', location='args')


@animal_ns.route('/')
class AnimalList(Resource):
    # @jwt_required() # Add JWT protection if required for listing animals
    @animal_ns.doc('list_animals')
    @animal_ns.expect(animal_list_parser) # Document query parameters
    @animal_ns.marshal_with(paginated_animal_model) # Marshal with paginated model
    def get(self):
        """
        Lists all animals for the current tenant with pagination, filtering, and search
        """
        try:
            current_tenant_id = get_current_tenant_id() # Get tenant_id for filtering

            args = animal_list_parser.parse_args(request)
            page = args['page']
            per_page = args['per_page']
            filter_nome = args.get('nome')
            filter_sexo = args.get('sexo')
            filter_status = args.get('status')
            search_term = args.get('search')

            if per_page > 100:
                abort(400, message='Per page limit is 100')


            query = Animal.query.filter_by(tenant_id=current_tenant_id)

            # Apply filters
            if filter_nome:
                query = query.filter(Animal.nome.ilike(f'%{filter_nome}%'))
            if filter_sexo:
                query = query.filter_by(sexo=filter_sexo)
            if filter_status:
                query = query.filter_by(status=filter_status)

            # Apply search term across multiple fields
            if search_term:
                 search_pattern = f'%{search_term}%'
                 query = query.filter(or_(
                     Animal.nome.ilike(search_pattern),
                     Animal.microchip.ilike(search_pattern),
                     Animal.pedigree.ilike(search_pattern),
                     Animal.cor.ilike(search_pattern),
                     Animal.status.ilike(search_pattern),
                     Animal.origem.ilike(search_pattern)
                 ))


            # Paginate the results
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)

            # Prepare the response with items and metadata
            response = {
                'items': pagination.items,
                '_meta': {
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'page': pagination.page,
                    'per_page': pagination.per_page
                }
            }

            return response, 200

        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error during animal listing: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred during animal listing: {e}")
            abort(500, message='An error occurred during animal listing.')


    # @jwt_required() # Add JWT protection if required for creating animals
    @animal_ns.doc('create_animal')
    @animal_ns.expect(animal_model)
    @animal_ns.marshal_with(animal_model, code=201)
    def post(self):
        """
        Creates a new animal for the current tenant
        """
        try:
            current_tenant_id = get_current_tenant_id() # Get tenant_id

            new_animal_data = animal_ns.payload
            tipo_animal = new_animal_data.pop('tipo_animal', None) # Get type and remove from data

            # --- Start Validation ---
            if not tipo_animal or tipo_animal not in ['Animal', 'Matriz', 'Reprodutor', 'Filhote']:
                 abort(400, message=f'Invalid or missing animal type. Must be one of: Animal, Matriz, Reprodutor, Filhote.')

            required_fields = ['nome', 'data_nascimento', 'sexo']
            for field in required_fields:
                 if field not in new_animal_data or not new_animal_data[field]:
                     abort(400, message=f'Missing or empty required field: {field}')

            # Validate date formats and convert if strings
            date_fields = ['data_nascimento', 'data_aquisicao']
            for field in date_fields:
                 if field in new_animal_data and isinstance(new_animal_data[field], str):
                     if new_animal_data[field]: # Check if string is not empty
                         try:
                             new_animal_data[field] = date.fromisoformat(new_animal_data[field])
                             # Ensure date_nascimento is not in the future
                             if field == 'data_nascimento' and new_animal_data[field] > date.today():
                                  abort(400, message='Date of birth cannot be in the future.')
                         except ValueError:
                             abort(400, message=f'Invalid date format for {field}. Use YYYY-MM-DD.')
                     else:
                          new_animal_data[field] = None # Set to None if empty string was provided

            # Validate sex value
            if 'sexo' in new_animal_data and new_animal_data['sexo'] not in ['M', 'F']:
                 abort(400, message='Invalid value for sexo. Must be \'M\' or \'F\'.')

            # Validate numerical fields (peso, altura, valor_aquisicao)
            numeric_fields = ['peso', 'altura', 'valor_aquisicao']
            for field in numeric_fields:
                if field in new_animal_data and new_animal_data[field] is not None:
                    if not isinstance(new_animal_data[field], numbers.Number) or new_animal_data[field] < 0:
                         abort(400, message=f'{field} must be a non-negative number.')

            # Add specific validations for Filhote fields if present
            if tipo_animal == 'Filhote':
                 if 'preco_venda' in new_animal_data and new_animal_data['preco_venda'] is not None:
                      if not isinstance(new_animal_data['preco_venda'], numbers.Number) or new_animal_data['preco_venda'] < 0:
                           abort(400, message='preco_venda must be a non-negative number.')


            # --- End Validation ---


            # Instantiate the correct class based on tipo_animal
            if tipo_animal == 'Matriz':
                # Filter payload to include only fields relevant to Matriz and Animal
                matriz_fields = ['proximo_cio', 'status_reprodutivo',
                                 'qtd_cruzamentos', 'qtd_filhotes', 'aposentada', 'data_aposentadoria']
                # Combine animal fields and matriz specific fields
                # This approach assumes that the model's __init__ can handle extra kwargs gracefully
                # A more robust approach would be to explicitly filter data for each subclass
                allowed_fields = [c.name for c in Animal.__table__.columns if c.name not in ['id', 'tenant_id']] + matriz_fields
                filtered_data = {k: v for k, v in new_animal_data.items() if k in allowed_fields}
                new_animal = Matriz(tenant_id=current_tenant_id, **filtered_data)
            elif tipo_animal == 'Reprodutor':
                # Filter payload to include only fields relevant to Reprodutor and Animal
                reprodutor_fields = ['qtd_cruzamentos', 'qtd_filhotes', 'qualidade_esperma',
                                     'ultima_coleta', 'ativo_reprodutivo', 'taxa_fertilidade']
                allowed_fields = [c.name for c in Animal.__table__.columns if c.name not in ['id', 'tenant_id']] + reprodutor_fields
                filtered_data = {k: v for k, v in new_animal_data.items() if k in allowed_fields}
                new_animal = Reprodutor(tenant_id=current_tenant_id, **filtered_data)
            elif tipo_animal == 'Filhote':
                 # Filter payload to include only fields relevant to Filhote and Animal
                 filhote_fields = ['ordem_nascimento', 'peso_nascimento', 'status_venda',
                                   'preco_venda', 'data_venda', 'reservado']
                 allowed_fields = [c.name for c in Animal.__table__.columns if c.name not in ['id', 'tenant_id']] + filhote_fields
                 filtered_data = {k: v for k, v in new_animal_data.items() if k in allowed_fields}
                 new_animal = Filhote(tenant_id=current_tenant_id, **filtered_data)
            elif tipo_animal == 'Animal':
                 # Filter payload to include only fields relevant to Animal
                 animal_fields = [c.name for c in Animal.__table__.columns if c.name not in ['id', 'tenant_id']]
                 filtered_data = {k: v for k, v in new_animal_data.items() if k in animal_fields}
                 new_animal = Animal(tenant_id=current_tenant_id, **filtered_data)


            db.session.add(new_animal)
            db.session.commit()

            return new_animal, 201

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error during animal creation: {e}")
            # Check for specific integrity errors if needed (e.g., duplicate microchip)
            # A more user-friendly message could be crafted based on the error details if possible
            abort(409, message='Resource already exists or violates unique constraint.')
        except DataError as e:
            db.session.rollback()
            current_app.logger.error(f"Data error during animal creation: {e}")
            # This might catch issues like string too long for a column
            abort(400, message='Invalid data format or value provided.')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during animal creation: {e}")
            abort(500, message='Database error occurred.')
        except ValueError as e:
            db.session.rollback() # Rollback in case of error after session add
            current_app.logger.error(f"Value error during animal creation: {e}")
            abort(400, message=f"Invalid value provided: {e}")
        except Exception as e:
            db.session.rollback() # Rollback in case of other errors after session add
            current_app.logger.error(f"An unexpected error occurred during animal creation: {e}")
            abort(500, message='An error occurred during animal creation.')


@animal_ns.route('/<int:id>')
@animal_ns.param('id', 'The animal identifier')
class AnimalResource(Resource):
    # @jwt_required() # Add JWT protection
    @animal_ns.doc('get_animal')
    @animal_ns.marshal_with(animal_model)
    def get(self, id):
        """
        Gets an animal by its ID for the current tenant
        """
        try:
            current_tenant_id = get_current_tenant_id() # Get tenant_id

            # Explicitly filter by tenant_id in the query
            animal = Animal.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                description=f"Animal with ID {id} not found for this tenant"
            )

            return animal, 200
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error during fetching animal {id}: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred fetching animal {id}: {e}")
            abort(500, message='An error occurred while fetching the animal.')


    # @jwt_required() # Add JWT protection
    @animal_ns.doc('update_animal')
    @animal_ns.expect(animal_model, validate=False) # validate=False allows partial updates
    @animal_ns.marshal_with(animal_model)
    def put(self, id):
        """
        Updates an animal by its ID for the current tenant
        """
        try:
            current_tenant_id = get_current_tenant_id() # Get tenant_id

            # Explicitly filter by tenant_id to get the animal
            animal = Animal.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"Animal with ID {id} not found for this tenant"
            )

            update_data = animal_ns.payload

            # --- Start Validation for PUT ---
            # Prevent updating immutable fields
            if 'id' in update_data and update_data['id'] != id:
                abort(400, message='Cannot change animal ID.')
            if 'tenant_id' in update_data and update_data['tenant_id'] != current_tenant_id:
                 abort(400, message='Cannot change tenant ID.')
            if 'tipo_animal' in update_data and update_data['tipo_animal'] != animal.tipo_animal: # Assuming tipo_animal is immutable after creation
                 abort(400, message='Cannot change animal type after creation.')

            # List of fields allowed for update (exclude immutable fields)
            allowed_update_fields = [
                'nome', 'microchip', 'pedigree', 'data_nascimento', 'sexo',
                'cor', 'peso', 'altura', 'status', 'origem',
                'data_aquisicao', 'valor_aquisicao', 'observacoes', 'ativo'
            ]

            # Add fields specific to subclasses if present in payload and animal is of that type
            if isinstance(animal, Matriz):
                 allowed_update_fields.extend(['proximo_cio', 'status_reprodutivo', 'qtd_cruzamentos',
                                      'qtd_filhotes', 'aposentada', 'data_aposentadoria'])
            elif isinstance(animal, Reprodutor):
                 allowed_update_fields.extend(['qtd_cruzamentos', 'qtd_filhotes', 'qualidade_esperma',
                                       'ultima_coleta', 'ativo_reprodutivo', 'taxa_fertilidade'])
            elif isinstance(animal, Filhote):
                 allowed_update_fields.extend(['ordem_nascimento', 'peso_nascimento', 'status_venda',
                                      'preco_venda', 'data_venda', 'reservado'])

            # Apply validations only to fields present in the update data and allowed for update
            for field, value in update_data.items():
                 if field in allowed_update_fields:
                     # Validate date formats and convert if strings
                     if field in ['data_nascimento', 'data_aquisicao', 'proximo_cio', 'data_aposentadoria', 'ultima_coleta', 'data_venda'] and isinstance(value, str):
                          if value: # Check if string is not empty
                              try:
                                  update_data[field] = date.fromisoformat(value)
                                  # Ensure data_nascimento is not in the future for updates too
                                  if field == 'data_nascimento' and update_data[field] > date.today():
                                      abort(400, message='Date of birth cannot be in the future.')
                              except ValueError:
                                  abort(400, message=f'Invalid date format for {field}. Use YYYY-MM-DD.')
                          else:
                               update_data[field] = None # Set to None if empty string

                     # Validate sex value if present
                     elif field == 'sexo' and value not in ['M', 'F']:
                          abort(400, message='Invalid value for sexo. Must be \'M\' or \'F\'.')

                     # Validate numerical fields
                     elif field in ['peso', 'altura', 'valor_aquisicao', 'preco_venda'] and value is not None:
                         if not isinstance(value, numbers.Number) or value < 0:
                            abort(400, message=f'{field} must be a non-negative number.')

                     # Add more specific validations for other fields as needed
                     # For example, string length checks if they are not handled by the model definition or require specific API-level checks

            # --- End Validation for PUT ---


            # Update animal object with validated data
            for field, value in update_data.items():
                # Only update allowed fields
                if field in allowed_update_fields:
                   setattr(animal, field, value)


            db.session.commit()
            return animal, 200

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during animal update {id}: {e}")
            abort(500, message='Database error occurred.')
        except ValueError as e:
            db.session.rollback() # Rollback in case of error after session add
            current_app.logger.error(f"Value error during animal update {id}: {e}")
            abort(400, message=f"Invalid value provided: {e}")
        except Exception as e:
             db.session.rollback() # Rollback in case of other errors after session update
             current_app.logger.error(f"An unexpected error occurred during animal update {id}: {e}")
             abort(500, message='An error occurred during animal update.')


    # @jwt_required() # Add JWT protection
    @animal_ns.doc('delete_animal')
    @animal_ns.response(204, 'Animal successfully deleted')
    @animal_ns.response(404, 'Animal not found for this tenant')
    def delete(self, id):
        """
        Deletes an animal by its ID for the current tenant
        """
        try:
            current_tenant_id = get_current_tenant_id() # Get tenant_id

            # Explicitly filter by tenant_id to get the animal
            animal = Animal.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"Animal with ID {id} not found for this tenant"
            )

            db.session.delete(animal)
            db.session.commit()

            return '', 204 # 204 No Content on successful deletion

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during animal deletion {id}: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            db.session.rollback() # Rollback in case of other errors after session delete
            current_app.logger.error(f"An unexpected error occurred during animal deletion {id}: {e}")
            abort(500, message='An error occurred during animal deletion.')