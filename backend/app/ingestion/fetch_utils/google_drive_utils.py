import io
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from app.config import SCOPES, SERVICE_ACCOUNT_FILE_PATH
from app.utils import setup_logger
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

logger = setup_logger()


def extract_file_id(gdrive_url: str) -> str:
    if "id=" in gdrive_url:
        file_id = gdrive_url.split("id=")[1].split("&")[0]
        if file_id:
            return file_id
        else:
            raise ValueError(
                "Invalid Google Drive URL format: missing file ID after 'id='."
            )
    else:
        parts = gdrive_url.strip("/").split("/")
        if "d" in parts:
            d_index = parts.index("d")
            try:
                file_id = parts[d_index + 1]
                if file_id:
                    return file_id
                else:
                    raise ValueError(
                        "Invalid Google Drive URL format: missing file ID after '/d/'."
                    )
            except IndexError as e:
                raise ValueError(
                    "Invalid Google Drive URL format: incomplete URL."
                ) from e
        else:
            raise ValueError(
                """URL format not recognized. Ensure it contains 'id=' or follows the
                standard Drive URL format."""
            )


def determine_file_type(file_name: str) -> str:
    _, ext = os.path.splitext(file_name.lower())
    if ext == ".pdf":
        return "pdf"
    elif ext == ".xlsx":
        return "xlsx"
    else:
        return "other"


def download_file(file_id: str) -> Optional[io.BytesIO]:
    """
    Download a file from Google Drive using the Drive API.
    """
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE_PATH, scopes=SCOPES
    )
    drive_service = build("drive", "v3", credentials=creds)
    try:
        request = drive_service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        if file_buffer.getbuffer().nbytes == 0:
            raise RuntimeError("No content was downloaded from the file.")
        file_buffer.seek(0)
        return file_buffer
    except Exception as e:
        logger.error(f"Error downloading file with ID '{file_id}': {e}")
        return None


def download_file_wrapper(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """A wrapper function to process each record and download its file."""
    try:
        fields = record.get("fields", {})
        gdrive_link = fields.get("Drive link")
        file_name = fields.get("File name")
        document_id = fields.get("ID")
        survey_name = fields.get("Survey name")
        description = fields.get("Description")

        if not gdrive_link or not file_name:
            logger.error("Record is missing 'Drive link' or 'File name'")
            return None

        # Check if the file is a PDF (we only want to process PDFs)
        file_type = determine_file_type(file_name)
        if file_type != "pdf":
            logger.info(f"Skipping non-PDF file: '{file_name}'")
            return None

        file_id = extract_file_id(gdrive_link)
        if not file_id:
            logger.error(f"Could not extract file ID from link '{gdrive_link}'")
            return None

        logger.info(f"Starting download of file '{file_name}'")
        file_buffer = download_file(file_id)
        if file_buffer is None:
            logger.error(f"Failed to download file '{file_name}'")
            return None

        logger.info(f"Completed download of file '{file_name}'")
        return {
            "file_name": file_name,
            "file_buffer": file_buffer,
            "file_type": file_type,
            "document_id": document_id,
            "survey_name": survey_name,
            "summary": description,
            "fields": fields,
        }
    except Exception as e:
        logger.error(f"Error downloading file '{file_name}': {e}")
        return None


def download_all_files(
    records: List[Dict[str, Any]], n_max_workers: int
) -> List[Dict[str, Any]]:
    """Download all files concurrently using ThreadPoolExecutor."""
    downloaded_files = []

    with ThreadPoolExecutor(max_workers=n_max_workers) as executor:
        # Map each record to a future
        future_to_record = {
            executor.submit(download_file_wrapper, record): record for record in records
        }

        for future in as_completed(future_to_record):
            record = future_to_record[future]
            file_name = record.get("fields", {}).get("File name", "Unknown")
            try:
                result = future.result()
                if result is not None:
                    downloaded_files.append(result)
            except Exception as e:
                logger.error(f"Error downloading file '{file_name}': {e}")

    return downloaded_files
