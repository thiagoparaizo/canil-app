from flask import request, current_app, abort
from sqlalchemy import text
from app import db # Assuming db is initialized in app/__init__.py
from app.models.tenant import Tenant # Import the Tenant model

def set_tenant_context():
    """
    Detects the tenant based on the subdomain and sets the SQLAlchemy search_path.
    """
    # Extract subdomain from request host. Handle potential www. or other prefixes later if needed.
    # For simplicity, assuming subdomain is the first part of the host.
    host_parts = request.host.split('.')
    subdomain = host_parts[0] if len(host_parts) > 1 else ''

    # Prevent processing for local development domains like 'localhost' or IP addresses
    # and also for the main domain where public data is accessed.
    # You might need a more sophisticated check based on your config.
    if subdomain in ['', 'localhost'] or request.host == current_app.config.get('MAIN_DOMAIN'):
        current_app.logger.debug("Accessed main domain or localhost, setting search_path to public only.")
        try:
            db_session = db.session
            db_session.execute(text("SET search_path TO public;"))
        except Exception as e:
             current_app.logger.error(f"Error setting search_path to public: {e}")
        return

    # Query the public schema for the tenant using the domain (subdomain + main domain)
    # Assuming the Tenant model is accessible from the public schema implicitly or explicitly
    # In a real multi-schema app, querying the public schema might require a specific engine/session or connection setup
    # This example assumes Tenant model query works across schemas if configured correctly.
    # A more robust way might involve a separate engine/session for public schema.
    # For now, let's assume SQLAlchemy's model query can target public if not in a tenant context yet (which it isn't here).

    # Construct the full domain name to match the Tenant model's 'domain' field
    main_domain = current_app.config.get('MAIN_DOMAIN')
    full_domain = f"{subdomain}.{main_domain}" if main_domain else subdomain # Adjust based on your domain structure

    tenant = Tenant.query.filter_by(domain=full_domain).first()

    if tenant:
        try:
            # Set the search_path for the current database connection to tenant's schema and then public
            db_session = db.session
            # Important: Use the actual schema_name from the tenant object
            db_session.execute(text(f"SET search_path TO {tenant.schema_name}, public;"))
            current_app.logger.debug(f"Search path set to {tenant.schema_name}, public for tenant: {tenant.name}")
        except Exception as e:
            current_app.logger.error(f"Error setting search_path for tenant {tenant.name} ({full_domain}): {e}")
            # Depending on your requirements, you might want to abort the request or render an error page
            abort(500, description="Could not set tenant context.")
    else:
        # Handle cases where the domain doesn't match a tenant.
        # For tenant-specific routes, this should probably be a 404 or a specific error.
        # For now, we'll just log a warning and potentially set the path to public (already handled above).
        current_app.logger.warning(f"No tenant found for domain: {full_domain}. Request will likely fail if accessing tenant-specific data.")
        # If the request path indicates a tenant-specific resource, you might want to abort.
        # Example check (basic):
        # if request.path.startswith('/api/v1/animals') or request.path.startswith('/api/v1/breeding'):
        #    abort(404, description=f"No kennel found at {subdomain}")


def register_tenant_middleware(app):
    """
    Registers the set_tenant_context function as a before_request handler.
    """
    app.before_request(set_tenant_context)