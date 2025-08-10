"""
Flask Application Factory for Canil Management System
This module contains the application factory function and app configuration.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_restx import Api
from werkzeug.exceptions import HTTPException

# Initialize extensions (without app binding)
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_object=None):
    """
    Application factory function that creates and configures the Flask app.
    
    Args:
        config_object: Configuration class or object to use
        
    Returns:
        Flask application instance
    """
    # Create Flask instance
    app = Flask(__name__)
    
    # Load configuration
    if config_object is None:
        config_object = 'app.config.Config'
    
    app.config.from_object(config_object)
    
    # Validate required configuration
    _validate_config(app)
    
    # Initialize extensions with app
    _init_extensions(app)
    
    # Register blueprints and APIs
    _register_blueprints(app)
    
    # Register error handlers
    _register_error_handlers(app)
    
    # Configure logging
    _configure_logging(app)
    
    # Register CLI commands
    _register_cli_commands(app)
    
    # Set up app context helpers
    _setup_app_context(app)
    
    return app


def _validate_config(app):
    """Validate required configuration variables."""
    required_configs = [
        'SECRET_KEY',
        'JWT_SECRET_KEY'
    ]
    
    missing_configs = []
    for config in required_configs:
        if not app.config.get(config):
            missing_configs.append(config)
    
    if missing_configs:
        raise ValueError(f"Missing required configuration: {', '.join(missing_configs)}")


def _init_extensions(app):
    """Initialize Flask extensions with the app."""
    # Database
    db.init_app(app)
    migrate.init_app(app, db)
    
    # JWT Authentication
    jwt.init_app(app)
    
    # Import models to ensure they are registered with SQLAlchemy
    with app.app_context():
        _import_models()


def _import_models():
    """Import all models to ensure they are registered with SQLAlchemy."""
    try:
        # Import the models package which will import all individual modules
        import app.models
        print("✅ All models imported successfully")
    except ImportError as e:
        print(f"⚠️  Warning: Could not import some models: {e}")
        # Try importing individual modules as fallback
        model_modules = [
            'tenant', 'system', 'animal', 'breeding', 
            'health', 'identity', 'person', 'transaction', 
            'media', 'saas'
        ]
        
        for module_name in model_modules:
            try:
                __import__(f'app.models.{module_name}')
                print(f"✅ {module_name} models imported")
            except ImportError as e:
                print(f"⚠️  Could not import {module_name}: {e}")


def _register_blueprints(app):
    """Register Flask blueprints and Flask-RESTx APIs."""
    # Create main API instance
    api = Api(
        app,
        version='1.0',
        title='Canil Management System API',
        description='A comprehensive kennel management system API',
        doc='/docs/',
        prefix='/api/v1'
    )
    
    # Register authentication namespace (no JWT required)
    try:
        from app.resources.auth_resource import auth_ns
        api.add_namespace(auth_ns, path='/auth')
    except ImportError as e:
        app.logger.warning(f"Could not import auth_resource: {e}")
    
    # Register password reset namespace (no JWT required)
    try:
        from app.resources.reset_password_resource import reset_password_ns
        api.add_namespace(reset_password_ns, path='/reset-password')
    except ImportError as e:
        app.logger.warning(f"Could not import reset_password_resource: {e}")
    
    # Register main application namespaces (JWT required)
    namespaces_to_register = [
        ('app.resources.animal_resource', 'animal_ns', '/animals'),
        ('app.resources.breeding_resource', 'breeding_ns', '/breeding'),
        ('app.resources.health_resource', 'health_ns', '/health'),
        ('app.resources.identity_resource', 'identity_ns', '/identity'),
        ('app.resources.person_resource', 'person_ns', '/people'),
        ('app.resources.transaction_resource', 'transaction_ns', '/transactions'),
        ('app.resources.media_resource', 'media_ns', '/media'),
        ('app.resources.system_resource', 'system_ns', '/system'),
        ('app.resources.saas_resource', 'saas_ns', '/saas'),
    ]
    
    for module_name, namespace_name, path in namespaces_to_register:
        try:
            module = __import__(module_name, fromlist=[namespace_name])
            namespace = getattr(module, namespace_name)
            api.add_namespace(namespace, path=path)
            app.logger.info(f"✅ Registered namespace: {namespace_name} at {path}")
        except (ImportError, AttributeError) as e:
            app.logger.warning(f"⚠️  Could not register {namespace_name}: {e}")
    
    # Register middleware
    _register_middleware(app)


def _register_middleware(app):
    """Register custom middleware."""
    try:
        from app.middleware.tenant_middleware import register_tenant_middleware
        register_tenant_middleware(app)
        app.logger.info("✅ Tenant middleware registered")
    except ImportError as e:
        app.logger.warning(f"⚠️  Could not register tenant middleware: {e}")


def _register_error_handlers(app):
    """Register global error handlers."""
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handle HTTP exceptions with JSON response."""
        return jsonify({
            'error': e.name,
            'message': e.description,
            'code': e.code
        }), e.code
    
    @app.errorhandler(500)
    def handle_internal_error(e):
        """Handle internal server errors."""
        db.session.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(404)
    def handle_not_found(e):
        """Handle 404 errors."""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(403)
    def handle_forbidden(e):
        """Handle 403 errors."""
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403


def _configure_logging(app):
    """Configure application logging."""
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Set up rotating file handler
        file_handler = RotatingFileHandler(
            'logs/canil_app.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Canil Management System startup')


def _register_cli_commands(app):
    """Register custom CLI commands."""
    
    @app.cli.command()
    def init_db():
        """Initialize the database with tables."""
        from flask import current_app
        
        try:
            db.create_all()
            current_app.logger.info("✅ Database tables created successfully")
            print("✅ Database initialized successfully!")
        except Exception as e:
            current_app.logger.error(f"❌ Error initializing database: {e}")
            print(f"❌ Error initializing database: {e}")
    
    @app.cli.command()
    def create_admin():
        """Create an admin user."""
        from app.models.system import Usuario
        from werkzeug.security import generate_password_hash
        
        try:
            # This would need to be implemented based on your User model
            admin = Usuario(
                login='admin@canil.com',
                senha=generate_password_hash('admin123'),
                perfil='admin',
                ativo=True,
                tenant_id=1  # Default tenant
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created successfully!")
            print("   Login: admin@canil.com")
            print("   Password: admin123")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin user: {e}")


def _setup_app_context(app):
    """Set up application context helpers."""
    
    # Setup app - executa na criação
    app.logger.info("🐕 Canil Management System started successfully")
    
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'database': 'connected' if _test_db_connection() else 'disconnected'
        })
    
    @app.route('/api-info')
    def api_info():
        """API information endpoint."""
        return jsonify({
            'name': 'Canil Management System API',
            'version': '1.0.0',
            'description': 'A comprehensive kennel management system',
            'endpoints': {
                'documentation': '/docs/',
                'health': '/health',
                'api': '/api/v1/'
            }
        })


def _test_db_connection():
    """Test database connection."""
    try:
        db.session.execute('SELECT 1')
        return True
    except Exception:
        return False