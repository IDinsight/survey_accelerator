# app/search/utils.py

import os
from collections import OrderedDict
from typing import List, Tuple

import cohere
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.models import DocumentDB
from app.search.schemas import (
    DocumentMetadata,
    DocumentSearchResult,
    MatchedChunk,
    MatchedQAPair,
)
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
    session: AsyncSession, embedding: list[float], top_k: int
) -> list[Tuple[DocumentDB, float]]:
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
) -> list[Tuple[DocumentDB, float]]:
    """
    Perform keyword-based search using PostgreSQL's full-text search capabilities.
    Returns a list of tuples (DocumentDB, rank).
    """
    try:
        rank = func.ts_rank_cd(
            func.to_tsvector("english", DocumentDB.contextualized_chunk),
            func.plainto_tsquery("english", query_str),
        ).label("rank")

        stmt = (
            select(DocumentDB, rank)
            .where(
                func.to_tsvector("english", DocumentDB.contextualized_chunk).op("@@")(
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
    session: AsyncSession, query_str: str, top_k: int, precision: bool = False
) -> List[DocumentSearchResult]:
    """
    Perform a hybrid search combining semantic and keyword search results.

    Groups matches by document, ranks documents by best match score, and includes
    multiple matches per document.

    Args:
        session: Async SQLAlchemy session.
        query_str: The search query string.
        top_k: The number of top results to return.
        precision: If True, performs precision search by re-ranking QA pairs.

    Returns:
        A list of DocumentSearchResult objects containing the documents and their
        matches.
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

        if not precision:
            # Regular search mode
            texts = []
            match_info = []
            for doc in combined_results.values():
                # Prepare text for re-ranking
                texts.append(doc.contextualized_chunk)
                match_info.append(
                    {
                        "doc": doc,
                        "chunk": doc.contextualized_chunk,
                        "page_number": doc.page_number,
                    }
                )

            # Use Cohere's rerank API
            rerank_response = co.rerank(
                model="rerank-english-v3.0",
                query=query_str,
                documents=texts,
                top_n=None,
                return_documents=False,
            )

            # Collect reranked matches
            matches = []
            for rank, result in enumerate(rerank_response.results):
                index = result.index
                relevance_score = result.relevance_score
                info = match_info[index]
                doc = info["doc"]
                matches.append(
                    {
                        "doc_id": doc.id,
                        "doc": doc,
                        "page_number": info["page_number"],
                        "chunk": info["chunk"],
                        "relevance_score": relevance_score,
                        "rank": rank + 1,
                    }
                )

            # Group matches by document
            documents = {}
            for match in matches:
                doc_id = match["doc_id"]
                if doc_id not in documents:
                    documents[doc_id] = {
                        "doc": match["doc"],
                        "matches": [],
                        "best_score": match["relevance_score"],
                    }
                documents[doc_id]["matches"].append(match)
                # Update best score if necessary
                if match["relevance_score"] > documents[doc_id]["best_score"]:
                    documents[doc_id]["best_score"] = match["relevance_score"]

            # Sort documents by best_score
            sorted_docs = sorted(
                documents.values(),
                key=lambda x: x["best_score"],
                reverse=True,
            )

            # Prepare the final results
            final_results = []
            for doc_entry in sorted_docs:
                doc = doc_entry["doc"]
                matches = doc_entry["matches"]
                # Sort matches by their rank
                matches.sort(key=lambda x: x["rank"])
                # Prepare MatchedChunk instances
                matched_chunks = [
                    MatchedChunk(
                        page_number=match["page_number"],
                        contextualized_chunk=match["chunk"],
                        relevance_score=match["relevance_score"],
                        rank=match["rank"],
                    )
                    for match in matches
                ]
                # Prepare DocumentMetadata
                metadata = DocumentMetadata.from_orm(doc)
                # Create DocumentSearchResult
                result = DocumentSearchResult(
                    metadata=metadata,
                    matches=matched_chunks,
                )
                final_results.append(result)

            return final_results

        else:
            # Precision mode
            texts = []
            match_info = []
            for doc in combined_results.values():
                # Ensure qa_pairs are loaded
                await session.refresh(doc, ["qa_pairs"])
                chunk_summary = doc.chunk_summary or ""
                for qa_pair in doc.qa_pairs:
                    text = f"""{chunk_summary} Question: {qa_pair.question}
                    Answer: {qa_pair.answer}"""
                    print(text)
                    texts.append(text)
                    match_info.append(
                        {
                            "doc": doc,
                            "qa_pair": qa_pair,
                            "page_number": doc.page_number,
                            "chunk_summary": chunk_summary,
                        }
                    )

            if not texts:
                return []

            # Use Cohere's rerank API
            rerank_response = co.rerank(
                model="rerank-english-v3.0",
                query=query_str,
                documents=texts,
                top_n=None,
                return_documents=False,
            )

            # Collect reranked matches
            matches = []
            for rank, result in enumerate(rerank_response.results):
                index = result.index
                relevance_score = result.relevance_score
                info = match_info[index]
                doc = info["doc"]
                qa_pair = info["qa_pair"]
                matches.append(
                    {
                        "doc_id": doc.id,
                        "doc": doc,
                        "qa_pair": qa_pair,
                        "page_number": info["page_number"],
                        "relevance_score": relevance_score,
                        "rank": rank + 1,
                    }
                )

            # Group matches by document
            documents = {}
            for match in matches:
                doc_id = match["doc_id"]
                if doc_id not in documents:
                    documents[doc_id] = {
                        "doc": match["doc"],
                        "matches": [],
                        "best_score": match["relevance_score"],
                    }
                documents[doc_id]["matches"].append(match)
                # Update best score if necessary
                if match["relevance_score"] > documents[doc_id]["best_score"]:
                    documents[doc_id]["best_score"] = match["relevance_score"]

            # Sort documents by best_score
            sorted_docs = sorted(
                documents.values(),
                key=lambda x: x["best_score"],
                reverse=True,
            )

            # Prepare the final results
            final_results = []
            for doc_entry in sorted_docs:
                doc = doc_entry["doc"]
                matches = doc_entry["matches"]
                # Sort matches by their rank
                matches.sort(key=lambda x: x["rank"])
                # Prepare MatchedQAPair instances
                matched_qas = [
                    MatchedQAPair(
                        page_number=match["page_number"],
                        question=match["qa_pair"].question,
                        answer=match["qa_pair"].answer,
                        relevance_score=match["relevance_score"],
                        rank=match["rank"],
                    )
                    for match in matches
                ]
                # Prepare DocumentMetadata
                metadata = DocumentMetadata.from_orm(doc)
                # Create DocumentSearchResult
                result = DocumentSearchResult(
                    metadata=metadata,
                    matches=matched_qas,
                )
                final_results.append(result)

            return final_results

    except Exception as e:
        logger.error(f"Error performing hybrid search: {e}")
        raise
