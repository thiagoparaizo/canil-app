from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .middleware.tenant_middleware import register_tenant_middleware
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager # Import JWTManager

db = SQLAlchemy()
jwt = JWTManager() # Initialize JWTManager

def create_app(config_object='app.config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_object)
    db.init_app(app)
    jwt.init_app(app) # Initialize JWT with app

 # Register the tenant middleware
    register_tenant_middleware(app)

    migrate = Migrate(app, db)

    # Import and register blueprints/resources here later

    return app