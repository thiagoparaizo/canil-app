from flask_restx import Namespace, Resource, fields, abort
from app import db
from app.models.system import Usuario, Configuracao, LogSistema, Backup, Endereco, Canil # Assuming these models are defined
from sqlalchemy.exc import SQLAlchemyError
from app.models.tenant import Tenant # Assuming Tenant model is needed
# from werkzeug.security import generate_password_hash # Uncomment when implementing password hashing
from datetime import datetime # Import datetime for default values

system_ns = Namespace('system', description='System related operations (Users, Configurations, Logs, Backups, Addresses, Kennels)')

# Define models for API representation
usuario_model = system_ns.model('Usuario', {
    'id': fields.Integer(readOnly=True),
    'login': fields.String(required=True),
    'perfil': fields.String(required=True),
    'ultimo_acesso': fields.DateTime,
    'ativo': fields.Boolean,
    'permissoes': fields.Raw, # For JSONB
    'tenant_id': fields.Integer(required=True), # Foreign key
    # Relationships to Tenant and Logs can be handled by nested models or IDs
})

configuracao_model = system_ns.model('Configuracao', {
    'id': fields.Integer(readOnly=True),
    'chave': fields.String(required=True),
    'valor': fields.String,
    'descricao': fields.String,
    'tipo': fields.String,
    'categoria': fields.String,
    'tenant_id': fields.Integer(required=True), # Foreign key
})

log_sistema_model = system_ns.model('LogSistema', {
    'id': fields.Integer(readOnly=True),
    'data_hora': fields.DateTime(required=True),
    'usuario_id': fields.Integer, # Foreign key (optional)
    'acao': fields.String(required=True),
    'tabela': fields.String,
    'dados_anteriores': fields.Raw, # For JSONB
    'dados_novos': fields.Raw, # For JSONB
    'ip': fields.String,
    'tenant_id': fields.Integer(required=True), # Foreign key
    # Relationships to Usuario and Tenant can be handled by nested models or IDs
})

backup_model = system_ns.model('Backup', {
    'id': fields.Integer(readOnly=True),
    'data_backup': fields.Date(required=True),
    'tipo': fields.String,
    'tamanho': fields.Float,
    'caminho': fields.String,
    'status': fields.String,
    'observacoes': fields.String,
    'tenant_id': fields.Integer(required=True), # Foreign key
})

endereco_model = system_ns.model('Endereco', {
    'id': fields.Integer(readOnly=True),
    'logradouro': fields.String(required=True),
    'numero': fields.String,
    'complemento': fields.String,
    'bairro': fields.String,
    'cidade': fields.String(required=True),
    'estado': fields.String(required=True),
    'cep': fields.String,
    'pais': fields.String,
    'tenant_id': fields.Integer(required=True), # Foreign key
    # Relationships to Cliente, Funcionario, Canil will be handled by separate endpoints or nested models
})

canil_model = system_ns.model('Canil', {
    'id': fields.Integer(readOnly=True),
    'nome': fields.String(required=True),
    'cnpj': fields.String,
    'registro_kennel': fields.String,
    'site': fields.String,
    'email': fields.String,
    'telefone': fields.String,
    'ativo': fields.Boolean,
    'tenant_id': fields.Integer(required=True), # Foreign key
    'endereco_id': fields.Integer, # Foreign key (1:1)
    # Relationship to Endereco can be handled by a nested model or ID
})

# --- Usuario Resources ---

@system_ns.route('/usuarios')
class UsuarioList(Resource):
    @system_ns.doc('list_usuarios')
    @system_ns.marshal_list_with(usuario_model)
    def get(self):
        """List all users"""
        # TODO: Apply @tenant_required decorator
        usuarios = Usuario.query.all()
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            usuarios = Usuario.query.filter_by(tenant_id=tenant_id).all()
            return usuarios
        except SQLAlchemyError as e:
            db.session.rollback()
            system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            system_ns.abort(500, message=f'An error occurred: {e}')

    @system_ns.doc('create_usuario')
    @system_ns.expect(usuario_model) # Note: Password handling should be done securely (not via direct model)
    @system_ns.marshal_with(usuario_model, code=201)
    def post(self):
        """Create a new user"""
        # TODO: Apply @tenant_required decorator
        data = system_ns.payload
        tenant_id = 1 # TODO: Get tenant_id from context/middleware

        if 'login' not in data or 'perfil' not in data:
            system_ns.abort(400, message='Missing required fields: login, perfil')

        # Password should be hashed before creating the user model instance
        # data['senha'] = generate_password_hash(data['senha'])
        new_usuario = Usuario(**data) # Needs adjustment for password handling
        db.session.add(new_usuario)
        db.session.commit()
        return new_usuario, 201

@system_ns.route('/usuarios/<int:id>')
@system_ns.param('id', 'The user identifier')
class UsuarioResource(Resource):
    @system_ns.doc('get_usuario')
    @system_ns.marshal_with(usuario_model)
    def get(self, id):
        """Get a user by its ID"""
        usuario = Usuario.query.get_or_404(id)
        return usuario

        # TODO: Apply @tenant_required decorator
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            usuario = Usuario.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
            return usuario
        except SQLAlchemyError as e:
             system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            system_ns.abort(500, message=f'An error occurred: {e}')

    @system_ns.doc('update_usuario')
    @system_ns.expect(usuario_model) # Note: Updating password requires separate logic
    @system_ns.marshal_with(usuario_model)
    def put(self, id):
        """Update a user by its ID"""
        usuario = Usuario.query.get_or_404(id)
        data = system_ns.payload
        # Prevent updating sensitive fields or require separate endpoints
        data.pop('senha', None)

        for key, value in data.items():
            setattr(usuario, key, value)

        db.session.commit()
        return usuario

    @system_ns.doc('delete_usuario')
    @system_ns.response(204, 'User deleted')
    def delete(self, id):
        """Delete a user by its ID"""
        usuario = Usuario.query.get_or_404(id)
        db.session.delete(usuario)
        db.session.commit()
        return '', 204

        # TODO: Apply @tenant_required decorator
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            usuario = Usuario.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
            data = system_ns.payload

            # Prevent updating sensitive fields or require separate endpoints
            data.pop('senha', None)
            data.pop('tenant_id', None) # Prevent updating tenant_id

            for key, value in data.items():
                setattr(usuario, key, value)

            db.session.commit()
            return usuario
        except SQLAlchemyError as e:
            db.session.rollback()
            system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            system_ns.abort(500, message=f'An error occurred: {e}')


# --- Configuracao Resources ---

@system_ns.route('/configuracoes')
class ConfiguracaoList(Resource):
    @system_ns.doc('list_configuracoes')
    @system_ns.marshal_list_with(configuracao_model)
    def get(self):
        """List all configurations"""
        configuracoes = Configuracao.query.all()
        return configuracoes

        # TODO: Apply @tenant_required decorator
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            configuracoes = Configuracao.query.filter_by(tenant_id=tenant_id).all()
            return configuracoes
        except SQLAlchemyError as e:
            system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            system_ns.abort(500, message=f'An error occurred: {e}')

    @system_ns.doc('create_configuracao')
    @system_ns.expect(configuracao_model)
    @system_ns.marshal_with(configuracao_model, code=201)
    def post(self):
        """Create a new configuration"""
        data = system_ns.payload
        new_configuracao = Configuracao(**data)
        db.session.add(new_configuracao)
        db.session.commit()
        return new_configuracao, 201

        # TODO: Apply @tenant_required decorator
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        data = system_ns.payload
        if 'chave' not in data:
            system_ns.abort(400, message='Missing required field: chave')
        try:
            new_configuracao = Configuracao(tenant_id=tenant_id, **data)
            db.session.add(new_configuracao)
            db.session.commit()
            return new_configuracao, 201
        except SQLAlchemyError as e:
            db.session.rollback()
            system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            system_ns.abort(500, message=f'An error occurred: {e}')

@system_ns.route('/configuracoes/<int:id>')
@system_ns.param('id', 'The configuration identifier')
class ConfiguracaoResource(Resource):
    @system_ns.doc('get_configuracao')
    @system_ns.marshal_with(configuracao_model)
    def get(self, id):
        """Get a configuration by its ID"""
        configuracao = Configuracao.query.get_or_404(id)
        return configuracao

        # TODO: Apply @tenant_required decorator
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            configuracao = Configuracao.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
            return configuracao
        except SQLAlchemyError as e:
             system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            system_ns.abort(500, message=f'An error occurred: {e}')

    @system_ns.doc('update_configuracao')
    @system_ns.expect(configuracao_model)
    @system_ns.marshal_with(configuracao_model)
    def put(self, id):
        """Update a configuration by its ID"""
        configuracao = Configuracao.query.get_or_404(id)
        data = system_ns.payload
        for key, value in data.items():
            setattr(configuracao, key, value)

        db.session.commit()
        return configuracao

    @system_ns.doc('delete_configuracao')
    @system_ns.response(204, 'Configuration deleted')
    def delete(self, id):
        """Delete a configuration by its ID"""
        configuracao = Configuracao.query.get_or_404(id)
        db.session.delete(configuracao)
        db.session.commit()
        return '', 204

        # TODO: Apply @tenant_required decorator
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            configuracao = Configuracao.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
            data = system_ns.payload

            # Prevent changing sensitive fields
            data.pop('chave', None)
            data.pop('tenant_id', None) # Prevent updating tenant_id

            for key, value in data.items():
                setattr(configuracao, key, value)

            db.session.commit()
            return configuracao
        except SQLAlchemyError as e:
            db.session.rollback()
            system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            system_ns.abort(500, message=f'An error occurred: {e}')

        # TODO: Apply @tenant_required decorator
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            configuracao = Configuracao.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
            db.session.delete(configuracao)
            db.session.commit()
            return '', 204
        except SQLAlchemyError as e:
            db.session.rollback()
            system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            system_ns.abort(500, message=f'An error occurred: {e}')


# --- LogSistema Resources ---
# Note: LogSistema is typically created internally, not via a public API
# However, providing read endpoints might be useful for administrators

@system_ns.route('/logs_sistema')
class LogSistemaList(Resource):
    @system_ns.doc('list_logs_sistema')
    @system_ns.marshal_list_with(log_sistema_model)
    def get(self):
        """List all system logs (admin only)"""
        # Authentication and authorization checks are crucial here
        logs = LogSistema.query.all()
        return logs

        # TODO: Apply @tenant_required decorator
        # TODO: Add admin authorization check
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            logs = LogSistema.query.filter_by(tenant_id=tenant_id).all()
            return logs
        except SQLAlchemyError as e:
            system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            system_ns.abort(500, message=f'An error occurred: {e}')

@system_ns.route('/logs_sistema/<int:id>')
@system_ns.param('id', 'The log entry identifier')
class LogSistemaResource(Resource):
    @system_ns.doc('get_log_sistema')
    @system_ns.marshal_with(log_sistema_model)
    def get(self, id):
        """Get a system log entry by its ID (admin only)"""
        # Authentication and authorization checks are crucial here
        log = LogSistema.query.get_or_404(id)
        return log

        # TODO: Apply @tenant_required decorator
        # TODO: Add admin authorization check
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            log = LogSistema.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
            return log
        except SQLAlchemyError as e:
             system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            system_ns.abort(500, message=f'An error occurred: {e}')

# --- Backup Resources ---
# Note: Backup operations might be triggered by internal processes or admin commands
# API endpoints could be for viewing backup status or triggering backups (with auth)

@system_ns.route('/backups')
class BackupList(Resource):
    @system_ns.doc('list_backups')
    @system_ns.marshal_list_with(backup_model)
    def get(self):
        """List all backups (admin only)"""
        # Authentication and authorization checks are crucial here
        backups = Backup.query.all()
        return backups

        # TODO: Apply @tenant_required decorator
        # TODO: Add admin authorization check
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            backups = Backup.query.filter_by(tenant_id=tenant_id).all()
            return backups
        except SQLAlchemyError as e:
            system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            system_ns.abort(500, message=f'An error occurred: {e}')

    @system_ns.doc('create_backup')
    @system_ns.response(201, 'Backup process initiated')
    def post(self):
        """Initiate a new backup process (admin only)"""
        # Authentication and authorization checks are crucial here
        # Trigger an asynchronous task (e.g., Celery) for backup
        # backup_task.delay()
        return {'message': 'Backup process initiated'}, 201

        # TODO: Apply @tenant_required decorator
        # TODO: Add admin authorization check
        # Trigger an asynchronous task (e.g., Celery) for backup
        # backup_task.delay(tenant_id=tenant_id) # Pass tenant_id to the task
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
             return {'message': 'Backup process initiated for tenant {}'.format(tenant_id)}, 201
        except Exception as e:
            system_ns.abort(500, message=f'Error initiating backup: {e}')

@system_ns.route('/backups/<int:id>')
@system_ns.param('id', 'The backup identifier')
class BackupResource(Resource):
    @system_ns.doc('get_backup')
    @system_ns.marshal_with(backup_model)
    def get(self, id):
        """Get a backup record by its ID (admin only)"""
        # Authentication and authorization checks are crucial here
        backup = Backup.query.get_or_404(id)
        return backup

        # TODO: Apply @tenant_required decorator
        # TODO: Add admin authorization check
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            backup = Backup.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
            return backup
        except SQLAlchemyError as e:
             system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            system_ns.abort(500, message=f'An error occurred: {e}')

# --- Endereco Resources ---
# Note: Endereco resources might be managed via related models (Cliente, Funcionario, Canil)
# However, providing direct access might be useful

@system_ns.route('/enderecos')
class EnderecoList(Resource):
    @system_ns.doc('list_enderecos')
    @system_ns.marshal_list_with(endereco_model)
    def get(self):
        """List all addresses"""
        enderecos = Endereco.query.all()
        return enderecos

        # TODO: Apply @tenant_required decorator
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            enderecos = Endereco.query.filter_by(tenant_id=tenant_id).all()
            return enderecos
        except SQLAlchemyError as e:
            system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            system_ns.abort(500, message=f'An error occurred: {e}')

    @system_ns.doc('create_endereco')
    @system_ns.expect(endereco_model)
    @system_ns.marshal_with(endereco_model, code=201)
    def post(self):
        """Create a new address"""
        data = system_ns.payload
        new_endereco = Endereco(**data)
        db.session.add(new_endereco)
        db.session.commit()
        return new_endereco, 201

        # TODO: Apply @tenant_required decorator
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        data = system_ns.payload
        if 'logradouro' not in data or 'cidade' not in data or 'estado' not in data:
            system_ns.abort(400, message='Missing required fields: logradouro, cidade, estado')
        try:
            new_endereco = Endereco(tenant_id=tenant_id, **data)
            db.session.add(new_endereco)
            db.session.commit()
            return new_endereco, 201
        except SQLAlchemyError as e:
            db.session.rollback()
            system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            system_ns.abort(500, message=f'An error occurred: {e}')

@system_ns.route('/enderecos/<int:id>')
@system_ns.param('id', 'The address identifier')
class EnderecoResource(Resource):
    @system_ns.doc('get_endereco')
    @system_ns.marshal_with(endereco_model)
    def get(self, id):
        """Get an address by its ID"""
        endereco = Endereco.query.get_or_404(id)
        return endereco

        # TODO: Apply @tenant_required decorator
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            endereco = Endereco.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
            return endereco
        except SQLAlchemyError as e:
             system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            system_ns.abort(500, message=f'An error occurred: {e}')

    @system_ns.doc('update_endereco')
    @system_ns.expect(endereco_model)
    @system_ns.marshal_with(endereco_model)
    def put(self, id):
        """Update an address by its ID"""
        endereco = Endereco.query.get_or_404(id)
        data = system_ns.payload
        for key, value in data.items():
            setattr(endereco, key, value)

        db.session.commit()
        return endereco

    @system_ns.doc('delete_endereco')
    @system_ns.response(204, 'Address deleted')
    def delete(self, id):
        """Delete an address by its ID"""
        endereco = Endereco.query.get_or_404(id)
        db.session.delete(endereco)
        db.session.commit()
        return '', 204

        # TODO: Apply @tenant_required decorator
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            endereco = Endereco.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
            data = system_ns.payload

            data.pop('tenant_id', None) # Prevent updating tenant_id

            for key, value in data.items():
                setattr(endereco, key, value)

            db.session.commit()
            return endereco
        except SQLAlchemyError as e:
            db.session.rollback()
            system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            system_ns.abort(500, message=f'An error occurred: {e}')

        # TODO: Apply @tenant_required decorator
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            endereco = Endereco.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
            db.session.delete(endereco)
            db.session.commit()
            return '', 204
        except SQLAlchemyError as e:
            db.session.rollback()
            system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            system_ns.abort(500, message=f'An error occurred: {e}')


# --- Canil Resources ---

@system_ns.route('/canis')
class CanilList(Resource):
    @system_ns.doc('list_canis')
    @system_ns.marshal_list_with(canil_model)
    def get(self):
        """List all kennels"""
        canis = Canil.query.all()
        return canis

        # TODO: Apply @tenant_required decorator
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            canis = Canil.query.filter_by(tenant_id=tenant_id).all()
            return canis
        except SQLAlchemyError as e:
            system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            system_ns.abort(500, message=f'An error occurred: {e}')

    @system_ns.doc('create_canil')
    @system_ns.expect(canil_model)
    @system_ns.marshal_with(canil_model, code=201)
    def post(self):
        """Create a new kennel"""
        data = system_ns.payload
        new_canil = Canil(**data)
        db.session.add(new_canil)
        db.session.commit()
        return new_canil, 201

        # TODO: Apply @tenant_required decorator
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        data = system_ns.payload
        if 'nome' not in data:
            system_ns.abort(400, message='Missing required field: nome')
        try:
            # Optional: Validate endereco_id exists for this tenant if provided
            # if 'endereco_id' in data and data['endereco_id']:
            #     endereco = Endereco.query.filter_by(id=data['endereco_id'], tenant_id=tenant_id).first()
            #     if not endereco:
            #         system_ns.abort(404, message=f'Address with ID {data["endereco_id"]} not found for this tenant')

            new_canil = Canil(tenant_id=tenant_id, **data)
            db.session.add(new_canil)
            db.session.commit()
            return new_canil, 201
        except SQLAlchemyError as e:
            db.session.rollback()
            system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            system_ns.abort(500, message=f'An error occurred: {e}')

@system_ns.route('/canis/<int:id>')
@system_ns.param('id', 'The kennel identifier')
class CanilResource(Resource):
    @system_ns.doc('get_canil')
    @system_ns.marshal_with(canil_model)
    def get(self, id):
        """Get a kennel by its ID"""
        canil = Canil.query.get_or_404(id)
        return canil

        # TODO: Apply @tenant_required decorator
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            canil = Canil.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
            return canil
        except SQLAlchemyError as e:
             system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            system_ns.abort(500, message=f'An error occurred: {e}')

    @system_ns.doc('update_canil')
    @system_ns.expect(canil_model)
    @system_ns.marshal_with(canil_model)
    def put(self, id):
        """Update a kennel by its ID"""
        canil = Canil.query.get_or_404(id)
        data = system_ns.payload

        # Preventing updating foreign keys directly, or add logic
        data.pop('endereco_id', None)

        for key, value in data.items():
            setattr(canil, key, value)

        db.session.commit()
        return canil

    @system_ns.doc('delete_canil')
    @system_ns.response(204, 'Kennel deleted')
    def delete(self, id):
        """Delete a kennel by its ID"""
        canil = Canil.query.get_or_404(id)
        db.session.delete(canil)
        db.session.commit()
        return '', 204

        # TODO: Apply @tenant_required decorator
        tenant_id = 1 # TODO: Get tenant_id from context/middleware
        try:
            canil = Canil.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
            data = system_ns.payload

            # Preventing updating foreign keys directly, or add logic
            data.pop('endereco_id', None) # Prevent updating foreign key directly
            data.pop('tenant_id', None) # Prevent updating tenant_id

            for key, value in data.items():
                setattr(canil, key, value)

            db.session.commit()
            return canil
        except SQLAlchemyError as e:
            db.session.rollback()
            system_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            system_ns.abort(500, message=f'An error occurred: {e}')