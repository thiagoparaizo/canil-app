import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:password@host:port/database'
    # Replace the placeholder with a development URL for now
    SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost:5432/canil_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret-jwt-key' # Add JWT Secret Key

    # Dropbox API Configuration
    DROPBOX_APP_KEY = os.environ.get('DROPBOX_APP_KEY') or 'YOUR_DROPBOX_APP_KEY'
    DROPBOX_APP_SECRET = os.environ.get('DROPBOX_APP_SECRET') or 'YOUR_DROPBOX_APP_SECRET'
    # If using a long-lived access token directly
    DROPBOX_ACCESS_TOKEN = os.environ.get('DROPBOX_ACCESS_TOKEN') or 'YOUR_DROPBOX_ACCESS_TOKEN'
    # Configure the root folder for the app if needed
    DROPBOX_ROOT_PATH = os.environ.get('DROPBOX_ROOT_PATH') or '/Apps/CanilApp' # Example path

    # Redis Configuration for Cache and Celery Broker
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CACHE_TYPE = 'RedisCache' # Example if using Flask-Caching with Redis
    CACHE_REDIS_URL = REDIS_URL # Example for Flask-Caching

    # Celery Configuration using Redis
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL