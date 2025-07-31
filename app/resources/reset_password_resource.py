from flask_restx import Namespace, Resource, fields
from app import db
from app.models.system import Usuario
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash # Import generate_password_hash
# TODO: Import generate_reset_token and verify_reset_token from app.utils.tokens


reset_password_ns = Namespace('reset_password', description='Password reset operations')

# Model for password reset request (initiate reset)
reset_request_model = reset_password_ns.model('ResetRequest', {
    'email_or_login': fields.String(required=True, description='User email or login')
})

# Model for password reset confirmation (set new password)
reset_confirm_model = reset_password_ns.model('ResetConfirm', {
    'token': fields.String(required=True, description='Password reset token'),
    'new_password': fields.String(required=True, description='New password')
})

# Model for success message response
success_message_model = reset_password_ns.model('SuccessMessage', {
    'message': fields.String
})

@reset_password_ns.route('/request')
class ResetPasswordRequest(Resource):
    @reset_password_ns.doc('request_password_reset')
    @reset_password_ns.expect(reset_request_model)
    @reset_password_ns.marshal_with(success_message_model)
    def post(self):
        """
        Request a password reset. Sends a reset token (simulate email for now).
        """
        data = reset_password_ns.payload
        email_or_login = data.get('email_or_login')
        
        if not email_or_login:
             reset_password_ns.abort(400, message='Missing email_or_login.')

        try:
            # 1. Find the user by email or login in the public schema
            user = Usuario.query.filter((Usuario.email == email_or_login) | (Usuario.login == email_or_login)).first()

            # 2. If user exists, generate a reset token and simulate sending an email
            if user:
                # TODO: token = generate_reset_token(user.id)
                # TODO: send_reset_email(user.email, token) # Placeholder function for sending email
                print(f"Simulating password reset request for: {email_or_login}. Email with reset token would be sent.") # Log for development

        except SQLAlchemyError as e:
             db.session.rollback()
             reset_password_ns.abort(500, message=f'Database error: {e}')
        return {'message': 'If a user with that email or login exists, a password reset link has been sent.'}, 200


@reset_password_ns.route('/confirm')
class ResetPasswordConfirm(Resource):
    @reset_password_ns.doc('confirm_password_reset')
    @reset_password_ns.expect(reset_confirm_model)
    @reset_password_ns.marshal_with(success_message_model)
    def post(self):
        """
        Confirm password reset with a token and set a new password.
        """
        data = reset_password_ns.payload
        token = data.get('token')
        new_password = data.get('new_password') # This will be validated by expect(reset_confirm_model)

        try:
            # 1. Verify the reset token and get the user ID
            # TODO: user_id = verify_reset_token(token)
            # if not user_id:
            #      reset_password_ns.abort(400, message='Invalid or expired token.')

            user_id = 1 # Placeholder: Assume token verification was successful and returned user_id 1
            if not token: # Basic check for token presence before placeholder verification
                 reset_password_ns.abort(400, message='Invalid or expired token.') # Or a more specific message after actual verification

            # 2. If token is valid, find the user and update their password
            user = Usuario.query.get(user_id)
            if user:
                user.senha = generate_password_hash(new_password) # Hash the new password
                db.session.commit()
                return {'message': 'Your password has been reset successfully.'}, 200
            else:
                 reset_password_ns.abort(400, message='Invalid or expired token.') # User not found for valid token? (shouldn't happen if token includes valid id)

        except SQLAlchemyError as e:
             db.session.rollback()
             reset_password_ns.abort(500, message=f'Database error: {e}')
             print(f"Simulating password reset confirmation with token: {token}")
        return {'message': 'Password reset simulation successful. Your password would have been updated.'}, 200 # Fallback or success for simulation
