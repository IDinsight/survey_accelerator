# utils/google_drive_utils.py

import io
import os
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import Resource as DriveResource
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from app.config import SCOPES, SERVICE_ACCOUNT_FILE_PATH, XLSX_SUBDIR
from app.utils import setup_logger

logger = setup_logger()


def get_drive_service() -> DriveResource:
    """
    Authenticate using a service account and return the Drive service.
    """
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE_PATH, scopes=SCOPES
    )
    drive_service = build("drive", "v3", credentials=creds)
    return drive_service


def extract_file_id(gdrive_url: str) -> str:
    """
    Extract the file ID from a Google Drive URL.

    Supports URLs of the form:
    - https://drive.google.com/file/d/FILE_ID/view?usp=sharing
    - https://drive.google.com/open?id=FILE_ID
    - Any URL containing 'id=FILE_ID'
    """
    if "id=" in gdrive_url:
        # URL contains 'id=FILE_ID'
        file_id = gdrive_url.split("id=")[1].split("&")[0]
        if file_id:
            return file_id
        else:
            raise ValueError(
                "Invalid Google Drive URL format: missing file ID after 'id='."
            )
    else:
        # Handle URLs of the form 'https://drive.google.com/file/d/FILE_ID/...'
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
                """URL format not recognized. Ensure it contains 'id=' or
                follows the standard Drive URL format."""
            )


def determine_file_type(file_name: str) -> str:
    """
    Determine the file type based on the file extension.
    """
    _, ext = os.path.splitext(file_name.lower())
    if ext == ".pdf":
        return "pdf"
    elif ext == ".xlsx":
        return "xlsx"
    else:
        return "other"


def download_file(
    file_id: str, file_name: str, file_type: str, drive_service: DriveResource
) -> Optional[io.BytesIO]:
    """
    Download a file from Google Drive using its file ID and handle it based on file type
    For PDFs, download into memory and return the BytesIO object.
    For XLSX, download and save to disk.
    """
    try:
        # Get file metadata to determine MIME type
        file_metadata = (
            drive_service.files().get(fileId=file_id, fields="mimeType, name").execute()
        )
        mime_type = file_metadata.get("mimeType")

        if (
            file_type == "xlsx"
            and mime_type == "application/vnd.google-apps.spreadsheet"
        ):
            # Export Google Sheets to Excel format
            request = drive_service.files().export_media(
                fileId=file_id,
                mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            save_path = os.path.join(
                XLSX_SUBDIR,
                (
                    f"{file_name}.xlsx"
                    if not file_name.lower().endswith(".xlsx")
                    else file_name
                ),
            )
            with open(save_path, "wb") as xlsx_file:
                downloader = MediaIoBaseDownload(xlsx_file, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            return None  # No need to return anything for XLSX
        elif file_type == "pdf":
            # Download PDF files into memory
            request = drive_service.files().get_media(fileId=file_id)
            pdf_buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(pdf_buffer, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            pdf_buffer.seek(0)  # Reset buffer position to the beginning
            return pdf_buffer  # Return the in-memory file for PDFs
        else:
            return None

    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return None
