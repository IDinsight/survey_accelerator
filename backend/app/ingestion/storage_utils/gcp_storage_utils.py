import asyncio
import io
import os
from typing import Any, Dict, List

from ...utils import setup_logger

logger = setup_logger()

# Define the directory for locally saved files (e.g., "./uploaded_files")
LOCAL_UPLOAD_DIR = os.environ.get("LOCAL_UPLOAD_DIR", "./uploaded_files")
os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")


def save_file_buffer_to_local(
    file_buffer: io.BytesIO, file_name: str, content_type: str = "application/pdf"
) -> str:
    """
    Saves an in-memory file buffer to a local directory and returns the URL to access it.

    Args:
        file_buffer: In-memory file-like object (io.BytesIO).
        file_name: Name of the destination file.
        content_type: MIME type of the file (optional, for reference).

    Returns:
        URL string to access the locally saved file.
    """
    try:
        # Rewind the file buffer to ensure its start is reached.
        file_buffer.seek(0)

        # Compute the full path to write the file.
        local_path = os.path.join(LOCAL_UPLOAD_DIR, file_name)

        # Write the file content to the local path
        with open(local_path, "wb") as f:
            f.write(file_buffer.read())

        # Construct a URL for access.
        # Assuming you'll mount the local directory in your static file serving, e.g. "/uploaded_files"
        pdf_url = f"{BASE_URL}/uploaded_files/{file_name}"
        return pdf_url

    except Exception as e:
        logger.error(f"Error saving file locally: {e}")
        return ""


async def upload_files_to_local(
    metadata_list: List[Dict[str, Any]], semaphore: asyncio.Semaphore
) -> List[Dict[str, Any]]:
    """
    Saves files to local disk concurrently and updates metadata with the file URLs.
    """

    async def save_local(metadata):
        async with semaphore:
            file_name = metadata["file_name"]
            file_buffer = metadata["file_buffer"]

            # Ensure file buffer is rewound
            file_buffer.seek(0)

            # Save the file locally using the helper
            local_url = await asyncio.to_thread(
                save_file_buffer_to_local,
                file_buffer,
                file_name,
            )

            if not local_url:
                logger.error(f"Failed to save file '{file_name}' locally")
                return None

            metadata["pdf_url"] = local_url
            return metadata

    tasks = [save_local(metadata) for metadata in metadata_list]
    results = await asyncio.gather(*tasks)
    return [res for res in results if res]
