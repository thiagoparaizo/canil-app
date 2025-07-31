from flask import request
from flask_restx import Namespace, Resource, fields, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app import db
from app.models.saas import PlanoAssinatura, Assinatura, Pagamento
from app.models.tenant import Tenant
from app.services.payment_service import PaymentService
from datetime import date

# Assuming get_current_tenant is available from your middleware or authentication system
from app.middleware.tenant_middleware import get_current_tenant # Adjust import based on actual location

# Define models for API representation
plano_assinatura_model = saas_ns.model('PlanoAssinatura', {
    'id': fields.Integer(readOnly=True),
    'nome': fields.String(required=True),
    'descricao': fields.String,
    'valor': fields.Float(required=True),
    'limite_funcionarios': fields.Integer(default=0),
    'limite_animais': fields.Integer,
    'backup_automatico': fields.Boolean,
    'suporte_premium': fields.Boolean,
    'recursos': fields.String,  # Or fields.Raw for JSON
    'ativo': fields.Boolean,
    # Relationships to Assinaturas can be handled by a separate endpoint or nested models
})

assinatura_model = saas_ns.model('Assinatura', {
    'id': fields.Integer(readOnly=True),
    'plano_id': fields.Integer(required=True, description='ID of the subscription plan'),  # Foreign key
    'valor': fields.Float(required=True),
    'data_inicio': fields.Date(required=True),
    'data_vencimento': fields.Date,
    'status': fields.String(required=True, description="e.g., 'Ativa', 'Inativa', 'Cancelada', 'Em teste'"),
    'forma_pagamento': fields.String,
    'renovacao_automatica': fields.Boolean,
    'observacoes': fields.String,
    # Relationships to PlanoAssinatura, Tenant, and Pagamentos can be handled by nested models or IDs
})

pagamento_model = saas_ns.model('Pagamento', {
    'id': fields.Integer(readOnly=True),
    'assinatura_id': fields.Integer(required=True, description='ID of the associated subscription'),  # Foreign key
    'valor': fields.Float(required=True),
    'data_pagamento': fields.Date(required=True),
    'data_vencimento': fields.Date(description='Due date'),  # Due date
    'status': fields.String(required=True),  # e.g., 'Pendente', 'Confirmado', 'Recusado', 'Estornado'
    'metodo_pagamento': fields.String,
    'transacao_id': fields.String,
    'observacoes': fields.String,
    # Relationship to Assinatura can be handled by a nested model or ID
})

# Models for Mercado Pago integration
payment_request_model = saas_ns.model('PaymentRequest', {
    'transaction_amount': fields.Float(required=True, description='Amount to be paid'),
    'token': fields.String(required=True, description='Card token from Mercado Pago SDK'),
    'description': fields.String(description='Payment description'),
    'installments': fields.Integer(default=1, description='Number of installments'),
    'payment_method_id': fields.String(description='Mercado Pago payment method ID'),
    'payer': fields.Nested(saas_ns.model('PayerInfo', {
        'email': fields.String(required=True),
        # Add other payer details as required by Mercado Pago API
    }), required=True),
    'assinatura_id': fields.Integer(required=True, description='ID of the associated subscription'), # Link payment to subscription
    # Add other fields as required by Mercado Pago API
})

payment_response_model = saas_ns.model('PaymentResponse', {
    'id': fields.Integer(description='Mercado Pago Payment ID'),
    'status': fields.String(description='Payment status'),
    'status_detail': fields.String(description='Payment status detail'),
    'transaction_amount': fields.Float,
    'date_approved': fields.DateTime,
    'payment_method_id': fields.String,
    'description': fields.String,
    'local_payment_id': fields.Integer(description='ID of the local Pagamento record')
    # Add other relevant fields from Mercado Pago response
})


subscription_request_model = saas_ns.model('SubscriptionRequest', {
    'plano_id': fields.Integer(required=True, description='ID of the subscription plan'),
    # tenant_id is derived from context, not requested in payload
    'forma_pagamento': fields.String(description='Payment method for subscription'),
    'renovacao_automatica': fields.Boolean(default=True, description='Enable automatic renewal'),
    # Add fields required for initial payment or recurring setup via Mercado Pago
    'payment_data': fields.Nested(payment_request_model, required=False, description='Initial payment data for the subscription')
    # Add other fields as required for subscription creation in Mercado Pago
})

# Model for Webhook payload (simplified)
webhook_event_model = saas_ns.model('WebhookEvent', {
    'id': fields.String,
    'topic': fields.String(required=True),
    'resource': fields.String(required=True),
    'user': fields.Integer,
    'application_id': fields.Integer,
    'attempts': fields.Integer,
    'sent': fields.DateTime,
    'received': fields.DateTime,
    'data': fields.Raw # Raw data as received
    # You might need a more detailed model based on actual webhook structure
})


# --- PlanoAssinatura Resources ---

@saas_ns.route('/planos_assinatura')
class PlanoAssinaturaList(Resource):
    @saas_ns.doc('list_planos_assinatura')
    @saas_ns.marshal_list_with(plano_assinatura_model)
    def get(self):
        """List all subscription plans"""
        try:
            planos = PlanoAssinatura.query.all()
            return planos
        except SQLAlchemyError as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            saas_ns.abort(500, message=f'An error occurred: {e}')


    @saas_ns.doc('create_plano_assinatura')
    @saas_ns.expect(plano_assinatura_model)
    @saas_ns.marshal_with(plano_assinatura_model, code=201)
    def post(self):
        """Create a new subscription plan"""
        try:
            # Admin/System privilege check might be needed here
            data = saas_ns.payload

            # Add basic validations
            if data.get('valor') is not None and data['valor'] < 0:
                 saas_ns.abort(400, message='Valor must be a non-negative number.')
            if data.get('limite_funcionarios') is not None and data['limite_funcionarios'] < 0:
                 saas_ns.abort(400, message='Limite de funcionários must be a non-negative integer.')
            if data.get('limite_animais') is not None and data['limite_animais'] < 0:
                 saas_ns.abort(400, message='Limite de animais must be a non-negative integer.')

            new_plano = PlanoAssinatura(**data)
            db.session.add(new_plano)
            db.session.commit()
            return new_plano, 201
        except SQLAlchemyError as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'An error occurred: {e}')


@saas_ns.route('/planos_assinatura/<int:id>')
@saas_ns.param('id', 'The subscription plan identifier')
class PlanoAssinaturaResource(Resource):
    @saas_ns.doc('get_plano_assinatura')
    @saas_ns.marshal_with(plano_assinatura_model)
    def get(self, id):
        """Get a subscription plan by its ID"""
        try:
            plano = PlanoAssinatura.query.get_or_404(id)
            return plano
        except SQLAlchemyError as e:
            saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            saas_ns.abort(500, message=f'An error occurred: {e}')

    @saas_ns.doc('update_plano_assinatura')
    @saas_ns.expect(plano_assinatura_model)
    @saas_ns.marshal_with(plano_assinatura_model)
    def put(self, id):
        """Update a subscription plan by its ID"""
        # Admin/System privilege check might be needed here
        try:
            plano = PlanoAssinatura.query.get(id)
            if not plano:
                saas_ns.abort(404, message=f'Subscription plan with ID {id} not found.')

            data = saas_ns.payload

            # Add basic validations for updated fields
            if data.get('valor') is not None and data['valor'] < 0:
                 saas_ns.abort(400, message='Valor must be a non-negative number.')
            if data.get('limite_funcionarios') is not None and data['limite_funcionarios'] < 0:
                 saas_ns.abort(400, message='Limite de funcionários must be a non-negative integer.')
            if data.get('limite_animais') is not None and data['limite_animais'] < 0:
                 saas_ns.abort(400, message='Limite de animais must be a non-negative integer.')

            for key, value in data.items():
                setattr(plano, key, value)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'An error occurred: {e}')

    @saas_ns.doc('delete_plano_assinatura')
    @saas_ns.response(204, 'Subscription plan deleted')
    def delete(self, id):
        """Delete a subscription plan by its ID"""
        try:
            plano = PlanoAssinatura.query.get(id)
            if not plano:
                saas_ns.abort(404, message=f'Subscription plan with ID {id} not found.')
            db.session.delete(plano)
            db.session.commit()
            return '', 204
        except SQLAlchemyError as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'An error occurred: {e}')


# --- Assinatura Resources ---

@saas_ns.route('/assinaturas')
class AssinaturaList(Resource):
    @saas_ns.doc('list_assinaturas')
    @saas_ns.marshal_list_with(assinatura_model)
    def get(self):
        """List all subscriptions"""
        try:
            assinaturas = Assinatura.query.filter_by(tenant_id=get_current_tenant().id).all()
            return assinaturas
        except SQLAlchemyError as e:
            saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            saas_ns.abort(500, message=f'An error occurred: {e}')


    @saas_ns.doc('create_assinatura')
    @saas_ns.expect(assinatura_model)
    @saas_ns.marshal_with(assinatura_model, code=201)
    def post(self):
        """Create a new subscription (local record only - payment/mercadopago creation handled elsewhere)"""
        try:
            tenant_id = get_current_tenant().id # Get tenant_id from current context
            data = saas_ns.payload

            # Basic validation for foreign keys
            plano_id = data.get('plano_id')
            if not plano_id:
                saas_ns.abort(400, message='Missing plano_id.')

            # Validate required fields and data types
            if not data.get('valor') or data['valor'] <= 0:
                 saas_ns.abort(400, message='Valor is required and must be positive.')
            if not data.get('data_inicio'):
                 saas_ns.abort(400, message='Data de início is required.')
            # Optional: Validate date format if passed as string, or rely on fields.Date
            if not data.get('status'):
                 saas_ns.abort(400, message='Status is required.')
            # Optional: Validate status against allowed values
            allowed_statuses = ['Ativa', 'Inativa', 'Cancelada', 'Em teste', 'Pendente'] # Example statuses
            if data['status'] not in allowed_statuses:
                 saas_ns.abort(400, message=f"Invalid status. Allowed values are: {', '.join(allowed_statuses)}")

            # Check if PlanoAssinatura exists
            plano = PlanoAssinatura.query.get(plano_id)
            if not plano:
                saas_ns.abort(404, message=f'PlanoAssinatura with ID {plano_id} not found.')

            new_assinatura = Assinatura(tenant_id=tenant_id, **data)
            db.session.add(new_assinatura)
            db.session.commit()
            return new_assinatura, 201
        except (SQLAlchemyError, IntegrityError) as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'An error occurred: {e}')


@saas_ns.route('/assinaturas/<int:id>')
@saas_ns.param('id', 'The subscription identifier')
class AssinaturaResource(Resource):
    @saas_ns.doc('get_assinatura')
    @saas_ns.marshal_with(assinatura_model)
    def get(self, id):
        """Get a subscription by its ID"""
        try:
            tenant_id = get_current_tenant().id
            assinatura = Assinatura.query.filter_by(id=id, tenant_id=tenant_id).first()
            if not assinatura:
                saas_ns.abort(404, message=f'Subscription with ID {id} not found for this tenant.')
            return assinatura
        except SQLAlchemyError as e:
             saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            saas_ns.abort(500, message=f'An error occurred: {e}')

    @saas_ns.doc('update_assinatura')
    @saas_ns.expect(assinatura_model)
    @saas_ns.marshal_with(assinatura_model)
    def put(self, id):
        """Update a subscription by its ID"""
        try:
            tenant_id = get_current_tenant().id
            assinatura = Assinatura.query.filter_by(id=id, tenant_id=tenant_id).first()
            if not assinatura:
                saas_ns.abort(404, message=f'Subscription with ID {id} not found for this tenant.')

            data = saas_ns.payload

            # Prevent updating foreign keys directly
            data.pop('plano_id', None)
            data.pop('tenant_id', None)

            # Validate received fields
            if data.get('valor') is not None and data['valor'] <= 0:
                 saas_ns.abort(400, message='Valor must be positive.')
            # Optional: Validate date formats if present
            if data.get('status') is not None:
                 allowed_statuses = ['Ativa', 'Inativa', 'Cancelada', 'Em teste', 'Pendente'] # Example statuses
                 if data['status'] not in allowed_statuses:
                      saas_ns.abort(400, message=f"Invalid status. Allowed values are: {', '.join(allowed_statuses)}")

            for key, value in data.items():
                 if hasattr(assinatura, key): # Only update if the attribute exists
                    setattr(assinatura, key, value)
                # else: ignore unknown fields or raise error

            db.session.commit()
            return assinatura
        except (SQLAlchemyError, IntegrityError) as e:
            saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'An error occurred: {e}')

    @saas_ns.doc('delete_assinatura')
    @saas_ns.response(204, 'Subscription deleted')
    def delete(self, id):
        """Delete a subscription by its ID"""
        # TODO: Implement multi-tenant filtering/check
        try:
            tenant_id = get_current_tenant().id
            assinatura = Assinatura.query.filter_by(id=id, tenant_id=tenant_id).first()
            if not assinatura:
                 saas_ns.abort(404, message=f'Subscription with ID {id} not found for this tenant.')
            db.session.commit()
            return '', 204
        except SQLAlchemyError as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'An error occurred: {e}')


# --- Pagamento Resources ---

@saas_ns.route('/pagamentos')
class PagamentoList(Resource):
    @saas_ns.doc('list_pagamentos')
    @saas_ns.marshal_list_with(pagamento_model)
    def get(self):
        """List all payments"""
        try:
            pagamentos = Pagamento.query.join(Assinatura).filter(Assinatura.tenant_id == get_current_tenant().id).all()
            return pagamentos
        except SQLAlchemyError as e:
            saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            saas_ns.abort(500, message=f'An error occurred: {e}')


    @saas_ns.doc('create_pagamento')
    @saas_ns.expect(pagamento_model)
    @saas_ns.marshal_with(pagamento_model, code=201)
    def post(self):
        """Create a new payment record (local record only - actual payment processing handled elsewhere)"""
        try:
            tenant_id = get_current_tenant().id
            data = saas_ns.payload

            # Validate required fields and data types
            assinatura_id = data.get('assinatura_id')
            if not assinatura_id:
                saas_ns.abort(400, message='Missing assinatura_id.')
            if not data.get('valor') or data['valor'] <= 0:
                 saas_ns.abort(400, message='Valor is required and must be positive.')
            if not data.get('data_pagamento'):
                 saas_ns.abort(400, message='Data de pagamento is required.')
            # Optional: Validate date format if passed as string, or rely on fields.Date
            if not data.get('status'):
                 saas_ns.abort(400, message='Status is required.')
            # Optional: Validate status against allowed values
            allowed_statuses = ['Pendente', 'Confirmado', 'Recusado', 'Estornado'] # Example statuses
            if data['status'] not in allowed_statuses:
                 saas_ns.abort(400, message=f"Invalid status. Allowed values are: {', '.join(allowed_statuses)}")

            # Check if Assinatura exists and belongs to the current tenant
            assinatura = Assinatura.query.filter_by(id=assinatura_id, tenant_id=tenant_id).first()
            if not assinatura:
                saas_ns.abort(404, message=f'Assinatura with ID {assinatura_id} not found for this tenant.')

            new_pagamento = Pagamento(**data)
            db.session.add(new_pagamento)
            db.session.commit()
            return new_pagamento, 201
        except (SQLAlchemyError, IntegrityError) as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'An error occurred: {e}')


@saas_ns.route('/pagamentos/<int:id>')
@saas_ns.param('id', 'The payment identifier')
class PagamentoResource(Resource):
    @saas_ns.doc('get_pagamento')
    @saas_ns.marshal_with(pagamento_model)
    def get(self, id):
        """Get a payment by its ID"""
        try:
            tenant_id = get_current_tenant().id
            pagamento = Pagamento.query.join(Assinatura).filter(Pagamento.id == id, Assinatura.tenant_id == tenant_id).first()
            if not pagamento:
                 saas_ns.abort(404, message=f'Payment with ID {id} not found for this tenant.')
            return pagamento
        except SQLAlchemyError as e:
             saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            saas_ns.abort(500, message=f'An error occurred: {e}')


    @saas_ns.doc('update_pagamento')
    @saas_ns.expect(pagamento_model)
    @saas_ns.marshal_with(pagamento_model)
    def put(self, id):
        """Update a payment by its ID"""
        try:
            tenant_id = get_current_tenant().id
            pagamento = Pagamento.query.join(Assinatura).filter(Pagamento.id == id, Assinatura.tenant_id == tenant_id).first()
            if not pagamento:
                 saas_ns.abort(404, message=f'Payment with ID {id} not found for this tenant.')

            data = saas_ns.payload

            data.pop('assinatura_id', None) # Prevent changing the associated subscription

            # Validate received fields
            if data.get('valor') is not None and data['valor'] <= 0:
                 saas_ns.abort(400, message='Valor must be positive.')
            # Optional: Validate date formats if present
            if data.get('status') is not None:
                 allowed_statuses = ['Pendente', 'Confirmado', 'Recusado', 'Estornado'] # Example statuses
                 if data['status'] not in allowed_statuses:
                      saas_ns.abort(400, message=f"Invalid status. Allowed values are: {', '.join(allowed_statuses)}")

            for key, value in data.items():
                 if hasattr(pagamento, key): # Only update if the attribute exists
                    setattr(pagamento, key, value)
            db.session.commit()
            return pagamento
        except SQLAlchemyError as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'An error occurred: {e}')

    @saas_ns.doc('delete_pagamento')
    @saas_ns.response(204, 'Payment deleted')
    def delete(self, id):
        """Delete a payment by its ID"""
        # TODO: Implement multi-tenant filtering/check
        try:
            tenant_id = get_current_tenant().id
            pagamento = Pagamento.query.join(Assinatura).filter(Pagamento.id == id, Assinatura.tenant_id == tenant_id).first()
            if not pagamento:
                 saas_ns.abort(404, message=f'Payment with ID {id} not found for this tenant.')
            db.session.commit()
            return '', 204
        except SQLAlchemyError as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'An error occurred: {e}')


# --- Mercado Pago Integration Endpoints ---

# Model for webhook request payload (example, adjust based on actual Mercado Pago structure)
# The raw payload might be more complex and require different parsing
mercadopago_webhook_model = saas_ns.model('MercadoPagoWebhookEvent', {
    'id': fields.String,
    'topic': fields.String,
    'resource': fields.String,
    # Add other expected fields from Mercado Pago webhook
})


@saas_ns.route('/pagamentos/process')
class ProcessPaymentResource(Resource):
    @saas_ns.doc('process_payment')
    @saas_ns.expect(payment_request_model)
    @saas_ns.marshal_with(payment_response_model, code=201)
    def post(self):
        """Process a payment using Mercado Pago"""
        try:
            payment_data = saas_ns.payload
            payment_service = PaymentService()

            # Validate input data (e.g., required fields in payment_data, valid assinatura_id)
            assinatura_id = payment_data.get('assinatura_id')
            if not assinatura_id:
                saas_ns.abort(400, message='Missing assinatura_id in payment data.')

            # Validate Mercado Pago specific fields
            if not payment_data.get('transaction_amount') or payment_data['transaction_amount'] <= 0:
                 saas_ns.abort(400, message='transaction_amount is required and must be positive.')
            if not payment_data.get('token'):
                 saas_ns.abort(400, message='token is required.')
            if not payment_data.get('payer') or not payment_data['payer'].get('email'):
                 saas_ns.abort(400, message='Payer email is required.')

            # Retrieve current tenant ID and ensure the subscription belongs to this tenant
            tenant_id = get_current_tenant().id
            assinatura = Assinatura.query.filter_by(id=assinatura_id, tenant_id=tenant_id).first()
            if not assinatura:
                 saas_ns.abort(404, message=f'Subscription with ID {assinatura_id} not found for this tenant')

            # Call the payment service to process the payment
            mp_response = payment_service.process_payment(payment_data)

            # Create or update local Pagamento record based on Mercado Pago response
            # This is a simplified example, you'd map MP response fields to your Pagamento model
            new_pagamento = Pagamento(
                assinatura_id=assinatura_id,
                valor=mp_response.get('transaction_amount'),
                data_pagamento=date.today(), # Or date from MP response if available
                status=mp_response.get('status', 'pendente'),
                metodo_pagamento=mp_response.get('payment_method_id'),
                transacao_id=mp_response.get('id')
                # Map other relevant fields
            )
            db.session.add(new_pagamento)
            db.session.commit()

            # Prepare response model
            response_data = {
                'id': mp_response.get('id'),
                'status': mp_response.get('status'),
                'status_detail': mp_response.get('status_detail'),
                'transaction_amount': mp_response.get('transaction_amount'),
                'date_approved': mp_response.get('date_approved'),
                'payment_method_id': mp_response.get('payment_method_id'),
                'description': mp_response.get('description'),
                'local_payment_id': new_pagamento.id
            }

            return response_data, 201

        except (SQLAlchemyError, IntegrityError) as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'Error processing payment: {e}')


@saas_ns.route('/assinaturas/criar_com_pagamento') # Naming convention adjusted for clarity
class CreateSubscriptionWithPaymentResource(Resource):
     @saas_ns.doc('create_subscription_with_payment')
     @saas_ns.expect(subscription_request_model)
     @saas_ns.marshal_with(assinatura_model, code=201)
     def post(self):
         """Create a new subscription and optionally process initial payment"""
         try:
             subscription_data = saas_ns.payload
             payment_data = subscription_data.pop('payment_data', None)
             tenant_id = get_current_tenant().id # Get tenant_id from context

             plano_id = subscription_data.get('plano_id')
             if not plano_id:
                 saas_ns.abort(400, message='Missing plano_id')

             # Validate other subscription data fields before creating
             if subscription_data.get('valor') is not None and subscription_data['valor'] <= 0:
                  saas_ns.abort(400, message='Valor must be positive.')
             if subscription_data.get('data_inicio') is None:
                  saas_ns.abort(400, message='Data de início is required.')
             # Optional: Validate date format
             if subscription_data.get('status') is not None: # Status might be set by the process, but validate if provided
                 allowed_statuses = ['Ativa', 'Inativa', 'Cancelada', 'Em teste', 'Pendente']
                 if subscription_data['status'] not in allowed_statuses:
                      saas_ns.abort(400, message=f"Invalid status. Allowed values are: {', '.join(allowed_statuses)}")

             plano = PlanoAssinatura.query.get(plano_id)
             if not plano or not tenant:
                 saas_ns.abort(404, message='PlanoAssinatura or Tenant not found') # Needs tenant check for Tenant


             # Create the local subscription record first (status could be 'pendente', 'ativo', etc.)
             new_assinatura = Assinatura(**subscription_data)
             new_assinatura.status = 'pendente' # Initial status before payment
             db.session.add(new_assinatura)
             db.session.commit() # Commit to get the subscription ID

             if payment_data:
                 # Link payment data to the newly created subscription
                 # Validate nested payment_data fields
                 if not payment_data.get('transaction_amount') or payment_data['transaction_amount'] <= 0:
                      saas_ns.abort(400, message='Payment transaction_amount is required and must be positive.')
                 if not payment_data.get('token'):
                      saas_ns.abort(400, message='Payment token is required.')
                 if not payment_data.get('payer') or not payment_data['payer'].get('email'):
                      saas_ns.abort(400, message='Payment payer email is required.')

                 # Add subscription ID to payment data
                 payment_data['assinatura_id'] = new_assinatura.id
                 # Process the initial payment
                 payment_service = PaymentService()
                 mp_response = payment_service.process_payment(payment_data)

                 # Update the subscription status based on payment result
                 if mp_response.get('status') == 'approved':
                     new_assinatura.status = 'ativa'
                 else:
                     new_assinatura.status = 'inativa' # Or 'pendente_pagamento'


                 # Create a local payment record linked to this subscription
                 new_pagamento = Pagamento(
                     assinatura_id=new_assinatura.id,
                     valor=mp_response.get('transaction_amount'),
                     data_pagamento=date.today(), # Or date from MP response
                     status=mp_response.get('status', 'pendente'),
                     metodo_pagamento=mp_response.get('payment_method_id'),
                     transacao_id=mp_response.get('id')
                     # Map other relevant fields
                 )
                 db.session.add(new_pagamento)


             db.session.commit() # Commit payment and subscription status update

             return new_assinatura, 201

         except (SQLAlchemyError, IntegrityError) as e:
             db.session.rollback()
             saas_ns.abort(500, message=f'Database error occurred: {e}')
         except Exception as e:
             db.session.rollback()
             saas_ns.abort(500, message=f'Error creating subscription with payment: {e}')


@saas_ns.route('/assinaturas/<int:id>/cancelar')
@saas_ns.param('id', 'The subscription identifier')
class CancelSubscriptionResource(Resource):
    @saas_ns.doc('cancel_subscription')
    @saas_ns.response(200, 'Subscription cancelled successfully')
    @saas_ns.response(404, 'Subscription not found')
    def post(self, id): # Using POST for action
        """Cancel a subscription"""
        try:
            tenant_id = get_current_tenant().id
            assinatura = Assinatura.query.filter_by(id=id, tenant_id=tenant_id).first()
            if not assinatura:
                 saas_ns.abort(404, message=f'Subscription with ID {id} not found for this tenant.')

            # Call the payment service to cancel in Mercado Pago
            payment_service = PaymentService()
            mp_response = payment_service.cancel_subscription(id) # Pass local sub ID, service maps to MP ID

            # Update local subscription status
            assinatura.status = 'cancelada'
            # TODO: Update data_vencimento if necessary

            db.session.commit()

            return {'message': 'Subscription cancelled successfully'}, 200

        except (SQLAlchemyError, IntegrityError) as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'Database error occurred: {e}')
        except Exception as e:
            db.session.rollback()
            saas_ns.abort(500, message=f'Error cancelling subscription: {e}')


@saas_ns.route('/webhooks/mercadopago')
class MercadoPagoWebhookResource(Resource):
    # @saas_ns.expect(mercadopago_webhook_model) # Webhook payload can vary, might not need strict validation here
    @saas_ns.response(200, 'Webhook received')
    def post(self):
        """Handle Mercado Pago webhook notifications"""
        try:
            webhook_data = request.json # Get raw JSON data from webhook
            # TODO: Implement webhook signature verification (e.g., using MP-Signature header and secret) for security

            payment_service = PaymentService()
            payment_service.handle_webhook(webhook_data)

            # Mercado Pago expects a 200 OK response quickly
            return '', 200

        except Exception as e:
            # Log the error but still return 200 to Mercado Pago if possible,
            # depending on how critical the error is and if you have a retry mechanism.
            # For critical errors, returning non-200 might be necessary for MP retries.
            # Logging is crucial here.
            print(f"Error handling Mercado Pago webhook: {e}") # Use proper logging
            # Depending on your error handling strategy, you might return a non-200 status
            # saas_ns.abort(500, message=f'Error processing webhook: {e}')
            return '', 200 # Or 500 if processing failed before acknowledging
