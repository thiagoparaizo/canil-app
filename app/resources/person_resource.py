from flask import request
from flask_restx import Namespace, Resource, fields, reqparse, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError
from datetime import date
import re # Import regex for format validation
from flask_jwt_extended import get_jwt_identity # Assuming tenant_id can be obtained from JWT identity

from app import db
from app.models.person import Cliente, Funcionario, Veterinario
from app.models.system import Endereco # Import Endereco model for validation

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
        # current_app.logger.error(f"Error getting tenant context: {e}") # Logging would be better
        abort(401, f"Tenant context not available. Authentication required or tenant not identified.")


person_ns = Namespace('person', description='Person related operations (Clients, Employees, Veterinarians)')

# Define models for API representation
# Using nested models for relationships like Endereco could be considered later

cliente_model = person_ns.model('Cliente', {
    'id': fields.Integer(readOnly=True),
    'nome': fields.String(required=True, description='Client\'s full name'),
    'cpf': fields.String(description='Client\'s CPF (11 digits)'),
    'telefone': fields.String(description='Client\'s phone number'),
    'email': fields.String(description='Client\'s email address'),
    'data_nascimento': fields.Date(description='Client\'s date of birth (YYYY-MM-DD)'),
    'ativo': fields.Boolean(description='Is the client active?'),
    'profissao': fields.String(description='Client\'s profession'),
    'endereco_id': fields.Integer(description='ID of the associated address'), # Foreign key
    # Relationships to transactions can be handled by separate endpoints or nested models
})

funcionario_model = person_ns.model('Funcionario', {
    'id': fields.Integer(readOnly=True),
    'nome': fields.String(required=True, description='Employee\'s full name'),
    'cpf': fields.String(description='Employee\'s CPF (11 digits)'),
    'telefone': fields.String(description='Employee\'s phone number'),
    'email': fields.String(description='Employee\'s email address'),
    'data_nascimento': fields.Date(description='Employee\'s date of birth (YYYY-MM-DD)'),
    'ativo': fields.Boolean(description='Is the employee active?'),
    'cargo': fields.String(required=True, description='Employee\'s role or position'),
    'salario': fields.Float(description='Employee\'s salary'),
    'data_admissao': fields.Date(required=True, description='Employee\'s start date (YYYY-MM-DD)'),
    'especialidade': fields.String(description='Employee\'s specialization'),
    'endereco_id': fields.Integer(description='ID of the associated address'), # Foreign key
    'tipo_pessoa': fields.String(readOnly=True, description='Discriminator for person type'), # Discriminator
})

veterinario_model = person_ns.model('Veterinario', {
    # Inherits fields from Funcionario implicitly or explicitly
    'id': fields.Integer(readOnly=True),
    'nome': fields.String(required=True, description='Veterinarian\'s full name'),
    'cpf': fields.String(description='Veterinarian\'s CPF (11 digits)'),
    'telefone': fields.String(description='Veterinarian\'s phone number'),
    'email': fields.String(description='Veterinarian\'s email address'),
    'data_nascimento': fields.Date(description='Veterinarian\'s date of birth (YYYY-MM-DD)'),
    'ativo': fields.Boolean(description='Is the veterinarian active?'),
    'cargo': fields.String(description='Veterinarian\'s role (Inherited from Funcionario)'), # Inherited
    'salario': fields.Float(description='Veterinarian\'s salary (Inherited from Funcionario)'), # Inherited
    'data_admissao': fields.Date(required=True, description='Veterinarian\'s start date (YYYY-MM-DD)'), # Inherited
    'especialidade': fields.String(description='Veterinarian\'s specialization (Inherited from Funcionario)'), # Inherited
    'endereco_id': fields.Integer(description='ID of the associated address'), # Foreign key
    'tipo_pessoa': fields.String(readOnly=True, description='Discriminator for person type'), # Discriminator
    'crmv': fields.String(required=True, description='Veterinarian\'s CRMV number'),
})


# Helper function for common person validations
def validate_person_data(data: dict, is_update: bool = False):
    # Common validations for Pessoa fields
    if 'nome' in data and (not data['nome'] or not isinstance(data['nome'], str)):
        abort(400, message='Nome is required and must be a non-empty string.')

    if 'cpf' in data and data['cpf'] is not None:
        if not isinstance(data['cpf'], str) or len(data['cpf']) != 11 or not data['cpf'].isdigit():
            abort(400, message='CPF must be a string of 11 digits.')

    if 'email' in data and data['email'] is not None:
        # Basic email format validation
        if not isinstance(data['email'], str) or not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
             abort(400, message='Invalid email format.')

    date_fields = ['data_nascimento', 'data_admissao']
    for field in date_fields:
        if field in data and data[field] is not None:
             if isinstance(data[field], str):
                 try:
                     data[field] = date.fromisoformat(data[field])
                 except ValueError:
                     abort(400, message=f'Invalid date format for {field}. Use YYYY-MM-DD.')
             # Optional: Ensure date is not in the future (for data_nascimento)
             if field == 'data_nascimento' and data[field] > date.today():
                  abort(400, message=f'{field} cannot be in the future.')


    if 'salario' in data and data['salario'] is not None:
        if not isinstance(data['salario'], (int, float)) or data['salario'] < 0:
            abort(400, message='Salario must be a non-negative number.')

    # Endereco validation (requires tenant_id context)
    if 'endereco_id' in data and data['endereco_id'] is not None:
        if not isinstance(data['endereco_id'], int) or data['endereco_id'] <= 0:
            abort(400, message='Endereco ID must be a positive integer.')
        # Validate if the address exists and belongs to the current tenant
        current_tenant_id = get_current_tenant_id()
        endereco = Endereco.query.filter_by(id=data['endereco_id'], tenant_id=current_tenant_id).first()
        if not endereco:
            abort(404, message=f'Address with ID {data["endereco_id"]} not found for this tenant.')


# --- Cliente Resources ---

@person_ns.route('/clientes')
class ClienteList(Resource):
    # @jwt_required() # Add JWT protection if required
    @person_ns.doc('list_clientes')
    @person_ns.marshal_list_with(cliente_model)
    def get(self):
        """
        Lists all clients for the current tenant
        """
        current_tenant_id = get_current_tenant_id()
        clientes = Cliente.query.filter_by(tenant_id=current_tenant_id).all()
        return clientes

    # @jwt_required() # Add JWT protection if required
    @person_ns.doc('create_cliente')
    @person_ns.expect(cliente_model)
    @person_ns.marshal_with(cliente_model, code=201)
    def post(self):
        """
        Creates a new client for the current tenant
        """
        try:
            current_tenant_id = get_current_tenant_id()
            data = person_ns.payload

            # Apply common person validations
            validate_person_data(data)

            # Cliente specific validations
            if 'nome' not in data or not data['nome']:
                 abort(400, message='Nome is required for Cliente.')


            new_cliente = Cliente(tenant_id=current_tenant_id, **data)
            db.session.add(new_cliente)
            db.session.commit()
            return new_cliente, 201

        except IntegrityError as e:
            db.session.rollback()
            # Check for specific integrity errors if needed (e.g., duplicate CPF/email if unique)
            abort(409, message='Resource already exists or violates unique constraint.')
        except DataError as e:
             db.session.rollback()
             abort(400, message='Invalid data format or value.')
        except SQLAlchemyError as e:
            db.session.rollback()
            # Log the error: current_app.logger.error(f"Database error creating cliente: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
             db.session.rollback()
             # Log the error: current_app.logger.error(f"An unexpected error occurred creating cliente: {e}")
             abort(500, message='An error occurred during client creation.')


@person_ns.route('/clientes/<int:id>')
@person_ns.param('id', 'The client identifier')
class ClienteResource(Resource):
    # @jwt_required() # Add JWT protection
    @person_ns.doc('get_cliente')
    @person_ns.marshal_with(cliente_model)
    def get(self, id):
        """
        Gets a client by its ID for the current tenant
        """
        current_tenant_id = get_current_tenant_id()
        # Explicitly filter by tenant_id
        cliente = Cliente.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
            description=f"Cliente with ID {id} not found for this tenant"
        )
        return cliente

    # @jwt_required() # Add JWT protection
    @person_ns.doc('update_cliente')
    @person_ns.expect(cliente_model, validate=False) # validate=False allows partial updates
    @person_ns.marshal_with(cliente_model)
    def put(self, id):
        """
        Updates a client by its ID for the current tenant
        """
        try:
            current_tenant_id = get_current_tenant_id()
            # Explicitly filter by tenant_id
            cliente = Cliente.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                description=f"Cliente with ID {id} not found for this tenant"
            )

            update_data = person_ns.payload

            # Apply common person validations to update data
            validate_person_data(update_data, is_update=True)

            # Prevent updating tenant_id or tipo_pessoa via PUT
            update_data.pop('tenant_id', None)
            update_data.pop('tipo_pessoa', None)


            for key, value in update_data.items():
                setattr(cliente, key, value)

            db.session.commit()
            return cliente

        except SQLAlchemyError as e:
            db.session.rollback()
            # Log the error: current_app.logger.error(f"Database error updating cliente {id}: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            db.session.rollback()
            # Log the error: current_app.logger.error(f"An unexpected error occurred updating cliente {id}: {e}")
            abort(500, message='An error occurred during client update.')


    # @jwt_required() # Add JWT protection
    @person_ns.doc('delete_cliente')
    @person_ns.response(204, 'Client successfully deleted')
    @person_ns.response(404, 'Client not found for this tenant')
    def delete(self, id):
        """
        Deletes a client by its ID for the current tenant
        """
        try:
            current_tenant_id = get_current_tenant_id()
            # Explicitly filter by tenant_id
            cliente = Cliente.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                description=f"Cliente with ID {id} not found for this tenant"
            )

            db.session.delete(cliente)
            db.session.commit()
            return '', 204 # 204 No Content on successful deletion

        except SQLAlchemyError as e:
            db.session.rollback()
            # Log the error: current_app.logger.error(f"Database error deleting cliente {id}: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            db.session.rollback()
            # Log the error: current_app.logger.error(f"An unexpected error occurred deleting cliente {id}: {e}")
            abort(500, message='An error occurred during client deletion.')


# --- Funcionario Resources ---

@person_ns.route('/funcionarios')
class FuncionarioList(Resource):
    # @jwt_required() # Add JWT protection
    @person_ns.doc('list_funcionarios')
    @person_ns.marshal_list_with(funcionario_model)
    def get(self):
        """
        Lists all employees for the current tenant
        """
        current_tenant_id = get_current_tenant_id()
        # You might want to filter out Veterinarians here depending on requirements
        # Ensure filtering by tenant_id for employees
        funcionarios = Funcionario.query.filter_by(tenant_id=current_tenant_id).filter(Funcionario.tipo_pessoa == 'funcionario').all()
        return funcionarios

    # @jwt_required() # Add JWT protection
    @person_ns.doc('create_funcionario')
    @person_ns.expect(funcionario_model) # Note: Expecting generic funcionario model
    @person_ns.marshal_with(funcionario_model, code=201)
    def post(self):
        """
        Creates a new employee for the current tenant
        """
        try:
            current_tenant_id = get_current_tenant_id()
            data = person_ns.payload

            # Apply common person validations
            validate_person_data(data)

            # Funcionario specific validations
            required_fields = ['data_admissao', 'cargo']
            for field in required_fields:
                 if field not in data or not data[field]:
                      abort(400, message=f'Missing or empty required field for Funcionario: {field}')

            # Ensure the correct type is set for polymorphic identity
            data['tipo_pessoa'] = 'funcionario'

            new_funcionario = Funcionario(tenant_id=current_tenant_id, **data)
            db.session.add(new_funcionario)
            db.session.commit()
            return new_funcionario, 201

        except IntegrityError as e:
            db.session.rollback()
            abort(409, message='Resource already exists or violates unique constraint.')
        except DataError as e:
             db.session.rollback()
             abort(400, message='Invalid data format or value.')
        except SQLAlchemyError as e:
            db.session.rollback()
            # Log the error: current_app.logger.error(f"Database error creating funcionario: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
             db.session.rollback()
             # Log the error: current_app.logger.error(f"An unexpected error occurred creating funcionario: {e}")
             abort(500, message='An error occurred during employee creation.')


@person_ns.route('/funcionarios/<int:id>')
@person_ns.param('id', 'The employee identifier')
class FuncionarioResource(Resource):
    # @jwt_required() # Add JWT protection
    @person_ns.doc('get_funcionario')
    @person_ns.marshal_with(funcionario_model)
    def get(self, id):
        """
        Gets an employee by its ID for the current tenant
        """
        current_tenant_id = get_current_tenant_id()
        # Fetching by the base class ID and filtering by tenant_id
        # Optional: Check if the fetched person is indeed a 'funcionario' type
        funcionario = Funcionario.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
             description=f"Employee with ID {id} not found for this tenant"
        )
        if funcionario.tipo_pessoa != 'funcionario':
             # Although the query filters by tenant, an ID from another tenant but with the same person type could theoretically exist if not filtered by base class
             # This check adds an extra layer of safety after filtering by tenant on the base class ID
             abort(404, description=f"Employee with ID {id} not found for this tenant")

        return funcionario

    # @jwt_required() # Add JWT protection
    @person_ns.doc('update_funcionario')
    @person_ns.expect(funcionario_model, validate=False)
    @person_ns.marshal_with(funcionario_model)
    def put(self, id):
        """
        Updates an employee by its ID for the current tenant
        """
        try:
            current_tenant_id = get_current_tenant_id()
            funcionario = Funcionario.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                description=f"Employee with ID {id} not found for this tenant"
            )
            if funcionario.tipo_pessoa != 'funcionario':
                 abort(404, description=f"Employee with ID {id} not found for this tenant")


            update_data = person_ns.payload

            # Apply common person validations to update data
            validate_person_data(update_data, is_update=True)

            # Prevent changing the type or tenant_id via update
            update_data.pop('tipo_pessoa', None)
            update_data.pop('tenant_id', None)

            for key, value in update_data.items():
                setattr(funcionario, key, value)

            db.session.commit()
            return funcionario

        except SQLAlchemyError as e:
            db.session.rollback()
            # Log the error: current_app.logger.error(f"Database error updating funcionario {id}: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            db.session.rollback()
            # Log the error: current_app.logger.error(f"An unexpected error occurred updating funcionario {id}: {e}")
            abort(500, message='An error occurred during employee update.')


    # @jwt_required() # Add JWT protection
    @person_ns.doc('delete_funcionario')
    @person_ns.response(204, 'Employee successfully deleted')
    @person_ns.response(404, 'Employee not found for this tenant')
    def delete(self, id):
        """
        Deletes an employee by its ID for the current tenant
        """
        try:
            current_tenant_id = get_current_tenant_id()
            funcionario = Funcionario.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                description=f"Employee with ID {id} not found for this tenant"
            )
            if funcionario.tipo_pessoa != 'funcionario':
                 abort(404, description=f"Employee with ID {id} not found for this tenant")

            db.session.delete(funcionario)
            db.session.commit()
            return '', 204 # 204 No Content on successful deletion

        except SQLAlchemyError as e:
            db.session.rollback()
            # Log the error: current_app.logger.error(f"Database error deleting funcionario {id}: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            db.session.rollback()
            # Log the error: current_app.logger.error(f"An unexpected error occurred deleting funcionario {id}: {e}")
            abort(500, message='An error occurred during employee deletion.')


# --- Veterinario Resources ---

@person_ns.route('/veterinarios')
class VeterinarioList(Resource):
    # @jwt_required() # Add JWT protection
    @person_ns.doc('list_veterinarios')
    @person_ns.marshal_list_with(veterinario_model)
    def get(self):
        """
        Lists all veterinarians for the current tenant
        """
        current_tenant_id = get_current_tenant_id()
        # Ensure filtering by tenant_id for veterinarians
        veterinarios = Veterinario.query.filter_by(tenant_id=current_tenant_id).all()
        return veterinarios

    # @jwt_required() # Add JWT protection
    @person_ns.doc('create_veterinario')
    @person_ns.expect(veterinario_model)
    @person_ns.marshal_with(veterinario_model, code=201)
    def post(self):
        """
        Creates a new veterinarian for the current tenant
        """
        try:
            current_tenant_id = get_current_tenant_id()
            data = person_ns.payload

            # Apply common person validations
            validate_person_data(data)

            # Veterinario specific validations
            required_fields = ['data_admissao', 'crmv']
            for field in required_fields:
                 if field not in data or not data[field]:
                      abort(400, message=f'Missing or empty required field for Veterinario: {field}')

            if 'crmv' in data and data['crmv'] is not None:
                if not isinstance(data['crmv'], str) or not data['crmv']:
                     abort(400, message='CRMV is required and must be a non-empty string.')
                # Add more specific CRMV format validation if needed

            # Ensure the correct type is set for polymorphic identity
            data['tipo_pessoa'] = 'veterinario'

            new_veterinario = Veterinario(tenant_id=current_tenant_id, **data)
            db.session.add(new_veterinario)
            db.session.commit()
            return new_veterinario, 201

        except IntegrityError as e:
            db.session.rollback()
            # Check for specific integrity errors (e.g., duplicate CRMV if unique)
            abort(409, message='Resource already exists or violates unique constraint.')
        except DataError as e:
             db.session.rollback()
             abort(400, message='Invalid data format or value.')
        except SQLAlchemyError as e:
            db.session.rollback()
            # Log the error: current_app.logger.error(f"Database error creating veterinario: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
             db.session.rollback()
             # Log the error: current_app.logger.error(f"An unexpected error occurred creating veterinario: {e}")
             abort(500, message='An error occurred during veterinarian creation.')


@person_ns.route('/veterinarios/<int:id>')
@person_ns.param('id', 'The veterinarian identifier')
class VeterinarioResource(Resource):
    # @jwt_required() # Add JWT protection
    @person_ns.doc('get_veterinario')
    @person_ns.marshal_with(veterinario_model)
    def get(self, id):
        """
        Gets a veterinarian by its ID for the current tenant
        """
        current_tenant_id = get_current_tenant_id()
        # Fetching by the base class ID and filtering by tenant_id
        veterinario = Veterinario.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
             description=f"Veterinarian with ID {id} not found for this tenant"
        )
        if not isinstance(veterinario, Veterinario):
             # Extra safety check if the filtered result somehow isn't the expected type
             abort(404, description=f"Veterinarian with ID {id} not found for this tenant")

        return veterinario

    # @jwt_required() # Add JWT protection
    @person_ns.doc('update_veterinario')
    @person_ns.expect(veterinario_model, validate=False)
    @person_ns.marshal_with(veterinario_model)
    def put(self, id):
        """
        Updates a veterinarian by its ID for the current tenant
        """
        try:
            current_tenant_id = get_current_tenant_id()
            veterinario = Veterinario.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                description=f"Veterinarian with ID {id} not found for this tenant"
            )
            if not isinstance(veterinario, Veterinario):
                 abort(404, description=f"Veterinarian with ID {id} not found for this tenant")


            update_data = person_ns.payload

            # Apply common person validations to update data
            validate_person_data(update_data, is_update=True)

            # Prevent changing the type or tenant_id via update
            update_data.pop('tipo_pessoa', None)
            update_data.pop('tenant_id', None)

            # Veterinario specific validation for update
            if 'crmv' in update_data and update_data['crmv'] is not None:
                 if not isinstance(update_data['crmv'], str) or not update_data['crmv']:
                      abort(400, message='CRMV cannot be empty if provided.')
                 # Add more specific CRMV format validation if needed

            for key, value in update_data.items():
                setattr(veterinario, key, value)

            db.session.commit()
            return veterinario

        except SQLAlchemyError as e:
            db.session.rollback()
            # Log the error: current_app.logger.error(f"Database error updating veterinario {id}: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            db.session.rollback()
            # Log the error: current_app.logger.error(f"An unexpected error occurred updating veterinario {id}: {e}")
            abort(500, message='An error occurred during veterinarian update.')


    # @jwt_required() # Add JWT protection
    @person_ns.doc('delete_veterinario')
    @person_ns.response(204, 'Veterinarian deleted')
    @person_ns.response(404, 'Veterinarian not found for this tenant')
    def delete(self, id):
        """
        Deletes a veterinarian by its ID for the current tenant
        """
        try:
            current_tenant_id = get_current_tenant_id()
            veterinario = Veterinario.query.filter_by(id=id, tenant_id=current_tenant_id).first_or_404(
                description=f"Veterinarian with ID {id} not found for this tenant"
            )
            if not isinstance(veterinario, Veterinario):
                 abort(404, description=f"Veterinarian with ID {id} not found for this tenant")

            db.session.delete(veterinario)
            db.session.commit()
            return '', 204 # 204 No Content on successful deletion

        except SQLAlchemyError as e:
            db.session.rollback()
            # Log the error: current_app.logger.error(f"Database error deleting veterinario {id}: {e}")
            abort(500, message='Database error occurred.')
        except Exception as e:
            db.session.rollback()
            # Log the error: current_app.logger.error(f"An unexpected error occurred deleting veterinario {id}: {e}")
            abort(500, message='An error occurred during veterinarian deletion.')
