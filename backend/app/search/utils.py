# app/search/utils.py

import os
from collections import OrderedDict
from typing import List, Tuple

import cohere
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.models import DocumentDB
from app.search.schemas import DocumentMetadata, RerankedDocument
from app.utils import setup_logger

logger = setup_logger()

# Initialize Cohere client
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
if not COHERE_API_KEY:
    logger.error(
        "Cohere API key not found. Please set the COHERE_API_KEY environment variable."
    )
    raise EnvironmentError("Cohere API key not found.")

co = cohere.Client(COHERE_API_KEY)


async def embed_query(query: str) -> cohere.EmbedResponse:
    """
    Generate embedding for the given query using Cohere's embedding model.
    """
    try:
        response = co.embed(
            texts=[query],
            model="embed-english-v3.0",
            input_type="search_query",
        )
        return response
    except Exception as e:
        logger.error(f"Error embedding query: {e}")
        raise


async def perform_semantic_search(
    session: AsyncSession, embedding: List[float], top_k: int
) -> List[Tuple[DocumentDB, float]]:
    """
    Perform semantic search using pgvector to find similar document embeddings.
    Returns a list of tuples (DocumentDB, distance).
    """
    try:
        # Build the query using SQLAlchemy in descending order
        distance = DocumentDB.content_embedding.cosine_distance(embedding).label(
            "distance"
        )

        stmt = select(DocumentDB, distance).order_by(distance).limit(top_k)
        result = await session.execute(stmt)
        documents = result.fetchall()
        return documents  # Each item is a tuple (DocumentDB, distance)
    except Exception as e:
        logger.error(f"Error performing semantic search: {e}")
        raise


async def perform_keyword_search(
    session: AsyncSession, query_str: str, top_k: int
) -> List[Tuple[DocumentDB, float]]:
    """
    Perform keyword-based search using PostgreSQL's full-text search capabilities.
    Returns a list of tuples (DocumentDB, rank).
    """
    try:
        rank = func.ts_rank_cd(
            func.to_tsvector("english", DocumentDB.content_text),
            func.plainto_tsquery("english", query_str),
        ).label("rank")

        stmt = (
            select(DocumentDB, rank)
            .where(
                func.to_tsvector("english", DocumentDB.content_text).op("@@")(
                    func.plainto_tsquery("english", query_str)
                )
            )
            .order_by(rank.desc())
            .limit(top_k)
        )
        result = await session.execute(stmt)
        documents = result.fetchall()
        return documents  # Each item is a tuple (DocumentDB, rank)
    except Exception as e:
        logger.error(f"Error performing keyword search: {e}")
        raise


async def hybrid_search(
    session: AsyncSession, query_str: str, top_k: int
) -> List[RerankedDocument]:
    """
    Combine semantic and keyword search results, remove duplicates, and re-rank.
    """
    try:
        # Perform semantic search
        embedding_response = await embed_query(query_str)
        semantic_results = await perform_semantic_search(
            session, embedding_response.embeddings[0], top_k
        )
        # Perform keyword search
        keyword_results = await perform_keyword_search(session, query_str, top_k)

        # Combine results into an ordered dictionary to remove duplicates
        combined_results = OrderedDict()
        for doc, _ in semantic_results:
            if doc.id not in combined_results:
                combined_results[doc.id] = doc

        for doc, _ in keyword_results:
            if doc.id not in combined_results:
                combined_results[doc.id] = doc

        # Prepare documents and corresponding DocumentDB instances for re-ranking
        documents = []
        doc_list = []
        for doc in combined_results.values():
            documents.append(doc.content_text)
            doc_list.append(doc)

        # Use Cohere's rerank API
        rerank_response = co.rerank(
            model="rerank-english-v3.0",
            query=query_str,
            documents=documents,
            top_n=top_k,
            return_documents=False,
        )

        # Collect the reranked results
        reranked_results = []
        for rank, result in enumerate(rerank_response.results):
            index = result.index
            relevance_score = result.relevance_score
            doc = doc_list[index]

            # Create DocumentMetadata instance from the ORM object
            metadata = DocumentMetadata.from_orm(doc)

            # Create RerankedDocument instance
            reranked_document = RerankedDocument(
                metadata=metadata,
                content_text=doc.content_text,
                relevance_score=relevance_score,
                rank=rank + 1,
            )
            reranked_results.append(reranked_document)

        return reranked_results
    except Exception as e:
        logger.error(f"Error performing hybrid search: {e}")
        raise
