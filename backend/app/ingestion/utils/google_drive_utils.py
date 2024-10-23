# utils/google_drive_utils.py

import io
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from app.config import SCOPES, SERVICE_ACCOUNT_FILE, XLSX_SUBDIR
from app.utils import setup_logger

logger = setup_logger()


def get_drive_service():
    """
    Authenticate using a service account and return the Drive service.
    """
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    drive_service = build("drive", "v3", credentials=creds)
    return drive_service


def extract_file_id(gdrive_url):
    """
    Extract the file ID from a Google Drive URL.
    """
    try:
        if "id=" in gdrive_url:
            return gdrive_url.split("id=")[1].split("&")[0]
        else:
            # Handle URLs of the form https://drive.google.com/file/d/FILE_ID/view?usp=sharing
            parts = gdrive_url.split("/")
            if "d" in parts:
                d_index = parts.index("d")
                return parts[d_index + 1]
            else:
                raise ValueError(
                    "URL format not recognized. Ensure it contains 'id=' or follows the standard Drive URL format."
                )
    except (IndexError, ValueError):
        raise ValueError("Invalid Google Drive URL format.")


def determine_file_type(file_name):
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


def download_file(file_id, file_name, file_type, drive_service):
    """
    Download a file from Google Drive using its file ID and handle it based on file type.
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
            with io.FileIO(save_path, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            return None  # No need to return anything for XLSX
        elif file_type == "pdf":
            # Download PDF files into memory
            request = drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            fh.seek(0)  # Reset buffer position to the beginning
            return fh  # Return the in-memory file
        elif file_type == "xlsx":
            # Download existing .xlsx files that are not Google Sheets
            request = drive_service.files().get_media(fileId=file_id)
            save_path = os.path.join(XLSX_SUBDIR, file_name)
            with io.FileIO(save_path, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            return None  # No need to return anything for XLSX
        else:
            return None

    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return None
