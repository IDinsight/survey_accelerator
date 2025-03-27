import asyncio
from typing import Any, BinaryIO, Dict

import PyPDF2
import tiktoken

from app.ingestion.process_utils.embedding_utils import create_embedding
from app.ingestion.process_utils.openai_utils import (
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
    try:
        pdf_reader = PyPDF2.PdfReader(file_buffer)
        chunks: list[str] = []
        num_pages = len(pdf_reader.pages)
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            if page_text and page_text.strip():
                chunks.append(page_text.strip())
        if not chunks:
            logger.warning("No text could be extracted from the uploaded PDF file.")
            return []
        return chunks
    except PyPDF2.errors.PdfReadError as e:
        logger.error(f"Error reading PDF file: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error parsing PDF file: {e}")
        return []


async def process_file(
    file_buffer: BinaryIO,
    file_name: str,
    file_type: str,
    metadata: Dict[str, Any],
) -> list[Dict[str, Any]]:
    """
    Process the file by parsing, generating summaries, and creating embeddings.
    Updates the progress bar after processing each page.

    The heavy computations are performed at the document level to improve efficiency.
    """
    if file_buffer is None:
        logger.warning(f"No file buffer provided for file '{file_name}'. Skipping.")
        return []

    # Parse the file asynchronously
    chunks = await parse_file(file_buffer, file_type)
    if not chunks:
        logger.warning(f"No text extracted from file '{file_name}'. Skipping.")
        return []

    # Combine all chunks into a single document_content
    document_content = "\n\n".join(chunks)

    # Initialize tiktoken encoder for the model you're using
    encoding = tiktoken.encoding_for_model("gpt-4")

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
    prompt_tokens = len(
        encoding.encode(prompt_template.format(document_content="", chunk_content=""))
    )

    # Tokenize document_content once
    document_tokens = encoding.encode(document_content)

    # Create metadata string once
    metadata_string = create_metadata_string(metadata)
    metadata_section = f"Information about this document:\n{metadata_string}\n\n"

    processed_pages: list[Dict[str, Any]] = []

    # Prepare tasks for contextual summaries
    contextual_summary_tasks = []
    for page_num, page_text in enumerate(chunks):
        # Tokenize the chunk content
        chunk_tokens = len(encoding.encode(page_text))

        # Calculate the available tokens for document_content
        available_tokens = MAX_CONTEXT_LENGTH - prompt_tokens - chunk_tokens

        if available_tokens <= 0:
            logger.warning(
                f"Chunk content on page {page_num + 1} is too long. Skipping."
            )
            contextual_summary_tasks.append(None)  # Placeholder for skipped page
            continue

        # Truncate document_content if necessary
        if len(document_tokens) > available_tokens:
            truncated_document_tokens = document_tokens[:available_tokens]
            truncated_document_content = encoding.decode(truncated_document_tokens)
        else:
            truncated_document_content = document_content

        # Create the task for generating contextual summary
        task = generate_contextual_summary(
            truncated_document_content,
            page_text,
        )
        contextual_summary_tasks.append(task)

    # Run contextual summary tasks concurrently
    chunk_summaries = await asyncio.gather(
        *[task for task in contextual_summary_tasks if task is not None],
        return_exceptions=True,
    )

    # Prepare tasks for embedding generation and QA extraction
    embedding_tasks = []

    summary_index = 0  # Index to keep track of successful summaries
    for page_num, page_text in enumerate(chunks):
        if contextual_summary_tasks[page_num] is None:
            # Skip pages that couldn't generate a summary
            continue

        chunk_summary = chunk_summaries[summary_index]
        summary_index += 1

        if not chunk_summary:
            logger.warning(
                f"Contextual summary generation failed for page {page_num + 1} "
                f"in file '{file_name}'. Skipping."
            )
            continue

        # Combine metadata, context summary, and chunk text
        contextualized_chunk = f"""METADATA: {metadata_section}
        CONTEXT: {chunk_summary}
        RAW TEXT: {page_text}"""

        # Create the task for embedding generation
        embedding_task = asyncio.to_thread(create_embedding, contextualized_chunk)
        embedding_tasks.append((page_num, embedding_task))

        # Initialize processed page entry
        processed_pages.append(
            {
                "page_number": page_num + 1,
                "contextualized_chunk": contextualized_chunk,
                "chunk_summary": chunk_summary,
                # Embedding and QA pairs will be added later
            }
        )

    # Run embedding tasks concurrently
    embeddings_results = await asyncio.gather(
        *[task for _, task in embedding_tasks], return_exceptions=True
    )

    # Associate embeddings and QA pairs with processed pages
    for i, page in enumerate(processed_pages):
        page_num = page["page_number"] - 1  # Zero-based index

        # Handle embedding
        embedding_result = embeddings_results[i]
        if isinstance(embedding_result, Exception) or embedding_result is None:
            logger.warning(
                f"Embedding generation failed for page {page_num + 1} in "
                f"file '{file_name}'. Skipping embedding."
            )
            page["embedding"] = None
        else:
            page["embedding"] = embedding_result

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
