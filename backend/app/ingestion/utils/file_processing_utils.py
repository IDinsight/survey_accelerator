# utils/file_processing_utils.py

import os
import io
import PyPDF2
import pandas as pd
from app.ingestion.utils.google_drive_utils import download_file, determine_file_type
from app.ingestion.utils.openai_utils import generate_contextual_summary
from app.ingestion.utils.embedding_utils import create_embedding
from app.config import XLSX_SUBDIR
from app.utils import setup_logger

logger = setup_logger()


def parse_file(file_buffer, file_type):
    """
    Parse the content of an uploaded file into chunks.
    For PDFs, each page is treated as its own chunk.
    For text files, the content is split into chunks of fixed size.
    """
    if file_type == "pdf":
        pdf_reader = PyPDF2.PdfReader(file_buffer)
        chunks = []
        num_pages = len(pdf_reader.pages)
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            if page_text and page_text.strip():
                chunks.append(page_text.strip())
        if not chunks:
            raise RuntimeError("No text could be extracted from the uploaded PDF file.")
    else:
        # Handle other file types if needed
        chunks = []
    return chunks


def process_file(file_buffer, file_name, file_type):
    """
    Process the file by parsing, generating summaries, and creating embeddings.
    """
    chunks = parse_file(file_buffer, file_type)
    if not chunks:
        logger.warning(f"No text extracted from file '{file_name}'. Skipping.")
        return []

    processed_pages = []
    for page_num, page_text in enumerate(chunks):
        # Generate contextual summary
        context = generate_contextual_summary(page_text, page_text)
        if not context:
            logger.warning(
                f"Contextual summary generation failed for page {page_num + 1} in file '{file_name}'. Skipping."
            )
            continue

        # Combine context with chunk text
        contextualized_chunk = f"{context}\n\n{page_text}"

        # Create embedding
        embedding = create_embedding(contextualized_chunk)
        if embedding is None:
            logger.warning(
                f"Embedding generation failed for page {page_num + 1} in file '{file_name}'. Skipping."
            )
            continue

        processed_pages.append(
            {
                "page_number": page_num + 1,
                "contextualized_chunk": contextualized_chunk,
                "embedding": embedding,
            }
        )
    return processed_pages


def open_sheet_in_pandas(file_path):
    """
    Open an Excel file in pandas and return the DataFrame.
    """
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        logger.error(f"Error opening Excel file: {e}")
        return None


def create_directories():
    """
    Create main and subdirectories for downloads if they don't exist.
    """
    os.makedirs(XLSX_SUBDIR, exist_ok=True)
