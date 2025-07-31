import dropbox
import os
import requests
from flask import current_app

# Assuming Dropbox API credentials are in Flask app config

class DropboxService:
    def __init__(self):
        # Initialize Dropbox client (will need to handle different auth flows later)
        # For now, assuming a long-lived access token is available in config
        self.dbx = dropbox.Dropbox(current_app.config.get('DROPBOX_ACCESS_TOKEN'))
        self.root_path = current_app.config.get('DROPBOX_ROOT_PATH', '')

    def upload_file(self, tenant_id: int, file_content, destination_path):
        """Upload a file to Dropbox for a specific tenant.
        destination_path should be relative to the tenant's root path.
        """
        # Ensure destination_path starts with a '/'
        if not destination_path.startswith('/'):
            destination_path = '/' + destination_path

        # Prepend tenant_id to the path
        tenant_path = f'/{tenant_id}' + destination_path
        full_path = self.root_path + tenant_path

        try:
            res = self.dbx.files_upload(file_content, full_path, mode=dropbox.files.WriteMode('overwrite'))
            # The response object contains metadata about the uploaded file
            return res
        except dropbox.exceptions.ApiError as e:
            current_app.logger.error(f"Error uploading file to Dropbox for tenant {tenant_id}: {e}")
            # Re-raise the exception after logging
            raise
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred during Dropbox upload for tenant {tenant_id}: {e}")
            raise

    def download_file(self, tenant_id: int, file_path):
        """Download a file from Dropbox for a specific tenant. file_path should be the full path within the tenant's folder."""
        # Prepend tenant_id to the path
        tenant_file_path = f'/{tenant_id}' + file_path
        full_path = self.root_path + tenant_file_path
        try:
            metadata, res = self.dbx.files_download(full_path)
            return res.content # Return the raw byte content of the file
        except dropbox.exceptions.ApiError as e:
            current_app.logger.error(f"Error downloading file from Dropbox for tenant {tenant_id}: {e}")
            # Re-raise the exception after logging
            raise
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred during Dropbox download for tenant {tenant_id}: {e}")
            raise

    def delete_file(self, tenant_id: int, file_path):
        """Delete a file from Dropbox for a specific tenant. file_path should be the full path within the tenant's folder."""
        # Prepend tenant_id to the path
        tenant_file_path = f'/{tenant_id}' + file_path
        full_path = self.root_path + tenant_file_path
        try:
            res = self.dbx.files_delete_v2(full_path)
            return res # Returns metadata of the deleted file
        except dropbox.exceptions.ApiError as e:
            current_app.logger.error(f"Error deleting file from Dropbox for tenant {tenant_id}: {e}")
            # Re-raise the exception after logging
            raise
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred during Dropbox deletion for tenant {tenant_id}: {e}")
            raise

    def get_shareable_link(self, tenant_id: int, file_path):
        """Get a shareable link for a file from Dropbox for a specific tenant. file_path should be the full path within the tenant's folder."""
        # Prepend tenant_id to the path
        tenant_file_path = f'/{tenant_id}' + file_path
        full_path = self.root_path + tenant_file_path
        try:
            # Check if a shared link already exists for this path
            try:
                links = self.dbx.sharing_list_shared_links(path=full_path, direct_only=True).links
                if links:
                    # If link exists, return it. Adjust for direct download if needed.
                    shareable_url = links[0].url
                    # shareable_url = shareable_url.replace('www.dropbox.com', 'dl.dropboxusercontent.com').replace('?dl=0', '?dl=1') # Example adjustment
                    return shareable_url
            except dropbox.exceptions.ApiError as e:
                # If list_shared_links raises an error other than 'path_not_found', handle it
                if not e.error.is_path() or not e.error.get_path().is_not_found():
                     raise # Re-raise unexpected API errors

            # If no link exists, create one
            link = self.dbx.sharing_create_shared_link_with_settings(full_path)
            shareable_url = link.url
            # shareable_url = shareable_url.replace('www.dropbox.com', 'dl.dropboxusercontent.com').replace('?dl=0', '?dl=1') # Example adjustment
            return shareable_url
        except dropbox.exceptions.ApiError as e:
            current_app.logger.error(f"Error getting shareable link from Dropbox for tenant {tenant_id}: {e}")
            raise
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred while getting Dropbox shareable link for tenant {tenant_id}: {e}")
            raise

# You would instantiate this service and use its methods in your resource or other service layers.
# Example:\
# dropbox_service = DropboxService()
# try:
#     # Assuming file_content is bytes and destination_path is like 'animals/fido/image.jpg'
#     uploaded_info = dropbox_service.upload_file(123, file_content, 'animals/fido/image.jpg') # Pass tenant_id
#     print(f"Uploaded file metadata: {uploaded_info}")
# except Exception as e:
#     print(f"Upload failed: {e}")

# You would instantiate this service and use its methods in your resource or other service layers.
# Example:
# dropbox_service = DropboxService()
# uploaded_info = dropbox_service.upload_file(123, file_data, '/path/in/dropbox/file.txt') # Pass tenant_id