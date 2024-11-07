# utils/file_processing_utils.py

import asyncio
from typing import Any, BinaryIO, Dict

import PyPDF2
import tiktoken
import tqdm

from app.ingestion.utils.embedding_utils import create_embedding
from app.ingestion.utils.openai_utils import (
    extract_question_answer_from_page,
    generate_contextual_summary,
)
from app.utils import setup_logger

logger = setup_logger()


async def parse_file(file_buffer: BinaryIO, file_type: str) -> list[str]:
    """
    Parse the content of an uploaded file into chunks asynchronously.
    For PDFs, each page is treated as its own chunk.
    """
    if file_type == "pdf":
        # Run the parsing in a thread to avoid blocking the event loop
        chunks = await asyncio.to_thread(parse_pdf_file, file_buffer)
    else:
        # Handle other file types if needed
        chunks = []
    return chunks


def parse_pdf_file(file_buffer: BinaryIO) -> list[str]:
    """
    Synchronously parse a PDF file into a list of page texts.
    """
    pdf_reader = PyPDF2.PdfReader(file_buffer)
    chunks: list[str] = []
    num_pages = len(pdf_reader.pages)
    for page_num in range(num_pages):
        page = pdf_reader.pages[page_num]
        page_text = page.extract_text()
        if page_text and page_text.strip():
            chunks.append(page_text.strip())
    if not chunks:
        raise RuntimeError("No text could be extracted from the uploaded PDF file.")
    return chunks


async def process_file(
    file_buffer: BinaryIO,
    file_name: str,
    file_type: str,
    progress_bar: tqdm.tqdm,
    progress_lock: asyncio.Lock,
    metadata: Dict[str, Any],  # Pass metadata here
) -> list[Dict[str, Any]]:
    """
    Process the file by parsing, generating summaries, and creating embeddings.
    Updates the progress bar after processing each page.
    """
    # Ensure file_buffer is not None
    if file_buffer is None:
        logger.warning(f"No file buffer provided for file '{file_name}'. Skipping.")
        return []

    # Parse the file asynchronously
    chunks = await parse_file(file_buffer, file_type)
    if not chunks:
        logger.warning(f"No text extracted from file '{file_name}'. Skipping.")
        return []

    # Update the progress bar total with the number of pages
    async with progress_lock:
        progress_bar.total += len(chunks)
        progress_bar.refresh()

    # Combine all chunks into a single document_content
    document_content = "\n\n".join(chunks)

    # Initialize tiktoken encoder for the model you're using
    encoding = tiktoken.encoding_for_model("gpt-4")  # Adjust the model name if needed

    # Define model's max context length
    MAX_CONTEXT_LENGTH = 8192  # Adjust according to your model's context length

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

    # Create metadata string
    metadata_string = create_metadata_string(metadata)
    metadata_section = f"Information about this document:\n{metadata_string}\n\n"

    processed_pages: list[Dict[str, Any]] = []

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

        # Tokenize document_content
        document_tokens = encoding.encode(document_content)

        # Truncate document_content if necessary
        if len(document_tokens) > available_tokens:
            # Truncate document_content to fit available tokens
            truncated_document_tokens = document_tokens[:available_tokens]
            truncated_document_content = encoding.decode(truncated_document_tokens)
        else:
            truncated_document_content = document_content

        # Generate contextual summary asynchronously
        chunk_summary = await asyncio.to_thread(
            generate_contextual_summary, truncated_document_content, page_text
        )

        if not chunk_summary:
            logger.warning(
                f"""Contextual summary generation failed for page {page_num + 1}
                in file '{file_name}'. Skipping."""
            )
            continue

        # Combine metadata, context summary, and chunk text
        contextualized_chunk = f"{metadata_section}{chunk_summary}\n\n{page_text}"

        # Create embedding asynchronously
        embedding = await asyncio.to_thread(create_embedding, contextualized_chunk)

        if embedding is None:
            logger.warning(
                f"""Embedding generation failed for page {page_num + 1} in
                file '{file_name}'. Skipping."""
            )
            continue

        # Extract questions and answers
        extracted_question_answers = extract_question_answer_from_page(page_text)
        if not isinstance(extracted_question_answers, list):
            logger.error(
                f"""Extracted QA pairs on page {page_num + 1} is not a list.
                Skipping QA pairs for this page."""
            )
            extracted_question_answers = []

        processed_pages.append(
            {
                "page_number": page_num + 1,
                "contextualized_chunk": contextualized_chunk,
                "chunk_summary": chunk_summary,
                "embedding": embedding,
                "extracted_question_answers": extracted_question_answers,
            }
        )

        # Update progress bar after processing each page
        async with progress_lock:
            progress_bar.update(1)

    return processed_pages


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
