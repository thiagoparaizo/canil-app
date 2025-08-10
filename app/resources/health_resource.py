from flask import request, current_app
from flask_restx import Namespace, Resource, fields, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError
from datetime import date  # Needed for date conversion and date comparisons
from flask_jwt_extended import get_jwt_identity # Assuming tenant_id can be obtained from JWT identity

# Assume Animal model is imported from app.models.animal
from app.models.animal import Animal
from app import db
from app.models.health import RegistroVeterinario, Vacinacao, Vermifugacao, ExameGenetico # Assuming these models are defined

health_ns = Namespace('health', description='Health related operations (Veterinary Records, Vaccinations, Deworming, Genetic Exams)')

# Define models for API representation
registro_veterinario_model = health_ns.model('RegistroVeterinario', {
    'id': fields.Integer(readOnly=True),
    'animal_id': fields.Integer(required=True, description='The animal identifier'), # Foreign key
    'data_consulta': fields.Date(required=True, description='Date of the consultation', example='YYYY-MM-DD'),
    'motivo': fields.String(required=True, description='Reason for the consultation'),
    'diagnostico': fields.String(description='Veterinary diagnosis'),
    'tratamento': fields.String(description='Prescribed treatment'),
    'peso': fields.Float(description='Animal\'s weight at the time of consultation'),
    'observacoes': fields.String(description='Additional observations'),
    'status_saude': fields.String(description='Animal\'s health status after consultation'),
    'emergencia': fields.Boolean(description='Was this an emergency consultation?'),
    # Relationships to Animal can be handled by nested models or IDs
})

vacinacao_model = health_ns.model('Vacinacao', {
    'id': fields.Integer(readOnly=True),
    'animal_id': fields.Integer(required=True, description='The animal identifier'), # Foreign key
    'tipo_vacina': fields.String(required=True, description='Type of vaccine administered'),
    'data_aplicacao': fields.Date(required=True, description='Date of vaccination', example='YYYY-MM-DD'),
    'proxima_dose': fields.Date(description='Date for the next dose', example='YYYY-MM-DD'),
    'lote': fields.String(description='Vaccine batch number'),
    'laboratorio': fields.String(description='Vaccine manufacturer'),
    'reacao': fields.Boolean(description='Did the animal have a reaction?'),
    'observacoes': fields.String(description='Additional observations'),
    # Relationships to Animal can be handled by nested models or IDs
})

vermifugacao_model = health_ns.model('Vermifugacao', {
    'id': fields.Integer(readOnly=True),
    'animal_id': fields.Integer(required=True, description='The animal identifier'), # Foreign key
    'medicamento': fields.String(required=True, description='Deworming medication name'),
    'data_aplicacao': fields.Date(required=True, description='Date of deworming', example='YYYY-MM-DD'),
    'dosagem': fields.Float(description='Dosage administered'),
    'proxima_aplicacao': fields.Date(description='Date for the next deworming', example='YYYY-MM-DD'),
    'observacoes': fields.String(description='Additional observations'),
    # Relationships to Animal can be handled by nested models or IDs
})

exame_genetico_model = health_ns.model('ExameGenetico', {
    'id': fields.Integer(readOnly=True),
    'animal_id': fields.Integer(required=True, description='The animal identifier'), # Foreign key
    'tipo_exame': fields.String(required=True, description='Type of genetic exam'),
    'data_coleta': fields.Date(description='Date sample was collected', example='YYYY-MM-DD'),
    'data_resultado': fields.Date(description='Date results were received', example='YYYY-MM-DD'),
    'resultado': fields.String(description='Exam results'),
    'laboratorio': fields.String(description='Laboratory that performed the exam'),
    'observacoes': fields.String(description='Additional observations'),
    'aprovado': fields.Boolean(description='Was the result considered favorable?'),
    # Relationships to Animal can be handled by nested models or IDs
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
        # If your JWT identity is not the tenant_id, you'll need to fetch
        # the user based on identity and then get their tenant_id.
        return get_jwt_identity()
    except Exception as e:
        current_app.logger.error(f"Error getting tenant context: {e}")
        # Use Flask-RESTx abort for consistent error responses
        abort(401, f"Tenant context not available. Authentication required or tenant not identified.")


# --- RegistroVeterinario Resources ---

@health_ns.route('/registros_veterinarios')
class RegistroVeterinarioList(Resource):
    # @jwt_required() # Add JWT protection
    @health_ns.doc('list_registros_veterinarios')
    @health_ns.marshal_list_with(registro_veterinario_model)
    def get(self):
        """List all veterinary records for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            registros = RegistroVeterinario.query.filter_by(tenant_id=current_tenant_id).all()
            return registros
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error during veterinary record listing: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred during veterinary record listing: {e}")
            abort(500, message='An error occurred during listing veterinary records.')


    # @jwt_required() # Add JWT protection
    @health_ns.doc('create_registro_veterinario')
    @health_ns.expect(registro_veterinario_model)
    @health_ns.marshal_with(registro_veterinario_model, code=201)
    def post(self):
        """Create a new veterinary record for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            data = health_ns.payload

            # --- Start Validation ---
            required_fields = ['animal_id', 'data_consulta', 'motivo']
            for field in required_fields:
                 if field not in data or not data[field]:
                     abort(400, message=f'Missing or empty required field: {field}')

            # Validate animal_id and tenant ownership
            animal_id = data['animal_id']
            animal = Animal.query.filter_by(id=animal_id, tenant_id=current_tenant_id).first()
            if not animal:
                 abort(404, message=f'Animal with ID {animal_id} not found or does not belong to this tenant.')

            # Validate date_consulta format and if it's not in the future
            data_consulta_str = data['data_consulta']
            if isinstance(data_consulta_str, str):
                 try:
                     data_consulta = date.fromisoformat(data_consulta_str)
                     data['data_consulta'] = data_consulta # Convert to date object
                 except ValueError:
                     abort(400, message=f'Invalid date format for data_consulta. Use YYYY-MM-DD.')
            else:
                data_consulta = data['data_consulta'] # Assume it's already a date object if not a string

            if data_consulta > date.today():
                 abort(400, message=f'data_consulta cannot be in the future.')

            # Validate peso if provided
            if 'peso' in data and data['peso'] is not None:
                 if not isinstance(data['peso'], (int, float)) or data['peso'] < 0:
                     abort(400, message='Peso must be a non-negative number.')
            # --- End Validation ---


            # Add tenant_id before creating the model instance
            data['tenant_id'] = current_tenant_id

            new_registro = RegistroVeterinario(**data)
            db.session.add(new_registro)
            db.session.commit()

            return new_registro, 201

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error during veterinary record creation: {e}")
            abort(409, message='Resource already exists or violates unique constraint.')
        except DataError as e:
            db.session.rollback()
            current_app.logger.error(f"Data error during veterinary record creation: {e}")
            abort(400, message='Invalid data format or value.')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during veterinary record creation: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during veterinary record creation: {e}")
            abort(500, message='An error occurred during creating veterinary record.')


@health_ns.route('/registros_veterinarios/<int:id>')
@health_ns.param('id', 'The veterinary record identifier')
class RegistroVeterinarioResource(Resource):
    # @jwt_required() # Add JWT protection
    @health_ns.doc('get_registro_veterinario')
    @health_ns.marshal_with(registro_veterinario_model)
    def get(self, id):
        """Get a veterinary record by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            registro = RegistroVeterinario.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"Veterinary record with ID {id} not found for this tenant"
            )
            return registro
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error fetching veterinary record {id}: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred fetching veterinary record {id}: {e}")
            abort(500, message='An error occurred while fetching the veterinary record.')


    # @jwt_required() # Add JWT protection
    @health_ns.doc('update_registro_veterinario')
    @health_ns.expect(registro_veterinario_model, validate=False) # validate=False allows partial updates
    @health_ns.marshal_with(registro_veterinario_model)
    def put(self, id):
        """Update a veterinary record by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            registro = RegistroVeterinario.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"Veterinary record with ID {id} not found for this tenant"
            )

            update_data = health_ns.payload

            # Prevent updating animal_id or tenant_id
            if 'animal_id' in update_data:
                abort(400, message='animal_id cannot be changed after creation.')
            if 'tenant_id' in update_data:
                 abort(400, message='tenant_id cannot be changed.')


            # --- Start Validation for Update ---
            # Validate date_consulta format and if it's not in the future if present
            if 'data_consulta' in update_data and update_data['data_consulta'] is not None:
                 data_consulta_str = update_data['data_consulta']
                 if isinstance(data_consulta_str, str):
                     try:
                         data_consulta = date.fromisoformat(data_consulta_str)
                         update_data['data_consulta'] = data_consulta # Convert to date object
                     except ValueError:
                         abort(400, message=f'Invalid date format for data_consulta. Use YYYY-MM-DD.')
                 else:
                     data_consulta = update_data['data_consulta'] # Assume it's already a date object

                 if data_consulta > date.today():
                      abort(400, message=f'data_consulta cannot be in the future.')

            # Validate peso if provided
            if 'peso' in update_data and update_data['peso'] is not None:
                 if not isinstance(update_data['peso'], (int, float)) or update_data['peso'] < 0:
                     abort(400, message='Peso must be a non-negative number.')
            # --- End Validation for Update ---


            # Update fields from the payload, excluding protected fields
            update_fields = ['data_consulta', 'motivo', 'diagnostico', 'tratamento',
                             'peso', 'observacoes', 'status_saude', 'emergencia']

            for field in update_fields:
                if field in update_data:
                     setattr(registro, field, update_data[field])


            db.session.commit()
            return registro

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during veterinary record update {id}: {e}")
            abort(500, message='Database error occurred.')
        except DataError as e:
            db.session.rollback()
            current_app.logger.error(f"Data error during veterinary record update {id}: {e}")
            abort(400, message='Invalid data format or value.')
        except Exception as e:
             db.session.rollback()
             current_app.logger.error(f"An unexpected error occurred during veterinary record update {id}: {e}")
             abort(500, message='An error occurred during updating veterinary record.')


    # @jwt_required() # Add JWT protection
    @health_ns.doc('delete_registro_veterinario')
    @health_ns.response(204, 'Veterinary record successfully deleted')
    @health_ns.response(404, 'Veterinary record not found for this tenant')
    def delete(self, id):
        """Deletes a veterinary record by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            registro = RegistroVeterinario.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"Veterinary record with ID {id} not found for this tenant"
            )
            db.session.delete(registro)
            db.session.commit()
            return '', 204 # 204 No Content on successful deletion
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during veterinary record deletion {id}: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during veterinary record deletion {id}: {e}")
            abort(500, message='An error occurred during deleting veterinary record.')

# --- Vacinacao Resources ---

@health_ns.route('/vacinacoes')
class VacinacaoList(Resource):
    # @jwt_required() # Add JWT protection
    @health_ns.doc('list_vacinacoes')
    @health_ns.marshal_list_with(vacinacao_model)
    def get(self):
        """List all vaccinations for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            vacinacoes = Vacinacao.query.filter_by(tenant_id=current_tenant_id).all()
            return vacinacoes
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error during vaccination listing: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred during vaccination listing: {e}")
            abort(500, message='An error occurred during listing vaccinations.')


    # @jwt_required() # Add JWT protection
    @health_ns.doc('create_vacinacao')
    @health_ns.expect(vacinacao_model)
    @health_ns.marshal_with(vacinacao_model, code=201)
    def post(self):
        """Create a new vaccination record for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            data = health_ns.payload

            # --- Start Validation ---
            required_fields = ['animal_id', 'tipo_vacina', 'data_aplicacao']
            for field in required_fields:
                 if field not in data or not data[field]:
                     abort(400, message=f'Missing or empty required field: {field}')

            # Validate animal_id and tenant ownership
            animal_id = data['animal_id']
            animal = Animal.query.filter_by(id=animal_id, tenant_id=current_tenant_id).first()
            if not animal:
                 abort(404, message=f'Animal with ID {animal_id} not found or does not belong to this tenant.')

            # Validate date_aplicacao format and if it's not in the future
            data_aplicacao_str = data['data_aplicacao']
            if isinstance(data_aplicacao_str, str):
                 try:
                     data_aplicacao = date.fromisoformat(data_aplicacao_str)
                     data['data_aplicacao'] = data_aplicacao # Convert to date object
                 except ValueError:
                     abort(400, message=f'Invalid date format for data_aplicacao. Use YYYY-MM-DD.')
            else:
                data_aplicacao = data['data_aplicacao'] # Assume it's already a date object

            if data_aplicacao > date.today():
                 abort(400, message=f'data_aplicacao cannot be in the future.')

            # Validate proxima_dose format and if it's after data_aplicacao if provided
            if 'proxima_dose' in data and data['proxima_dose'] is not None:
                 proxima_dose_str = data['proxima_dose']
                 if isinstance(proxima_dose_str, str):
                     try:
                         proxima_dose = date.fromisoformat(proxima_dose_str)
                         data['proxima_dose'] = proxima_dose # Convert to date object
                     except ValueError:
                         abort(400, message=f'Invalid date format for proxima_dose. Use YYYY-MM-DD.')
                 else:
                      proxima_dose = data['proxima_dose'] # Assume it's already a date object

                 if proxima_dose < data_aplicacao:
                      abort(400, message=f'proxima_dose cannot be before data_aplicacao.')

            # --- End Validation ---

            # Add tenant_id before creating the model instance
            data['tenant_id'] = current_tenant_id

            new_vacinacao = Vacinacao(**data)
            db.session.add(new_vacinacao)
            db.session.commit()

            return new_vacinacao, 201

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error during vaccination creation: {e}")
            abort(409, message='Resource already exists or violates unique constraint.')
        except DataError as e:
            db.session.rollback()
            current_app.logger.error(f"Data error during vaccination creation: {e}")
            abort(400, message='Invalid data format or value.')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during vaccination creation: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during vaccination creation: {e}")
            abort(500, message='An error occurred during creating vaccination record.')


@health_ns.route('/vacinacoes/<int:id>')
@health_ns.param('id', 'The vaccination identifier')
class VacinacaoResource(Resource):
    # @jwt_required() # Add JWT protection
    @health_ns.doc('get_vacinacao')
    @health_ns.marshal_with(vacinacao_model)
    def get(self, id):
        """Get a vaccination by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            vacinacao = Vacinacao.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"Vaccination with ID {id} not found for this tenant"
            )
            return vacinacao
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error fetching vaccination {id}: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred fetching vaccination {id}: {e}")
            abort(500, message='An error occurred while fetching the vaccination.')


    # @jwt_required() # Add JWT protection
    @health_ns.doc('update_vacinacao')
    @health_ns.expect(vacinacao_model, validate=False) # validate=False allows partial updates
    @health_ns.marshal_with(vacinacao_model)
    def put(self, id):
        """Update a vaccination by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            vacinacao = Vacinacao.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"Vaccination with ID {id} not found for this tenant"
            )

            update_data = health_ns.payload

            # Prevent updating animal_id or tenant_id
            if 'animal_id' in update_data:
                abort(400, message='animal_id cannot be changed after creation.')
            if 'tenant_id' in update_data:
                 abort(400, message='tenant_id cannot be changed.')

            # --- Start Validation for Update ---
            # Validate date_aplicacao format and if it's not in the future if present
            if 'data_aplicacao' in update_data and update_data['data_aplicacao'] is not None:
                 data_aplicacao_str = update_data['data_aplicacao']
                 if isinstance(data_aplicacao_str, str):
                     try:
                         data_aplicacao = date.fromisoformat(data_aplicacao_str)
                         update_data['data_aplicacao'] = data_aplicacao # Convert to date object
                     except ValueError:
                         abort(400, message=f'Invalid date format for data_aplicacao. Use YYYY-MM-DD.')
                 else:
                     data_aplicacao = update_data['data_aplicacao'] # Assume it's already a date object

                 if data_aplicacao > date.today():
                      abort(400, message=f'data_aplicacao cannot be in the future.')

            # Validate proxima_dose format and if it's after data_aplicacao if provided
            if 'proxima_dose' in update_data and update_data['proxima_dose'] is not None:
                 proxima_dose_str = update_data['proxima_dose']
                 if isinstance(proxima_dose_str, str):
                     try:
                         proxima_dose = date.fromisoformat(proxima_dose_str)
                         update_data['proxima_dose'] = proxima_dose # Convert to date object
                     except ValueError:
                         abort(400, message=f'Invalid date format for proxima_dose. Use YYYY-MM-DD.')
                 else:
                      proxima_dose = update_data['proxima_dose'] # Assume it's already a date object

                 # Need to use the potentially updated data_aplicacao for comparison
                 current_data_aplicacao = update_data.get('data_aplicacao', vacinacao.data_aplicacao)
                 if proxima_dose is not None and current_data_aplicacao is not None and proxima_dose < current_data_aplicacao:
                      abort(400, message=f'proxima_dose cannot be before data_aplicacao.')

            # --- End Validation for Update ---

            # Update fields from the payload, excluding protected fields
            update_fields = ['tipo_vacina', 'data_aplicacao', 'proxima_dose', 'lote',
                             'laboratorio', 'reacao', 'observacoes']

            for field in update_fields:
                if field in update_data:
                     setattr(vacinacao, field, update_data[field])


            db.session.commit()
            return vacinacao

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during vaccination update {id}: {e}")
            abort(500, message='Database error occurred.')
        except DataError as e:
            db.session.rollback()
            current_app.logger.error(f"Data error during vaccination update {id}: {e}")
            abort(400, message='Invalid data format or value.')
        except Exception as e:
             db.session.rollback()
             current_app.logger.error(f"An unexpected error occurred during vaccination update {id}: {e}")
             abort(500, message='An error occurred during updating vaccination record.')


    # @jwt_required() # Add JWT protection
    @health_ns.doc('delete_vacinacao')
    @health_ns.response(204, 'Vaccination successfully deleted')
    @health_ns.response(404, 'Vaccination not found for this tenant')
    def delete(self, id):
        """Deletes a vaccination by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            vacinacao = Vacinacao.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"Vaccination with ID {id} not found for this tenant"
            )
            db.session.delete(vacinacao)
            db.session.commit()
            return '', 204 # 204 No Content on successful deletion
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during vaccination deletion {id}: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during vaccination deletion {id}: {e}")
            abort(500, message='An error occurred during deleting vaccination record.')

# --- Vermifugacao Resources ---

@health_ns.route('/vermifugacoes')
class VermifugacaoList(Resource):
    # @jwt_required() # Add JWT protection
    @health_ns.doc('list_vermifugacoes')
    @health_ns.marshal_list_with(vermifugacao_model)
    def get(self):
        """List all deworming records for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            vermifugacoes = Vermifugacao.query.filter_by(tenant_id=current_tenant_id).all()
            return vermifugacoes
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error during deworming record listing: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred during deworming record listing: {e}")
            abort(500, message='An error occurred during listing deworming records.')


    # @jwt_required() # Add JWT protection
    @health_ns.doc('create_vermifugacao')
    @health_ns.expect(vermifugacao_model)
    @health_ns.marshal_with(vermifugacao_model, code=201)
    def post(self):
        """Create a new deworming record for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            data = health_ns.payload

            # --- Start Validation ---
            required_fields = ['animal_id', 'medicamento', 'data_aplicacao']
            for field in required_fields:
                 if field not in data or not data[field]:
                     abort(400, message=f'Missing or empty required field: {field}')

            # Validate animal_id and tenant ownership
            animal_id = data['animal_id']
            animal = Animal.query.filter_by(id=animal_id, tenant_id=current_tenant_id).first()
            if not animal:
                 abort(404, message=f'Animal with ID {animal_id} not found or does not belong to this tenant.')

            # Validate data_aplicacao format and if it's not in the future
            data_aplicacao_str = data['data_aplicacao']
            if isinstance(data_aplicacao_str, str):
                 try:
                     data_aplicacao = date.fromisoformat(data_aplicacao_str)
                     data['data_aplicacao'] = data_aplicacao # Convert to date object
                 except ValueError:
                     abort(400, message=f'Invalid date format for data_aplicacao. Use YYYY-MM-DD.')
            else:
                data_aplicacao = data['data_aplicacao'] # Assume it's already a date object

            if data_aplicacao > date.today():
                 abort(400, message=f'data_aplicacao cannot be in the future.')

            # Validate proxima_aplicacao format and if it's after data_aplicacao if provided
            if 'proxima_aplicacao' in data and data['proxima_aplicacao'] is not None:
                 proxima_aplicacao_str = data['proxima_aplicacao']
                 if isinstance(proxima_aplicacao_str, str):
                     try:
                         proxima_aplicacao = date.fromisoformat(proxima_aplicacao_str)
                         data['proxima_aplicacao'] = proxima_aplicacao # Convert to date object
                     except ValueError:
                         abort(400, message=f'Invalid date format for proxima_aplicacao. Use YYYY-MM-DD.')
                 else:
                      proxima_aplicacao = data['proxima_aplicacao'] # Assume it's already a date object

                 if proxima_aplicacao is not None and data_aplicacao is not None and proxima_aplicacao < data_aplicacao:
                      abort(400, message=f'proxima_aplicacao cannot be before data_aplicacao.')

            # Validate dosagem if provided
            if 'dosagem' in data and data['dosagem'] is not None:
                 if not isinstance(data['dosagem'], (int, float)) or data['dosagem'] < 0:
                     abort(400, message='Dosagem must be a non-negative number.')

            # --- End Validation ---

            # Add tenant_id before creating the model instance
            data['tenant_id'] = current_tenant_id

            new_vermifugacao = Vermifugacao(**data)
            db.session.add(new_vermifugacao)
            db.session.commit()

            return new_vermifugacao, 201

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error during deworming record creation: {e}")
            abort(409, message='Resource already exists or violates unique constraint.')
        except DataError as e:
            db.session.rollback()
            current_app.logger.error(f"Data error during deworming record creation: {e}")
            abort(400, message='Invalid data format or value.')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during deworming record creation: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during deworming record creation: {e}")
            abort(500, message='An error occurred during creating deworming record.')


@health_ns.route('/vermifugacoes/<int:id>')
@health_ns.param('id', 'The deworming identifier')
class VermifugacaoResource(Resource):
    # @jwt_required() # Add JWT protection
    @health_ns.doc('get_vermifugacao')
    @health_ns.marshal_with(vermifugacao_model)
    def get(self, id):
        """Get a deworming by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            vermifugacao = Vermifugacao.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"Deworming with ID {id} not found for this tenant"
            )
            return vermifugacao
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error fetching deworming {id}: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred fetching deworming {id}: {e}")
            abort(500, message='An error occurred while fetching the deworming.')

    @health_ns.doc('update_vermifugacao')
    @health_ns.expect(vermifugacao_model, validate=False)
    @health_ns.marshal_with(vermifugacao_model)
    def put(self, id):
        """Update a deworming by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            vermifugacao = Vermifugacao.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404()
            
            update_data = health_ns.payload
            if 'animal_id' in update_data:
                abort(400, message='animal_id cannot be changed after creation.')
            if 'tenant_id' in update_data:
                abort(400, message='tenant_id cannot be changed.')

            for key, value in update_data.items():
                if hasattr(vermifugacao, key):
                    setattr(vermifugacao, key, value)

            db.session.commit()
            return vermifugacao
        except Exception as e:
            db.session.rollback()
            abort(500, message='An error occurred during updating deworming record.')

    @health_ns.doc('delete_vermifugacao')
    @health_ns.response(204, 'Deworming successfully deleted')
    def delete(self, id):
        """Delete a deworming by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            vermifugacao = Vermifugacao.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404()
            db.session.delete(vermifugacao)
            db.session.commit()
            return '', 204
        except Exception as e:
            db.session.rollback()
            abort(500, message='An error occurred during deleting deworming record.')


# --- ExameGenetico Resources ---

@health_ns.route('/exames_geneticos')
class ExameGeneticoList(Resource):
    @health_ns.doc('list_exames_geneticos')
    @health_ns.marshal_list_with(exame_genetico_model)
    def get(self):
        """List all genetic exams for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            exames = ExameGenetico.query.filter_by(tenant_id=current_tenant_id).all()
            return exames
        except Exception as e:
            abort(500, message='Database error occurred.')

    @health_ns.doc('create_exame_genetico')
    @health_ns.expect(exame_genetico_model)
    @health_ns.marshal_with(exame_genetico_model, code=201)
    def post(self):
        """Create a new genetic exam for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            data = health_ns.payload
            data['tenant_id'] = current_tenant_id
            
            new_exame = ExameGenetico(**data)
            db.session.add(new_exame)
            db.session.commit()
            return new_exame, 201
        except Exception as e:
            db.session.rollback()
            abort(500, message='An error occurred during creating genetic exam.')


@health_ns.route('/exames_geneticos/<int:id>')
@health_ns.param('id', 'The genetic exam identifier')
class ExameGeneticoResource(Resource):
    @health_ns.doc('get_exame_genetico')
    @health_ns.marshal_with(exame_genetico_model)
    def get(self, id):
        """Get a genetic exam by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            exame = ExameGenetico.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404()
            return exame
        except Exception as e:
            abort(500, message='Database error occurred.')

    @health_ns.doc('delete_exame_genetico')
    @health_ns.response(204, 'Genetic exam deleted')
    def delete(self, id):
        """Delete a genetic exam by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            exame = ExameGenetico.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404()
            db.session.delete(exame)
            db.session.commit()
            return '', 204
        except Exception as e:
            db.session.rollback()
            abort(500, message='Database error occurred.')