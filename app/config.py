"""
Configuration settings for Canil Management System
Supports multiple environments: development, testing, production
"""

import os
from datetime import timedelta
from urllib.parse import quote_plus


class Config:
    """Base configuration class with common settings."""
    
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Application settings
    APP_NAME = 'Canil Management System'
    APP_VERSION = '1.0.0'
    
    # Pagination
    ITEMS_PER_PAGE = 10
    MAX_ITEMS_PER_PAGE = 100
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx'}
    
    # Email configuration (if needed)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Dropbox API Configuration
    DROPBOX_APP_KEY = os.environ.get('DROPBOX_APP_KEY')
    DROPBOX_APP_SECRET = os.environ.get('DROPBOX_APP_SECRET')
    DROPBOX_ACCESS_TOKEN = os.environ.get('DROPBOX_ACCESS_TOKEN')
    DROPBOX_ROOT_PATH = os.environ.get('DROPBOX_ROOT_PATH', '/Apps/CanilApp')
    
    # Redis Configuration for Cache and Celery
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = REDIS_URL
    
    # Celery Configuration
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'UTC'
    
    # Mercado Pago Configuration
    MERCADO_PAGO_ACCESS_TOKEN = os.environ.get('MERCADO_PAGO_ACCESS_TOKEN')
    MERCADO_PAGO_WEBHOOK_SECRET = os.environ.get('MERCADO_PAGO_WEBHOOK_SECRET')
    
    # Multi-tenant configuration
    MAIN_DOMAIN = os.environ.get('MAIN_DOMAIN', 'localhost')
    DEFAULT_TENANT_SCHEMA = 'public'
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    @staticmethod
    def init_app(app):
        """Initialize app-specific configuration."""
        pass
    
    @classmethod
    def get_database_uri(cls):
        """Build database URI from environment variables."""
        db_user = os.environ.get('DB_USER', 'postgres')
        db_password = os.environ.get('DB_PASSWORD', 'password')
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '5432')
        db_name = os.environ.get('DB_NAME', 'canil_db')
        
        # URL encode password to handle special characters
        db_password_encoded = quote_plus(db_password)
        
        return f'postgresql://{db_user}:{db_password_encoded}@{db_host}:{db_port}/{db_name}'


class DevelopmentConfig(Config):
    """Development environment configuration."""
    
    DEBUG = True
    TESTING = False
    
    # Database - definir como variável de classe simples
    SQLALCHEMY_DATABASE_URI = 'postgresql://canil_user:canil123@localhost:5432/canil_db'
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    
    # Development-specific settings
    EXPLAIN_TEMPLATE_LOADING = False
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    
    # Development-specific settings
    EXPLAIN_TEMPLATE_LOADING = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Enable SQL query logging in development
        import logging
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


class TestingConfig(Config):
    """Testing environment configuration."""
    
    TESTING = True
    DEBUG = True
    
    # Use in-memory SQLite for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Faster password hashing for tests
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=30)
    
    # Disable external services in tests
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


class ProductionConfig(Config):
    """Production environment configuration."""
    
    DEBUG = False
    TESTING = False
    
    # Database with connection pooling
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or 
        Config.get_database_uri()
    )
    
    # Enhanced security in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Logging
    LOG_LEVEL = 'INFO'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production-specific logging setup
        import logging
        from logging.handlers import SMTPHandler, SysLogHandler
        
        # Email error notifications (if configured)
        if app.config.get('MAIL_SERVER'):
            auth = None
            if app.config.get('MAIL_USERNAME'):
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            
            secure = None
            if app.config.get('MAIL_USE_TLS'):
                secure = ()
            
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr=app.config['MAIL_DEFAULT_SENDER'],
                toaddrs=app.config.get('ADMIN_EMAILS', []),
                subject='Canil System Error',
                credentials=auth,
                secure=secure
            )
            
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)


class HerokuConfig(ProductionConfig):
    """Heroku-specific production configuration."""
    
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        
        # Heroku-specific logging
        import logging
        from logging import StreamHandler
        
        stream_handler = StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)


class DockerConfig(ProductionConfig):
    """Docker-specific production configuration."""
    
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Get configuration class by name."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config_by_name.get(config_name, DevelopmentConfig)