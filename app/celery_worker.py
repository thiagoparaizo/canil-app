from celery import Celery
from flask import Flask

def create_celery_app(app=None):
    """
    Create a new Celery object and tie it to the Flask app's configuration.
    """
    if app is None:
        app = Flask(__name__)
        app.config.from_object('app.config.Config') # Assuming your config is here

    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        """
        Make celery tasks work with Flask app context
        """
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

# Example usage (if you were to run this file directly or import elsewhere)
# from app import create_app # Assuming you have a create_app factory
# app = create_app()
# celery_app = create_celery_app(app)