from app import db
from app.models.tenant import Tenant
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from typing import Dict

class TenantService:
    def create_new_tenant(self, tenant_data):
        """
        Creates a new tenant record in the public schema and attempts to create the tenant's database schema.
        """
        try:
            new_tenant = Tenant(**tenant_data)
            db.session.add(new_tenant)
            db.session.commit() # Commit to get the tenant ID and schema_name before schema creation

            # Attempt to create the database schema for the new tenant
            # Replace the placeholder with actual schema creation logic
            db.engine.execute(text(f"CREATE SCHEMA IF NOT EXISTS {new_tenant.schema_name}"))

            # Note: After creating the schema, you might need to apply migrations
            # to the new schema to set up the tables for this tenant.
            # This is a separate step, often handled by Alembic or a custom script
            # after schema creation.

            return new_tenant

        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error creating tenant: {e}") # Log the error
            raise # Re-raise the exception
        except Exception as e:
            db.session.rollback() # Ensure rollback on other errors too
            print(f"An unexpected error occurred creating tenant: {e}") # Log the error
            raise # Re-raise the exception

    def get_tenant_info(self, tenant_id):
        """
        Retrieves tenant information by ID from the public schema.
        """
        try:
            # Querying the Tenant model implicitly queries the public schema
            tenant = Tenant.query.get(tenant_id)
            return tenant
        except SQLAlchemyError as e:
            print(f"Database error getting tenant info: {e}") # Log the error
            raise # Re-raise the exception
        except Exception as e:
            print(f"An unexpected error occurred getting tenant info: {e}") # Log the error
            raise # Re-raise the exception

    def assign_subscription_plan(self, tenant_id: int, plan_id: int):
        """
        Assigns a subscription plan to a tenant.

        This method should link the Tenant to a Subscription/Plan model
        and potentially update the tenant's resource limits based on the assigned plan.
        """
        # Placeholder for assigning a plan
        print(f"Assigning plan {plan_id} to tenant {tenant_id}")
        # Example: Fetch tenant and plan, link them, update limits
        # tenant = self.get_tenant_info(tenant_id)
        # plan = Plan.query.get(plan_id) # Assuming Plan model exists
        # if tenant and plan:
        #     tenant.plan_id = plan.id
        #     tenant.update_limits_based_on_plan(plan) # Method on Tenant model or separate logic
        #     db.session.commit()
        pass

    def update_tenant_limits(self, tenant_id: int, limits_data: Dict):
        """
        Updates resource limits for a specific tenant.

        This method should update fields in the Tenant model or a related TenantLimits model.
        """
        # Placeholder for updating tenant limits
        print(f"Updating limits for tenant {tenant_id} with data: {limits_data}")
        # Example: Fetch tenant, update limit fields
        # tenant = self.get_tenant_info(tenant_id)
        # if tenant:
        #     tenant.max_animals = limits_data.get('max_animals', tenant.max_animals)
        #     tenant.max_users = limits_data.get('max_users', tenant.max_users)
        #     # ... update other limits
        #     db.session.commit()
        pass

    def check_tenant_resource_limit(self, tenant_id: int, resource_type: str) -> bool:
        """
        Checks if a tenant has exceeded a specific resource limit.

        This method should query the Tenant model or a TenantLimits model
        and compare current usage of the resource against the defined limit.
        Returns True if the limit is exceeded, False otherwise.
        """
        # Placeholder for checking resource limit
        print(f"Checking limit for resource '{resource_type}' for tenant {tenant_id}")
        # Example: Fetch tenant, get limit for resource_type, get current usage, compare
        # tenant = self.get_tenant_info(tenant_id)
        # if tenant:
        #     limit = getattr(tenant, f'max_{resource_type}', None) # Get limit based on resource_type string
        #     current_usage = self.get_current_resource_usage(tenant_id, resource_type) # Helper method needed
        #     if limit is not None and current_usage > limit:
        #         return True # Limit exceeded
        # return False # Limit not exceeded (or no limit defined)

        return False # Placeholder return: Assume limit is not exceeded for now
