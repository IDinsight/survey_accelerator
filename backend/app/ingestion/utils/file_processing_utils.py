# utils/file_processing_utils.py

from typing import Any, BinaryIO, Dict, List, Optional

import pandas as pd
import PyPDF2
import tiktoken
from app.ingestion.utils.embedding_utils import create_embedding
from app.ingestion.utils.openai_utils import generate_contextual_summary
from app.utils import setup_logger

logger = setup_logger()


def parse_file(file_buffer: BinaryIO, file_type: str) -> List[str]:
    """
    Parse the content of an uploaded file into chunks.
    For PDFs, each page is treated as its own chunk.
    For other file types, handle accordingly.
    """
    if file_type == "pdf":
        pdf_reader = PyPDF2.PdfReader(file_buffer)
        chunks: List[str] = []
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


def process_file(
    file_buffer: BinaryIO, file_name: str, file_type: str
) -> List[Dict[str, Any]]:
    """
    Process the file by parsing, generating summaries, and creating embeddings.
    """
    # Ensure file_buffer is not None
    if file_buffer is None:
        logger.warning(f"No file buffer provided for file '{file_name}'. Skipping.")
        return []

    chunks = parse_file(file_buffer, file_type)
    if not chunks:
        logger.warning(f"No text extracted from file '{file_name}'. Skipping.")
        return []

    # Combine all chunks into a single document_content
    document_content = "\n\n".join(chunks)

    # Initialize tiktoken encoder for the model you're using
    encoding = tiktoken.encoding_for_model("gpt-4")  # Adjust the model name if needed

    # Define model's max context length
    MAX_CONTEXT_LENGTH = 128000  # For GPT-4o
    # Alternatively, if you're using a different model, adjust accordingly

    # Estimate the tokens used by the prompt template
    prompt_template = """
    <document>
    {document_content}
    </document>

    Here is the chunk we want to situate within the whole document
    <chunk>
    {chunk_content}
    </chunk>

    Please give a short succinct context to situate this chunk within the overall
    document which is a survey questionnaire for the purposes of improving search
    retrieval of the chunk.
    Answer only with the succinct context and nothing else.
    """

    # Tokenize the prompt template without variables
    prompt_tokens = len(
        encoding.encode(prompt_template.format(document_content="", chunk_content=""))
    )

    processed_pages: List[Dict[str, Any]] = []
    for page_num, page_text in enumerate(chunks):
        # Tokenize the chunk content
        chunk_tokens = len(encoding.encode(page_text))

        # Calculate the available tokens for document_content
        available_tokens = MAX_CONTEXT_LENGTH - prompt_tokens - chunk_tokens

        # Ensure available_tokens is positive
        if available_tokens <= 0:
            logger.warning(
                f"Chunk content on page {page_num + 1} is too long. Skipping."
            )
            continue

        # Truncate document_content if necessary
        document_tokens = encoding.encode(document_content)
        if len(document_tokens) > available_tokens:
            # Truncate document_content to fit available tokens
            truncated_document_tokens = document_tokens[:available_tokens]
            truncated_document_content = encoding.decode(truncated_document_tokens)
        else:
            truncated_document_content = document_content

        # Generate contextual summary
        context = generate_contextual_summary(truncated_document_content, page_text)
        if not context:
            logger.warning(
                f"""Contextual summary generation failed for page {page_num + 1} in
                file '{file_name}'. Skipping."""
            )
            continue

        # Combine context with chunk text
        contextualized_chunk = f"{context}\n\n{page_text}"

        # Create embedding
        embedding = create_embedding(contextualized_chunk)
        if embedding is None:
            logger.warning(
                f"""Embedding generation failed for page {page_num + 1} in
                file '{file_name}'. Skipping."""
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


def open_sheet_in_pandas(file_path: str) -> Optional[pd.DataFrame]:
    """
    Open an Excel file in pandas and return the DataFrame.
    """
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        logger.error(f"Error opening Excel file: {e}")
        return None


def create_metadata_string(metadata: Dict[str, Any]) -> str:
    """Pieces together metadata fields into a human-readable string."""
    year = metadata.get("Year", "an unknown year")
    countries = ", ".join(metadata.get("Countries", [])) or "unknown countries"
    regions = ", ".join(metadata.get("Region(s)", [])) or "unknown regions"
    organizations = (
        ", ".join(metadata.get("Organization(s)", [])) or "unknown organizations"
    )
    date_added = metadata.get("Date added", "an unknown date")
    notes = metadata.get("Notes", "No notes available")
    drive_link = metadata.get("Drive link", "No drive link available")

    metadata_string = (
        f"This document was made in {year}, relates to {countries}, "
        f"within the {regions} region and was created by {organizations}. "
        f"It was added to our system on {date_added}. Notes about it are: {notes}. "
        f"Drive link: {drive_link}."
    )
    return metadata_string