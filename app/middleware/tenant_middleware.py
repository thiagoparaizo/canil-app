from flask import request, current_app, abort
from sqlalchemy import text
from app import db # Assuming db is initialized in app/__init__.py
from app.models.tenant import Tenant # Import the Tenant model

def set_tenant_context():
    """
    Detects the tenant based on the subdomain and sets the SQLAlchemy search_path.
    """
    # Extract subdomain from request host
    host_parts = request.host.split('.')
    subdomain = host_parts[0] if len(host_parts) > 1 else ''

    # Prevent processing for local development domains
    if subdomain in ['', 'localhost'] or request.host == current_app.config.get('MAIN_DOMAIN'):
        try:
            db_session = db.session
            db_session.execute(text("SET search_path TO public;"))
        except Exception as e:
             current_app.logger.error(f"Error setting search_path to public: {e}")
        return

    # Skip tenant lookup for now to avoid model loading issues
    # TODO: Implement proper tenant detection after models are fully loaded
    current_app.logger.debug(f"Skipping tenant lookup for domain: {request.host}")
    return


def register_tenant_middleware(app):
    """
    Registers the set_tenant_context function as a before_request handler.
    """
    app.before_request(set_tenant_context)