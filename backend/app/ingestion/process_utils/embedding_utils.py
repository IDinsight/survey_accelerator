# utils/embedding_utils.py

import asyncio
import io
from typing import Any, Dict, List

import cohere
from app.config import COHERE_API_KEY
from app.utils import setup_logger

logger = setup_logger()

cohere_client = cohere.Client(COHERE_API_KEY)

model = "embed-english-v3.0"


def create_embedding(text: str) -> list:
    """
    Create an embedding for the given text using Cohere.
    """
    try:
        response = cohere_client.embed(
            texts=[text],
            model=model,
            input_type="search_document",
            embedding_types=["float"],
        )

        embedding = response.embeddings.float
        return embedding[0]
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise e


async def process_files(
    metadata_list: List[Dict[str, Any]],
    semaphore: asyncio.Semaphore,
) -> List[Dict[str, Any]]:
    """
    Processes files concurrently and updates metadata with processed pages.
    """
    # Import here to avoid circular imports
    from app.ingestion.utils.file_processing_utils import process_file

    async def process(metadata):
        """
        Processes a single file and updates metadata with processed pages.
        """
        async with semaphore:
            file_name = metadata["file_name"]
            file_type = metadata.get(
                "file_type", "pdf"
            )  # Default to PDF if not specified
            fields = metadata.get("fields", {})
            file_buffer = metadata["file_buffer"]

            # Read the file content into bytes
            file_buffer.seek(0)
            file_bytes = file_buffer.read()

            # Create a new BytesIO object for processing
            processing_file_buffer = io.BytesIO(file_bytes)

            try:
                # Process the file asynchronously
                processed_pages = await process_file(
                    processing_file_buffer,
                    file_name,
                    file_type,
                    metadata=fields,
                )

                if not processed_pages:
                    logger.warning(
                        f"No processed pages for file '{file_name}'. Skipping."
                    )
                    return None
            except Exception as e:
                logger.error(f"Error processing file '{file_name}': {e}")
                return None

            metadata["processed_pages"] = processed_pages
            metadata["file_bytes"] = file_bytes
            return metadata

    tasks = [process(metadata) for metadata in metadata_list]
    results = await asyncio.gather(*tasks)
    return [res for res in results if res]
