#wsgi.py
"""
WSGI Entry Point for the Canil Management System
This file serves as the main entry point for both development and production.
"""

import os
from app import create_app
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Create the Flask application instance
app = create_app()

if __name__ == '__main__':
    # Development server configuration
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    
    print(f"🐕 Starting Canil Management System...")
    print(f"📍 Environment: {app.config.get('ENV', 'development')}")
    print(f"🔧 Debug mode: {debug_mode}")
    print(f"🌐 Running on: http://{host}:{port}")
    
    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        use_reloader=debug_mode,
        threaded=True
    )