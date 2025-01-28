# utils/embedding_utils.py

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
