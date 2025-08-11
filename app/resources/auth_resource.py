from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models.system import Usuario
from app.models.tenant import Tenant # Assuming Tenant model is needed to confirm tenant_id
from sqlalchemy.exc import SQLAlchemyError


auth_ns = Namespace('auth', description='Authentication operations')

# Model for login request
login_model = auth_ns.model('Login', {
    'login': fields.String(required=True, description='User login'),
    'senha': fields.String(required=True, description='User password')
})

# Model for login response (including JWT token)
auth_token_model = auth_ns.model('AuthToken', {
    'access_token': fields.String(required=True, description='JWT Access Token')
})

# Model for user registration request
register_model = auth_ns.model('RegisterUser', {
 'login': fields.String(required=True, description='User login (e.g., email)'),
 'senha': fields.String(required=True, description='User password'),
 'perfil': fields.String(required=True, description='User profile/role'),
 'tenant_id': fields.Integer(required=True, description='ID of the tenant the user belongs to')
})

# Model for /me response
user_info_model = auth_ns.model('UserInfo', {
 'user_id': fields.Integer(required=True, description='User ID'),
 'tenant_id': fields.Integer(required=True, description='Tenant ID')
})


@auth_ns.route('/login')
class UserLogin(Resource):
    @auth_ns.doc('user_login')
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(auth_token_model, code=200)
    def post(self):
        """
        Authenticate a user and return a JWT token.
        """
        data = auth_ns.payload
        login = data.get('login')
        senha = data.get('senha')

        # --- Start Validation ---
        if not login:
            auth_ns.abort(400, message='Missing login.')
        if not senha:
            auth_ns.abort(400, message='Missing password.')

        # Basic validation for login (assuming it's a username for now)
        if len(login) < 3:
            auth_ns.abort(400, message='Login must be at least 3 characters long.')

        # Basic validation for password minimum length
        if len(senha) < 6:
            auth_ns.abort(400, message='Password must be at least 6 characters long.')
        # --- End Validation ---

        # Explicitly query the public schema for the user
        try:
            # Ensure we query the public schema for the Usuario table
            user = db.session.query(Usuario).filter_by(login=login).first()

            if not user:
                auth_ns.abort(401, message='Invalid credentials') # Use generic message for security

            # Check the password hash
            if not check_password_hash(user.senha, senha):
                auth_ns.abort(401, message='Invalid credentials') # Use generic message for security

            # Authentication successful, create JWT
            # Include user_id and tenant_id in the token payload
            access_token = create_access_token(identity=str(user.id))

            return {'access_token': access_token}, 200

        except Exception as e:
            # Log the error for debugging
            print(f"Error during login for user {login}: {e}")
            auth_ns.abort(500, message='An error occurred during login')


@auth_ns.route('/register')
class UserRegister(Resource):
    @auth_ns.doc('register_user')
    @auth_ns.expect(register_model)
    @auth_ns.marshal_with(auth_token_model, code=201) # Or return just success message
    def post(self):
        """
        Register a new user.
        """
        data = auth_ns.payload
        login = data.get('login')
        senha = data.get('senha')
        perfil = data.get('perfil')
        tenant_id = data.get('tenant_id')

        # --- Start Validation ---
        if not login or not senha or not perfil or not tenant_id:
            auth_ns.abort(400, message='Missing required fields.')

        # TODO: Add more robust validation for login format (e.g., email)
        # TODO: Add password complexity validation
        # TODO: Validate perfil against allowed values

        try:
            # Ensure we query the public schema for Usuario and Tenant tables

            # 1. Validate Tenant existence
            tenant = db.session.query(Tenant).filter_by(id=tenant_id).first()
            if not tenant:
                auth_ns.abort(400, message=f'Tenant with ID {tenant_id} not found.')

            # 2. Check if login already exists
            existing_user = db.session.query(Usuario).filter_by(login=login).first()
            if existing_user:
                auth_ns.abort(409, message=f'Login \'{login}\' already exists.')

            # 3. Hash the password
            hashed_password = generate_password_hash(senha)

            # 4. Create the new user
            new_user = Usuario(
                login=login,
                senha=hashed_password, # Store hashed password
                perfil=perfil,
                tenant_id=tenant_id,
                ativo=True, # Assuming new users are active by default
                permissoes={} # Default empty permissions
                # Set ultimo_acesso on first login, not registration
            )

            db.session.add(new_user)
            db.session.commit()

            # Optional: Log the registration
            print(f"New user registered: {login} for tenant ID {tenant_id}")

            # Optional: Return a JWT token upon successful registration (auto-login)
            access_token = create_access_token(identity=str(new_user.id))

            return {'access_token': access_token}, 201
            # Or just return a success message:
            # return {'message': 'User registered successfully.'}, 201

        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error during user registration: {e}")
            auth_ns.abort(500, message='A database error occurred during registration.')
        except Exception as e:
            db.session.rollback()
            print(f"An unexpected error occurred during user registration: {e}")
            auth_ns.abort(500, message='An unexpected error occurred during registration.')

@auth_ns.route('/me')
class UserInfo(Resource):
    @auth_ns.doc('get_user_info')
    @jwt_required() # Protect this endpoint
    @auth_ns.marshal_with(user_info_model)
    def get(self):
        """
        Get information about the currently logged-in user.
        """
        current_user_id = get_jwt_identity()
        
        # Buscar o usuário no banco de dados
        user = db.session.query(Usuario).filter_by(id=int(current_user_id)).first()
        
        if not user:
            auth_ns.abort(404, message='User not found')

        return {'user_id': user.id, 'tenant_id': user.tenant_id}, 200