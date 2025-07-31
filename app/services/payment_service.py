import requests
from flask import current_app
import mercadopago
from mercadopago import exceptions
from app import db # Assuming db is available
# Assuming local models like Pagamento, Assinatura, Venda are defined elsewhere
# from app.models.transaction import Pagamento, Venda
# from app.models.saas import Assinatura

class PaymentService:
    def __init__(self):
        # Initialize Mercado Pago SDK client
        # Ensure MERCADO_PAGO_ACCESS_TOKEN is configured
        self.mercadopago_client = mercadopago.SDK(current_app.config.get("MERCADO_PAGO_ACCESS_TOKEN"))
        # Placeholder for API base URL if not using an SDK (kept for potential direct calls)
        self.base_url = "https://api.mercadopago.com"
        self.access_token = current_app.config.get("MERCADO_PAGO_ACCESS_TOKEN")

    def process_payment(self, payment_data: dict):
        """
        Process a payment through the Mercado Pago API using the SDK.
        payment_data should contain details like amount, tokenized card info, payer details, etc.
        The payment_data dictionary structure must match Mercado Pago SDK's requirements.
        """
        current_app.logger.info("Processing payment via PaymentService (Mercado Pago SDK)")
        # Ensure tenant_id is available in the context or passed in payment_data
        # tenant_id = payment_data.get('tenant_id') # Example: Pass tenant_id in data

        try:
            # Create the payment using the Mercado Pago SDK
            # The structure of payment_data is crucial and depends on your integration type (e.g., Checkout Pro, API)
            # Refer to Mercado Pago documentation for the required payment_data structure.
            # Example minimal payment_data structure:
            # {
            #     "transaction_amount": 100,
            #     "token": "...", # Tokenized card data
            #     "description": "Product description",
            #     "installments": 1,
            #     "payment_method_id": "visa",
            #     "payer": {
            #         "email": "test_user_123@test.com"
            #     }
            # }
            payment_response = self.mercadopago_client.payment.create(payment_data)

            # Mercado Pago SDK typically returns a dictionary with 'status' and 'response' keys
            # 'status' is the HTTP status code of the API call (e.g., 200, 201)
            # 'response' contains the actual payment data returned by the Mercado Pago API

            if payment_response and payment_response["status"] in [200, 201]: # Success status codes
               mp_payment_data = payment_response["response"]
               current_app.logger.info(f"Mercado Pago payment processed successfully. MP Payment ID: {mp_payment_data.get('id')}")

               # TODO: Save payment details to a local Pagamento model
               # Ensure Pagamento model has fields for Mercado Pago ID, status, amount, date,
               # and links to the tenant and related entities (e.g., Venda, Assinatura)
               # try:
               #     new_pagamento = Pagamento(
               #         mp_id=mp_payment_data.get('id'),
               #         status=mp_payment_data.get('status'),
               #         amount=mp_payment_data.get('transaction_amount'),
               #         data_criacao=datetime.fromisoformat(mp_payment_data.get('date_created').replace('Z', '+00:00')) if mp_payment_data.get('date_created') else datetime.utcnow(),
               #         tenant_id=tenant_id, # Get tenant_id from context or data
               #         # Link to Venda or Assinatura based on context
               #         # venda_id=...,
               #         # assinatura_id=...,
               #         raw_response=mp_payment_data # Optionally store the full response
               #     )
               #     db.session.add(new_pagamento)
               #     db.session.commit()
               #     current_app.logger.info(f"Local Pagamento record created for MP ID: {mp_payment_data.get('id')}")
               # except Exception as db_error:
               #     current_app.logger.error(f"Failed to save local payment record for MP ID {mp_payment_data.get('id')}: {db_error}")
               #     # Decide how to handle DB save failure after successful MP payment (log, alert, compensate)
               #     # db.session.rollback()


               # Return the Mercado Pago payment response data
               return mp_payment_data
            else:
               # Handle errors from the SDK response (non-success status codes)
               error_response = payment_response.get("response", {"message": "Unknown error from Mercado Pago SDK"})
               current_app.logger.error(f"Mercado Pago SDK payment error: {payment_response}")
               # Raise a more specific exception or return a structured error object
               raise Exception(f"Mercado Pago payment failed: {error_response.get('message')}")

        except exceptions.ApiError as e:
           current_app.logger.error(f"Mercado Pago API error during payment processing: {e}. Status code: {e.status_code}. Response: {e.body}")
           # Re-raise the specific API error for upstream handling
           raise
        except Exception as e:
           current_app.logger.error(f"An unexpected error occurred during Mercado Pago payment processing: {e}")
           raise

    def handle_webhook(self, webhook_data: dict):
        """
        Handle incoming webhooks from Mercado Pago.
        This method should verify the webhook, fetch the full resource, and process the notification.
        """
        current_app.logger.info("Handling Mercado Pago webhook via PaymentService (SDK)")

        # TODO: Implement webhook signature verification for security.
        # The request data and signature header should be verified against a secret key.
        # Example (requires access to request object and webhook secret config):
        # from flask import request
        # webhook_secret = current_app.config.get("MERCADO_PAGO_WEBHOOK_SECRET")
        # signature = request.headers.get('X-Signature')
        # if not self.verify_webhook_signature(request.data, signature, webhook_secret):
        #    current_app.logger.warning("Webhook signature verification failed.")
        #    # Depending on policy, return 400 or 403
        #    return {"status": "error", "message": "Invalid signature"}, 400


        try:
            topic = webhook_data.get('topic')
            resource_id = webhook_data.get('id') # Or 'data.id' depending on webhook version and configuration

            if not topic or not resource_id:
                current_app.logger.warning(f"Received webhook with missing topic or ID: {webhook_data}")
                return {"status": "ignored", "message": "Missing topic or resource ID"}, 400 # Bad Request

            current_app.logger.info(f"Received webhook for topic: {topic}, resource ID: {resource_id}")

            # Fetch the full resource details from Mercado Pago based on the topic
            resource_info = None
            if topic == 'payment':
                # Fetch the full payment details
                # The SDK get method returns a dictionary with 'status' and 'response'
                payment_details_response = self.mercadopago_client.payment.get(resource_id)
                if payment_details_response and payment_details_response["status"] == 200:
                    resource_info = payment_details_response["response"]
                    current_app.logger.info(f"Fetched payment details for ID {resource_id}. Status: {resource_info.get('status')}")

                    # TODO: Process payment status update in local Pagamento model
                    # Find the local Pagamento record using the Mercado Pago ID
                    # Update its status, date of status change, and other relevant fields
                    # Consider different statuses: approved, rejected, in_process, cancelled, refunded, charged_back, etc.
                    # Handle cases like first notification, retries, etc.
                    # Example:
                    # local_pagamento = Pagamento.query.filter_by(mp_id=resource_id).first()
                    # if local_pagamento:
                    #     local_pagamento.status = resource_info.get('status')
                    #     # Update other fields as needed
                    #     db.session.add(local_pagamento)
                    #     db.session.commit()
                    #     current_app.logger.info(f"Updated local Pagamento record for MP ID {resource_id} to status: {resource_info.get('status')}")
                    # else:
                    #     current_app.logger.warning(f"Local Pagamento record not found for MP ID: {resource_id}. Consider logging or creating a new record?")

                else:
                    current_app.logger.warning(f"Failed to fetch payment details for webhook ID {resource_id}: {payment_details_response}")
                    # Return an error status to indicate processing failed, MP might retry
                    return {"status": "error", "message": "Failed to fetch payment details"}, 500 # Internal Server Error


            elif topic == 'subscription_preapproval': # Older subscription model topic
                 # Fetch preapproval details
                 # preapproval_details_response = self.mercadopago_client.preapproval.get(resource_id)
                 # if preapproval_details_response and preapproval_details_response["status"] == 200:
                 #     resource_info = preapproval_details_response["response"]
                 #     current_app.logger.info(f"Fetched preapproval details for ID {resource_id}. Status: {resource_info.get('status')}")
                 #     # TODO: Process preapproval status update in local Assinatura model
                 # else:
                 #    current_app.logger.warning(f"Failed to fetch preapproval details for webhook ID {resource_id}: {preapproval_details_response}")
                 #    return {"status": "error", "message": "Failed to fetch preapproval details"}, 500

                 current_app.logger.warning(f"Older subscription (preapproval) webhook received for ID {resource_id}. Processing logic not fully implemented.")
                 # Acknowledge receipt but indicate not fully processed
                 return {"status": "acknowledged", "message": "Older subscription webhook received, processing not fully implemented."}, 200


            elif topic == 'plan': # Newer subscription model topic
                 # Handle plan-related webhooks if needed (e.g., creation, update)
                 current_app.logger.info(f"Plan webhook received for ID {resource_id}. Processing logic not fully implemented.")
                 return {"status": "acknowledged", "message": "Plan webhook received, processing not fully implemented."}, 200

            elif topic == 'subscription': # Newer subscription model topic
                 # Handle subscription-related webhooks (e.g., creation, update, cancellation, payment failure)
                 # subscription_details_response = self.mercadopago_client.subscription.get(resource_id) # Assumes SDK has a subscription.get
                 # if subscription_details_response and subscription_details_response["status"] == 200:
                 #      resource_info = subscription_details_response["response"]
                 #      current_app.logger.info(f"Fetched subscription details for ID {resource_id}. Status: {resource_info.get('status')}")
                 #      # TODO: Process subscription status update in local Assinatura model
                 # else:
                 #     current_app.logger.warning(f"Failed to fetch subscription details for webhook ID {resource_id}: {subscription_details_response}")
                 #     return {"status": "error", "message": "Failed to fetch subscription details"}, 500

                 current_app.logger.warning(f"Newer subscription webhook received for ID {resource_id}. Processing logic not fully implemented.")
                 return {"status": "acknowledged", "message": "Newer subscription webhook received, processing not fully implemented."}, 200

            else:
                current_app.logger.warning(f"Unhandled Mercado Pago webhook topic: {topic}")
                # Acknowledge receipt but indicate topic was ignored
                return {"status": "ignored", "message": f"Unhandled topic: {topic}"}, 200 # Acknowledge with OK


            # If resource_info was successfully fetched and processed
            if resource_info:
                 # TODO: Commit DB session if local models were updated
                 # db.session.commit()
                 return {"status": "success", "message": f"Webhook for {topic} ID {resource_id} processed successfully."}, 200
            else:
                 # This case should ideally be handled by the specific topic blocks returning errors
                 current_app.logger.warning(f"Webhook for {topic} ID {resource_id} processed but no resource info returned or processed.")
                 return {"status": "ignored", "message": f"Webhook processed, but no action taken for {topic} ID {resource_id}."}, 200


        except exceptions.ApiError as e:
           current_app.logger.error(f"Mercado Pago API error during webhook handling for ID {resource_id}: {e}. Status: {e.status_code}. Response: {e.body}")
           # Return an error status to indicate processing failed
           # Depending on MP's retry policy, you might want to return 500
           return {"status": "error", "message": f"Mercado Pago API error: {e.body}"}, 500
        except Exception as e:
           current_app.logger.error(f"An unexpected error occurred during Mercado Pago webhook handling for ID {resource_id}: {e}")
           # Return an error status to indicate processing failed
           return {"status": "error", "message": f"Unexpected error: {e}"}, 500

    # TODO: Add a method for webhook signature verification
    # def verify_webhook_signature(self, data, signature_header, secret):
    #     """
    #     Verifies the Mercado Pago webhook signature.
    #     Requires calculating the expected signature and comparing it to the header.
    #     Refer to Mercado Pago documentation for signature verification details.
    #     """
    #     # Implementation involves HMAC-SHA256 and comparing timestamps/signatures
    #     current_app.logger.warning("Webhook signature verification method not implemented.")
    #     return True # Placeholder - MUST IMPLEMENT THIS FOR SECURITY


    def create_subscription(self, subscription_data: dict):
        """
        Create a new subscription in Mercado Pago using the SDK.
        subscription_data should contain plan_id or product/price details, payer info, etc.
        The structure must match Mercado Pago SDK's requirements for subscription creation.
        """
        current_app.logger.info("Creating subscription via PaymentService (Mercado Pago SDK)")
        # Ensure tenant_id is available in the context or passed in subscription_data
        # tenant_id = subscription_data.get('tenant_id') # Example: Pass tenant_id in data

        try:
            # Create the subscription using the Mercado Pago SDK
            # Refer to Mercado Pago documentation for the required subscription_data structure (e.g., for /v1/subscriptions)
            subscription_response = self.mercadopago_client.subscription.create(subscription_data)

            if subscription_response and subscription_response["status"] in [200, 201]: # Success status codes
                mp_subscription_data = subscription_response["response"]
                current_app.logger.info(f"Mercado Pago subscription created successfully. MP Subscription ID: {mp_subscription_data.get('id')}")

                # TODO: Save subscription details to a local Assinatura model
                # Ensure Assinatura model has fields for Mercado Pago ID, status, start date,
                # plan details, tenant_id, and links to the relevant tenant/user.
                # try:
                #     new_assinatura = Assinatura(
                #         mp_id=mp_subscription_data.get('id'),
                #         status=mp_subscription_data.get('status'),
                #         data_inicio=datetime.fromisoformat(mp_subscription_data.get('start_date').replace('Z', '+00:00')) if mp_subscription_data.get('start_date') else datetime.utcnow(),
                #         tenant_id=tenant_id, # Get tenant_id from context or data
                #         # Link to Plan details if stored locally
                #         # plan_id=...,
                #         raw_response=mp_subscription_data # Optionally store the full response
                #     )
                #     db.session.add(new_assinatura)
                #     db.session.commit()
                #     current_app.logger.info(f"Local Assinatura record created for MP ID: {mp_subscription_data.get('id')}")
                # except Exception as db_error:
                #     current_app.logger.error(f"Failed to save local subscription record for MP ID {mp_subscription_data.get('id')}: {db_error}")
                #     # Decide how to handle DB save failure after successful MP subscription (log, alert, compensate)
                #     # db.session.rollback()

                # Return the Mercado Pago subscription response data
                return mp_subscription_data
            else:
                 # Handle errors from the SDK response
                 error_response = subscription_response.get("response", {"message": "Unknown error from Mercado Pago SDK"})
                 current_app.logger.error(f"Mercado Pago SDK subscription creation error: {subscription_response}")
                 raise Exception(f"Mercado Pago subscription creation failed: {error_response.get('message')}")


        except exceptions.ApiError as e:
           current_app.logger.error(f"Mercado Pago API error during subscription creation: {e}. Status: {e.status_code}. Response: {e.body}")
           raise
        except Exception as e:
           current_app.logger.error(f"An unexpected error occurred during Mercado Pago subscription creation: {e}")
           raise

    def cancel_subscription(self, subscription_id: str):
        """
        Cancel an existing subscription in Mercado Pago using the SDK or direct API call.
        subscription_id is the ID provided by Mercado Pago.
        """
        current_app.logger.info(f"Canceling subscription {subscription_id} via PaymentService")
        try:
            # Using a direct API call example as SDK might not have a dedicated cancel method,
            # or cancellation is done by updating the status to 'cancelled'.
            # Refer to Mercado Pago API documentation for the exact cancellation method/endpoint.
            headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
            # Example: PUT /v1/subscriptions/{id} with status cancelled
            cancel_url = f"{self.base_url}/v1/subscriptions/{subscription_id}"
            response = requests.put(cancel_url, json={"status": "cancelled"}, headers=headers)


            if response.status_code in [200, 204]: # OK or No Content
                current_app.logger.info(f"Subscription {subscription_id} canceled successfully in Mercado Pago.")
                # TODO: Update the status of the local Assinatura model to 'cancelled'
                # Find the local Assinatura record using the Mercado Pago ID
                # local_assinatura = Assinatura.query.filter_by(mp_id=subscription_id).first()
                # if local_assinatura:
                #     local_assinatura.status = 'cancelled' # Or match the status returned by MP if available
                #     local_assinatura.data_fim = datetime.utcnow() # Set end date if applicable
                #     db.session.add(local_assinatura)
                #     db.session.commit()
                #     current_app.logger.info(f"Updated local Assinatura record for MP ID {subscription_id} to cancelled.")
                # else:
                #     current_app.logger.warning(f"Local Assinatura record not found for MP ID: {subscription_id}. Cannot update local status.")

                # Depending on the response, you might return data or just status
                return True
            else:
                 current_app.logger.error(f"Mercado Pago subscription cancellation error for {subscription_id}: Status code: {response.status_code}. Response: {response.text}")
                 raise Exception(f"Mercado Pago subscription cancellation failed for {subscription_id}: {response.text}")

        except Exception as e:
           current_app.logger.error(f"An unexpected error occurred during Mercado Pago subscription cancellation {subscription_id}: {e}")
           raise


    def refund_payment(self, payment_id: str, amount: float = None):
        """
        Refund a payment in Mercado Pago using the SDK.
        payment_id is the ID provided by Mercado Pago.
        amount is optional for partial refunds (if None, it's a full refund).
        """
        current_app.logger.info(f"Refunding payment {payment_id} via PaymentService (Mercado Pago SDK)")
        try:
            # Create a refund using the Mercado Pago SDK
            # The refund_data can be empty for full refunds or contain 'amount' for partial refunds.
            refund_data = {}
            if amount is not None:
                refund_data["amount"] = amount

            # The SDK method returns a dictionary with 'status' and 'response'
            refund_response = self.mercadopago_client.refund.create(payment_id, refund_data)


            if refund_response and refund_response["status"] in [200, 201]: # Success status codes
                 mp_refund_data = refund_response["response"]
                 current_app.logger.info(f"Refund processed successfully for payment {payment_id}.")
                 # TODO: Record the refund details in a local model (e.g., related to Pagamento)
                 # This might involve creating a new Refund record or updating the original Pagamento status/details.
                 # Ensure the refund record is linked to the original Pagamento and includes tenant_id.
                 # Example:
                 # original_pagamento = Pagamento.query.filter_by(mp_id=payment_id).first()
                 # if original_pagamento:
                 #    # Create a Refund record associated with original_pagamento
                 #    new_refund = Refund(
                 #        mp_id=mp_refund_data.get('id'),
                 #        amount=mp_refund_data.get('amount'),
                 #        data_criacao=datetime.fromisoformat(mp_refund_data.get('date_created').replace('Z', '+00:00')) if mp_refund_data.get('date_created') else datetime.utcnow(),
                 #        pagamento_id=original_pagamento.id,
                 #        tenant_id=original_pagamento.tenant_id, # Inherit tenant_id from payment
                 #        raw_response=mp_refund_data
                 #    )
                 #    db.session.add(new_refund)
                 #    # You might also update the original payment's status if it's a full refund
                 #    # if amount is None or amount == original_pagamento.amount:
                 #    #    original_pagamento.status = 'refunded'
                 #    #    db.session.add(original_pagamento)
                 #    db.session.commit()
                 #    current_app.logger.info(f"Local Refund record created for MP Refund ID: {mp_refund_data.get('id')}")
                 # else:
                 #     current_app.logger.warning(f"Original Pagamento record not found for MP ID: {payment_id}. Cannot link refund.")


                 # Return the Mercado Pago refund response data
                 return mp_refund_data
            else:
                 # Handle errors from the SDK response
                 error_response = refund_response.get("response", {"message": "Unknown error from Mercado Pago SDK"})
                 current_app.logger.error(f"Mercado Pago SDK refund error for payment {payment_id}: {refund_response}")
                 raise Exception(f"Mercado Pago refund failed for payment {payment_id}: {error_response.get('message')}")

        except exceptions.ApiError as e:
           current_app.logger.error(f"Mercado Pago API error during payment refund {payment_id}: {e}. Status: {e.status_code}. Response: {e.body}")
           raise
        except Exception as e:
           current_app.logger.error(f"An unexpected error occurred during payment refund {payment_id}: {e}")
           raise

    # General comment on Tenant Context:
    # When interacting with local models (Pagamento, Assinatura, Venda, etc.) within this service,
    # it is crucial to ensure the tenant_id is correctly associated with the new records
    # and used for filtering when querying existing records. The tenant_id should be
    # passed into the service methods from the resource or a higher layer that has
    # access to the current tenant context (e.g., from JWT or the tenant middleware).
    # Example: process_payment(self, tenant_id: int, payment_data: dict):
    # This ensures data isolation for each tenant.