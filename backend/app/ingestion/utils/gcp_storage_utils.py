# utils/gcp_storage_utils.py

import io

from google.cloud import storage

from app.utils import setup_logger

logger = setup_logger()


def upload_file_buffer_to_gcp_bucket(
    file_buffer: io.BytesIO, bucket_name: str, destination_blob_name: str
) -> str:
    """
    Uploads a file from an in-memory file buffer to the GCP bucket and returns
    the public URL.

    Args:
        file_buffer: In-memory file-like object (io.BytesIO).
        bucket_name: Name of the GCP bucket.
        destination_blob_name: Destination name in the bucket.

    Returns:
        Public URL of the uploaded file.
    """
    try:
        # Initialize a client
        storage_client = storage.Client()

        # Get the bucket
        bucket = storage_client.bucket(bucket_name)

        # Create a blob object
        blob = bucket.blob(destination_blob_name)

        # Upload the file to GCP bucket
        blob.upload_from_file(file_buffer, rewind=True)

        # Get the public URL
        public_url = blob.public_url

        return public_url

    except Exception as e:
        logger.error(f"Error uploading file to GCP bucket: {e}")
        return ""
