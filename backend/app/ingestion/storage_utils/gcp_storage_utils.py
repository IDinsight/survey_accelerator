import io

from app.config import SERVICE_ACCOUNT_FILE_PATH
from app.utils import setup_logger
from google.cloud import storage
from google.oauth2 import service_account

logger = setup_logger()


def upload_file_buffer_to_gcp_bucket(
    file_buffer: io.BytesIO, bucket_name: str, destination_blob_name: str
) -> str:
    """
    Uploads a file from an in-memory file buffer to the GCP bucket and returns
    the public URL with inline Content-Disposition.

    Args:
        file_buffer: In-memory file-like object (io.BytesIO).
        bucket_name: Name of the GCP bucket.
        destination_blob_name: Destination name in the bucket.

    Returns:
        Public URL of the uploaded file.
    """
    try:
        # Load service account credentials
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE_PATH
        )

        # Initialize the storage client with credentials
        storage_client = storage.Client(credentials=creds)

        # Get the bucket
        bucket = storage_client.bucket(bucket_name)

        # Create a blob object
        blob = bucket.blob(destination_blob_name)

        # Set metadata for inline viewing
        blob.content_disposition = "inline"
        blob.content_type = "application/pdf"

        # Upload the file to GCP bucket
        blob.upload_from_file(file_buffer, rewind=True)

        # Apply metadata update
        blob.patch()

        # Get the public URL
        public_url = blob.public_url

        return public_url

    except Exception as e:
        logger.error(f"Error uploading file to GCP bucket: {e}")
        return ""
