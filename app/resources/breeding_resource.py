from flask import request, current_app
from flask_restx import Namespace, Resource, fields, reqparse, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError
from datetime import date, datetime # Import datetime for potential date comparisons
from flask_jwt_extended import get_jwt_identity # Assuming tenant_id can be obtained from JWT identity

# Configure logging (basic example)
# import logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


from app import db
from app.models.breeding import Ninhada, Cruzamento, ArvoreGenealogica
from app.models.animal import Animal, Matriz # Assuming Matriz is needed for validation


breeding_ns = Namespace('breeding', description='Breeding related operations (Litters, Crossings, Genealogy Trees)')

# Define models for API representation
ninhada_model = breeding_ns.model('Ninhada', {
    'id': fields.Integer(readOnly=True),
    'numero': fields.Integer(description='Litter number'),
    'data_cruzamento': fields.Date(description='Date of crossing (YYYY-MM-DD)'),
    'data_previsao_parto': fields.Date(description='Predicted date of birth (YYYY-MM-DD)'),
    'data_parto': fields.Date(description='Actual date of birth (YYYY-MM-DD)'),
    'qtd_filhotes': fields.Integer(description='Total number of puppies'),
    'qtd_vivos': fields.Integer(description='Number of live puppies'),
    'qtd_mortos': fields.Integer(description='Number of dead puppies'),
    'observacoes': fields.String(description='Additional observations'),
    'cruzamento_id': fields.Integer(required=True, description='ID of the associated crossing'), # Make required in API
    'matriz_id': fields.Integer(required=True, description='ID of the mother (Matriz)'), # Make required in API
    # Relationships to Filhotes can be handled by a separate endpoint or nested model if needed
})

cruzamento_model = breeding_ns.model('Cruzamento', {
    'id': fields.Integer(readOnly=True),
    'data_acasalamento': fields.Date(required=True, description='Date of mating (YYYY-MM-DD)'), # Make required in API
    'tipo': fields.String(description='Type of crossing'),
    'confirmado': fields.Boolean(description='Is the crossing confirmed?'),
    'coeficiente_consanguinidade': fields.Float(readOnly=True, description='Calculated inbreeding coefficient'), # Should be calculated, not set directly
    'observacoes': fields.String(description='Additional observations'),
    'data_confirmacao': fields.Date(description='Date of confirmation (YYYY-MM-DD)'),
    # Relationships to Matriz and Reprodutor (Animals) can be handled by nested models or IDs
    'animais_ids': fields.List(fields.Integer, required=True, min_items=2, description='IDs of the animals involved (at least two)'), # Make required and add min_items
})

arvore_genealogica_model = breeding_ns.model('ArvoreGenealogica', {
    'id': fields.Integer(readOnly=True),
    'animal_id': fields.Integer(required=True, description='ID of the animal the tree belongs to'), # Make required
    'geracao': fields.Integer(description='Generation depth of the tree'),
    'tipo': fields.String(description='Type of tree (e.g., complete, limited)'),
    'genealogia_data': fields.String(description='Serialized genealogy data (e.g., JSON string)'), # Or fields.Raw if using JSON
})


# Helper to get current tenant ID (Assuming this function is reliable after middleware)
def get_current_tenant_id():
    try:
        # This requires @jwt_required() or similar on the endpoint or a mechanism
        # to ensure get_jwt_identity() returns a valid identity/tenant_id.
        # In a real application, you might get this from Flask's `g` context after middleware.
        tenant_id = get_jwt_identity() # Example: assuming JWT identity is the tenant_id
        if tenant_id is None:
             abort(401, "Tenant context not available. Authentication required or tenant not identified.")
        return tenant_id
    except Exception as e:
        current_app.logger.error(f"Error getting tenant context: {e}")
        abort(401, "Tenant context not available. Authentication required or tenant not identified.")


# --- Ninhada Resources ---

@breeding_ns.route('/ninhadas')
class NinhadaList(Resource):
    # @jwt_required() # Add JWT protection
    @breeding_ns.doc('list_ninhadas')
    @breeding_ns.marshal_list_with(ninhada_model)
    def get(self):
        """List all litters for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            # Filter by tenant_id
            ninhadas = Ninhada.query.filter_by(tenant_id=current_tenant_id).all()
            return ninhadas

        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error during ninhada listing: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred during ninhada listing: {e}")
            abort(500, message='An error occurred during ninhada listing.')


    # @jwt_required() # Add JWT protection
    @breeding_ns.doc('create_ninhada')
    @breeding_ns.expect(ninhada_model)
    @breeding_ns.marshal_with(ninhada_model, code=201)
    def post(self):
        """Create a new litter for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            data = breeding_ns.payload

            # --- Start Validation ---
            required_fields = ['data_parto', 'qtd_filhotes', 'cruzamento_id', 'matriz_id']
            for field in required_fields:
                 if field not in data or data[field] is None: # Check for None explicitly
                     abort(400, message=f'Missing or empty required field: {field}')

            # Validate date formats and values
            date_fields = ['data_cruzamento', 'data_previsao_parto', 'data_parto']
            for field in date_fields:
                 if field in data and data[field] is not None:
                     if isinstance(data[field], str):
                         try:
                             data[field] = date.fromisoformat(data[field])
                         except ValueError:
                             abort(400, message=f'Invalid date format for {field}. Use YYYY-MM-DD.')
                     # After conversion (or if already date), validate date logic
                     if field == 'data_parto' and data[field] > date.today():
                          abort(400, message=f'data_parto cannot be in the future.')
                     # Add validation: data_parto >= data_cruzamento if both exist
                     if field == 'data_parto' and 'data_cruzamento' in data and data['data_cruzamento'] is not None and data[field] < data['data_cruzamento']:
                          abort(400, message=f'data_parto cannot be before data_cruzamento.')


            # Validate integer quantities and their sum
            int_quantity_fields = ['qtd_filhotes', 'qtd_vivos', 'qtd_mortos']
            for field in int_quantity_fields:
                 if field in data and data[field] is not None:
                     if not isinstance(data[field], int) or data[field] < 0:
                          abort(400, message=f'{field} must be a non-negative integer.')

            if data.get('qtd_vivos') is not None and data.get('qtd_mortos') is not None:
                 if data['qtd_vivos'] + data['qtd_mortos'] != data.get('qtd_filhotes'):
                      abort(400, message='Sum of qtd_vivos and qtd_mortos must equal qtd_filhotes.')


            # Validate existence and tenant ownership of related entities
            cruzamento_id = data['cruzamento_id']
            matriz_id = data['matriz_id']

            cruzamento = Cruzamento.query.filter_by(id=cruzamento_id, tenant_id=current_tenant_id).first()
            if not cruzamento:
                 abort(404, message=f'Cruzamento with ID {cruzamento_id} not found for this tenant.')

            matriz = Matriz.query.filter_by(id=matriz_id, tenant_id=current_tenant_id).first()
            if not matriz:
                 abort(404, message=f'Matriz with ID {matriz_id} not found for this tenant.')

            # Add relationship objects to data for instantiation if needed, or handle separately
            # data['cruzamento'] = cruzamento
            # data['matriz'] = matriz
            # --- End Validation ---

            # Ensure tenant_id is set on the new object
            data['tenant_id'] = current_tenant_id

            # Remove IDs from data to prevent potential issues if model doesn't expect them as kwargs
            # data.pop('cruzamento_id')
            # data.pop('matriz_id')


            new_ninhada = Ninhada(**data) # Assuming Ninhada model can accept cruzamento_id and matriz_id directly or has relationships configured


            db.session.add(new_ninhada)
            db.session.commit()

            return new_ninhada, 201

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error during ninhada creation: {e}")
            abort(409, message='Resource already exists or violates unique constraint.')
        except DataError as e:
            db.session.rollback()
            current_app.logger.error(f"Data error during ninhada creation: {e}")
            abort(400, message=f'Invalid data format or value: {e}')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during ninhada creation: {e}")
            abort(500, message='Database error occurred.')
        except ValueError as e:
             db.session.rollback()
             current_app.logger.error(f"Value error during ninhada creation: {e}")
             abort(400, message=f"Invalid value provided: {e}")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during ninhada creation: {e}")
            abort(500, message='An error occurred during ninhada creation.')


@breeding_ns.route('/ninhadas/<int:id>')
@breeding_ns.param('id', 'The litter identifier')
class NinhadaResource(Resource):
    # @jwt_required() # Add JWT protection
    @breeding_ns.doc('get_ninhada')
    @breeding_ns.marshal_with(ninhada_model)
    def get(self, id):
        """Get a litter by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            # Filter by tenant_id
            ninhada = Ninhada.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"Ninhada with ID {id} not found for this tenant"
            )
            return ninhada

        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error during fetching ninhada {id}: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred fetching ninhada {id}: {e}")
            abort(500, message='An error occurred while fetching the ninhada.')


    # @jwt_required() # Add JWT protection
    @breeding_ns.doc('update_ninhada')
    @breeding_ns.expect(ninhada_model, validate=False) # validate=False allows partial updates, validation below
    @breeding_ns.marshal_with(ninhada_model)
    def put(self, id):
        """Update a litter by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            # Filter by tenant_id
            ninhada = Ninhada.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"Ninhada with ID {id} not found for this tenant"
            )

            update_data = breeding_ns.payload

            # Prevent updating immutable fields if necessary
            if 'cruzamento_id' in update_data:
                abort(400, message='cruzamento_id cannot be updated.')
            if 'matriz_id' in update_data:
                 abort(400, message='matriz_id cannot be updated.')
            if 'tenant_id' in update_data: # Should not be able to change tenant_id
                 abort(400, message='tenant_id cannot be updated.')


            # Apply similar validations as POST for fields present in update_data
            date_fields = ['data_cruzamento', 'data_previsao_parto', 'data_parto']
            for field in date_fields:
                 if field in update_data and update_data[field] is not None:
                     if isinstance(update_data[field], str):
                         try:
                             update_data[field] = date.fromisoformat(update_data[field])
                         except ValueError:
                             abort(400, message=f'Invalid date format for {field}. Use YYYY-MM-DD.')
                     # After conversion (or if already date), validate date logic
                     if field == 'data_parto' and update_data[field] > date.today():
                          abort(400, message=f'data_parto cannot be in the future.')
                     # Add validation: data_parto >= data_cruzamento if both exist
                     if field == 'data_parto' and update_data.get('data_cruzamento') is not None and update_data[field] < update_data['data_cruzamento']:
                          abort(400, message=f'data_parto cannot be before data_cruzamento.')
                     # Also check against existing ninhada data if fields not in update_data
                     if field == 'data_parto' and 'data_cruzamento' not in update_data and ninhada.data_cruzamento is not None and update_data[field] < ninhada.data_cruzamento:
                          abort(400, message=f'data_parto cannot be before the existing data_cruzamento.')


            # Validate integer quantities and their sum
            int_quantity_fields = ['qtd_filhotes', 'qtd_vivos', 'qtd_mortos']
            for field in int_quantity_fields:
                 if field in update_data and update_data[field] is not None:
                     if not isinstance(update_data[field], int) or update_data[field] < 0:
                          abort(400, message=f'{field} must be a non-negative integer.')

            # Check sum of quantities if any are updated
            current_qtd_filhotes = update_data.get('qtd_filhotes', ninhada.qtd_filhotes)
            current_qtd_vivos = update_data.get('qtd_vivos', ninhada.qtd_vivos)
            current_qtd_mortos = update_data.get('qtd_mortos', ninhada.qtd_mortos)

            if current_qtd_vivos is not None and current_qtd_mortos is not None and current_qtd_filhotes is not None:
                 if current_qtd_vivos + current_qtd_mortos != current_qtd_filhotes:
                      abort(400, message='Sum of qtd_vivos and qtd_mortos must equal qtd_filhotes.')

            # --- End Validation ---


            # Update object attributes
            for key, value in update_data.items():
                # Check if attribute exists before setting
                if hasattr(ninhada, key):
                     setattr(ninhada, key, value)
                else:
                     current_app.logger.warning(f"Attempted to set non-existent attribute on Ninhada: {key}")


            db.session.commit()
            return ninhada

        except DataError as e:
            db.session.rollback()
            current_app.logger.error(f"Data error during ninhada update {id}: {e}")
            abort(400, message=f'Invalid data format or value: {e}')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during ninhada update {id}: {e}")
            abort(500, message='Database error occurred.')
        except ValueError as e:
             db.session.rollback()
             current_app.logger.error(f"Value error during ninhada update {id}: {e}")
             abort(400, message=f"Invalid value provided: {e}")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during ninhada update {id}: {e}")
            abort(500, message='An error occurred during ninhada update.')


    # @jwt_required() # Add JWT protection
    @breeding_ns.doc('delete_ninhada')
    @breeding_ns.response(204, 'Litter successfully deleted')
    @breeding_ns.response(404, 'Litter not found for this tenant')
    def delete(self, id):
        """Deletes a litter by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            # Filter by tenant_id
            ninhada = Ninhada.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"Ninhada with ID {id} not found for this tenant"
            )

            db.session.delete(ninhada)
            db.session.commit()

            return '', 204 # 204 No Content on successful deletion

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during ninhada deletion {id}: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during ninhada deletion {id}: {e}")
            abort(500, message='An error occurred during ninhada deletion.')


# --- Cruzamento Resources ---

@breeding_ns.route('/cruzamentos')
class CruzamentoList(Resource):
    # @jwt_required() # Add JWT protection
    @breeding_ns.doc('list_cruzamentos')
    @breeding_ns.marshal_list_with(cruzamento_model)
    def get(self):
        """List all crossings for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            # Filter by tenant_id
            cruzamentos = Cruzamento.query.filter_by(tenant_id=current_tenant_id).all()
            return cruzamentos

        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error during cruzamento listing: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred during cruzamento listing: {e}")
            abort(500, message='An error occurred during cruzamento listing.')


    # @jwt_required() # Add JWT protection
    @breeding_ns.doc('create_cruzamento')
    @breeding_ns.expect(cruzamento_model)
    @breeding_ns.marshal_with(cruzamento_model, code=201)
    def post(self):
        """Create a new crossing for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            data = breeding_ns.payload

            # --- Start Validation ---
            required_fields = ['data_acasalamento', 'animais_ids']
            for field in required_fields:
                 if field not in data or data[field] is None:
                     abort(400, message=f'Missing or empty required field: {field}')

            # Validate data_acasalamento format and value
            if isinstance(data['data_acasalamento'], str):
                 try:
                     data['data_acasalamento'] = date.fromisoformat(data['data_acasalamento'])
                 except ValueError:
                     abort(400, message=f'Invalid date format for data_acasalamento. Use YYYY-MM-DD.')
            # Validate data_confirmacao format and value if present
            if 'data_confirmacao' in data and data['data_confirmacao'] is not None:
                if isinstance(data['data_confirmacao'], str):
                    try:
                        data['data_confirmacao'] = date.fromisoformat(data['data_confirmacao'])
                    except ValueError:
                        abort(400, message=f'Invalid date format for data_confirmacao. Use YYYY-MM-DD.')
                # Validate data_confirmacao is not before data_acasalamento
                if data.get('data_confirmacao') is not None and data.get('data_acasalamento') is not None and data['data_confirmacao'] < data['data_acasalamento']:
                    abort(400, message='data_confirmacao cannot be before data_acasalamento.')


            # Validate animais_ids
            animal_ids = data.get('animais_ids')
            if not isinstance(animal_ids, list) or len(animal_ids) < 2:
                 abort(400, message='animais_ids must be a list of at least two animal IDs.')

            # Validate existence and tenant ownership of associated animals
            associated_animals = Animal.query.filter(
                 Animal.id.in_(animal_ids),
                 Animal.tenant_id == current_tenant_id
            ).all()

            if len(associated_animals) != len(animal_ids):
                # This means one or more provided animal IDs were not found or didn't belong to the tenant
                 found_ids = [a.id for a in associated_animals]
                 not_found_ids = [id for id in animal_ids if id not in found_ids]
                 abort(404, message=f'One or more animals not found or do not belong to this tenant: IDs {not_found_ids}')

            # Optionally validate animal types (e.g., one Matriz and one Reprodutor) if required by business logic
            # Example: Check if there's at least one Matriz and one Reprodutor among associated_animals
            # has_matriz = any(isinstance(a, Matriz) for a in associated_animals)
            # has_reprodutor = any(isinstance(a, Reprodutor) for a in associated_animals)
            # if not has_matriz or not has_reprodutor:
            #      abort(400, message='A crossing must involve at least one Matriz and one Reprodutor.')

            # --- End Validation ---

            # Ensure tenant_id is set on the new object
            data['tenant_id'] = current_tenant_id

            # Remove list of IDs from data before passing to model constructor if model expects relationship objects
            # animal_ids_for_relationship = data.pop('animais_ids') # Keep the list if needed for manual association
            # new_cruzamento = Cruzamento(**data)
            # # Manually associate animals if not handled by model constructor
            # for animal in associated_animals:
            #      new_cruzamento.animais.append(animal)
            # Or if model handles list of IDs directly:
            new_cruzamento = Cruzamento(**data) # Assuming Cruzamento model handles 'animais_ids' directly or via a setter


            db.session.add(new_cruzamento)
            db.session.commit()

            # Recalculate or trigger calculation of coeficiente_consanguinidade after commit if needed
            # Example: Trigger a Celery task to calculate consanguinity in background
            # from app.tasks import calculate_consanguinity_task
            # calculate_consanguinity_task.delay(new_cruzamento.id)


            return new_cruzamento, 201

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error during cruzamento creation: {e}")
            abort(409, message='Resource already exists or violates unique constraint.')
        except DataError as e:
            db.session.rollback()
            current_app.logger.error(f"Data error during cruzamento creation: {e}")
            abort(400, message=f'Invalid data format or value: {e}')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during cruzamento creation: {e}")
            abort(500, message='Database error occurred.')
        except ValueError as e:
             db.session.rollback()
             current_app.logger.error(f"Value error during cruzamento creation: {e}")
             abort(400, message=f"Invalid value provided: {e}")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during cruzamento creation: {e}")
            abort(500, message='An error occurred during cruzamento creation.')


@breeding_ns.route('/cruzamentos/<int:id>')
@breeding_ns.param('id', 'The crossing identifier')
class CruzamentoResource(Resource):
    # @jwt_required() # Add JWT protection
    @breeding_ns.doc('get_cruzamento')
    @breeding_ns.marshal_with(cruzamento_model)
    def get(self, id):
        """Get a crossing by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            # Filter by tenant_id
            cruzamento = Cruzamento.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"Cruzamento with ID {id} not found for this tenant"
            )
            return cruzamento

        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error during fetching cruzamento {id}: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred fetching cruzamento {id}: {e}")
            abort(500, message='An error occurred while fetching the cruzamento.')


    # @jwt_required() # Add JWT protection
    @breeding_ns.doc('update_cruzamento')
    @breeding_ns.expect(cruzamento_model, validate=False) # validate=False allows partial updates, validation below
    @breeding_ns.marshal_with(cruzamento_model)
    def put(self, id):
        """Update a crossing by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            # Filter by tenant_id
            cruzamento = Cruzamento.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"Cruzamento with ID {id} not found for this tenant"
            )

            update_data = breeding_ns.payload

            # Prevent updating immutable fields if necessary
            if 'tenant_id' in update_data: # Should not be able to change tenant_id
                 abort(400, message='tenant_id cannot be updated.')
            # Decide if 'data_acasalamento' can be updated
            # if 'data_acasalamento' in update_data:
            #      abort(400, message='data_acasalamento cannot be updated after creation.')


            # Apply similar validations as POST for fields present in update_data
            if 'data_acasalamento' in update_data and update_data['data_acasalamento'] is not None:
                 if isinstance(update_data['data_acasalamento'], str):
                     try:
                         update_data['data_acasalamento'] = date.fromisoformat(update_data['data_acasalamento'])
                     except ValueError:
                         abort(400, message=f'Invalid date format for data_acasalamento. Use YYYY-MM-DD.')

            if 'data_confirmacao' in update_data and update_data['data_confirmacao'] is not None:
                if isinstance(update_data['data_confirmacao'], str):
                    try:
                        update_data['data_confirmacao'] = date.fromisoformat(update_data['data_confirmacao'])
                    except ValueError:
                        abort(400, message=f'Invalid date format for data_confirmacao. Use YYYY-MM-DD.')
                # Validate data_confirmacao is not before data_acasalamento (check against existing or updated data)
                current_data_acasalamento = update_data.get('data_acasalamento', cruzamento.data_acasalamento)
                if update_data['data_confirmacao'] is not None and current_data_acasalamento is not None and update_data['data_confirmacao'] < current_data_acasalamento:
                     abort(400, message='data_confirmacao cannot be before data_acasalamento.')


            # Validate animaux_ids if present in update_data
            if 'animais_ids' in update_data and update_data['animais_ids'] is not None:
                 animal_ids = update_data['animais_ids']
                 if not isinstance(animal_ids, list) or len(animal_ids) < 2:
                      abort(400, message='animais_ids must be a list of at least two animal IDs.')

                 # Validate existence and tenant ownership of associated animals
                 associated_animals = Animal.query.filter(
                      Animal.id.in_(animal_ids),
                      Animal.tenant_id == current_tenant_id
                 ).all()

                 if len(associated_animals) != len(animal_ids):
                      found_ids = [a.id for a in associated_animals]
                      not_found_ids = [id for id in animal_ids if id not in found_ids]
                      abort(404, message=f'One or more animals for association not found or do not belong to this tenant: IDs {not_found_ids}')

                 # Optionally validate animal types in update as well


            # --- End Validation ---

            # Update object attributes
            animal_ids_to_update = update_data.pop('animais_ids', None) # Pop animas_ids to handle separately

            for key, value in update_data.items():
                if hasattr(cruzamento, key):
                     setattr(cruzamento, key, value)
                else:
                     current_app.logger.warning(f"Attempted to set non-existent attribute on Cruzamento: {key}")


            # Handle animals_ids update (Many-to-Many)
            if animal_ids_to_update is not None:
                 # Clear existing associations and add new ones
                 cruzamento.animais = [] # This might trigger deletes in the association table
                 associated_animals = Animal.query.filter(Animal.id.in_(animal_ids_to_update)).all() # Re-query based on validated IDs
                 for animal in associated_animals:
                      cruzamento.animais.append(animal) # Add new associations


            db.session.commit()

            # Recalculate or trigger calculation of coeficiente_consanguinidade after commit if needed
            # if animal_ids_to_update is not None: # Only if animals involved in crossing changed
            #     from app.tasks import calculate_consanguinity_task
            #     calculate_consanguinity_task.delay(cruzamento.id)


            return cruzamento

        except DataError as e:
            db.session.rollback()
            current_app.logger.error(f"Data error during cruzamento update {id}: {e}")
            abort(400, message=f'Invalid data format or value: {e}')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during cruzamento update {id}: {e}")
            abort(500, message='Database error occurred.')
        except ValueError as e:
             db.session.rollback()
             current_app.logger.error(f"Value error during cruzamento update {id}: {e}")
             abort(400, message=f"Invalid value provided: {e}")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during cruzamento update {id}: {e}")
            abort(500, message='An error occurred during cruzamento update.')


    # @jwt_required() # Add JWT protection
    @breeding_ns.doc('delete_cruzamento')
    @breeding_ns.response(204, 'Crossing successfully deleted')
    @breeding_ns.response(404, 'Crossing not found for this tenant')
    def delete(self, id):
        """Deletes a crossing by its ID for the current tenant"""
        try:
            current_tenant_id = get_current_tenant_id()
            # Filter by tenant_id
            cruzamento = Cruzamento.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                 description=f"Cruzamento with ID {id} not found for this tenant