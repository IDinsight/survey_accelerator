import asyncio
import os
from typing import List, Optional, Tuple

import cohere
from sqlalchemy import cast, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.models import DocumentDB
from app.search.openai_utils import (
    extract_highlight_keyphrase,
    generate_query_match_explanation,
)
from app.search.schemas import (
    DocumentMetadata,
    DocumentSearchResult,
    MatchedChunk,
)
from app.utils import setup_logger

logger = setup_logger()

INITIAL_TOP_K = 40  # Higher initial value to account for potential merges
FINAL_TOP_RESULTS = 25  # Final results desired

# Initialize Cohere client
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
if not COHERE_API_KEY:
    logger.error(
        "Cohere API key not found. Please set the COHERE_API_KEY environment variable."
    )
    raise EnvironmentError("Cohere API key not found.")

co = cohere.Client(COHERE_API_KEY)


async def embed_query(query: str) -> cohere.EmbedResponse:
    """Embed the search query using Cohere."""
    try:
        response = co.embed(
            texts=[query],
            model="embed-english-v3.0",
            truncate="LEFT",
            input_type="search_query",
        )
        return response
    except Exception as e:
        logger.error(f"Error embedding query: {e}")
        raise


def create_metadata(doc: DocumentDB) -> DocumentMetadata:
    """
    Helper function to create metadata for a document.
    """
    return DocumentMetadata(
        id=doc.id,
        file_name=doc.file_name,
        title=doc.title,
        summary=doc.summary,
        pdf_url=doc.pdf_url,
        countries=doc.countries,
        organizations=doc.organizations,
        regions=doc.regions,
        year=doc.year,
    )


async def perform_semantic_search(
    session: AsyncSession,
    embedding: List[float],
    top_k: int,
    country: Optional[str] = None,
    organization: Optional[str] = None,
    region: Optional[str] = None,
) -> List[Tuple[DocumentDB, float]]:
    """Perform semantic search using cosine distance."""
    try:
        distance = DocumentDB.content_embedding.cosine_distance(embedding).label(
            "distance"
        )

        stmt = select(DocumentDB, distance)
        if country:
            stmt = stmt.where(
                DocumentDB.countries.op("@>")(cast(f'["{country}"]', JSONB))
            )
        if organization:
            stmt = stmt.where(
                DocumentDB.organizations.op("@>")(cast(f'["{organization}"]', JSONB))
            )
        if region:
            stmt = stmt.where(DocumentDB.regions.op("@>")(cast(f'["{region}"]', JSONB)))

        stmt = stmt.order_by(distance).limit(top_k)
        result = await session.execute(stmt)
        documents = result.fetchall()
        return documents
    except Exception as e:
        logger.error(f"Error performing semantic search: {e}")
        raise


async def perform_keyword_search(
    session: AsyncSession,
    query_str: str,
    top_k: int,
    country: Optional[str] = None,
    organization: Optional[str] = None,
    region: Optional[str] = None,
) -> List[Tuple[DocumentDB, float]]:
    """Perform keyword search using ts_rank_cd."""
    try:
        rank = func.ts_rank_cd(
            func.to_tsvector("english", DocumentDB.contextualized_chunk),
            func.plainto_tsquery("english", query_str),
        ).label("rank")

        stmt = select(DocumentDB, rank).where(
            func.to_tsvector("english", DocumentDB.contextualized_chunk).op("@@")(
                func.plainto_tsquery("english", query_str)
            )
        )
        if country:
            stmt = stmt.where(
                DocumentDB.countries.op("@>")(cast(f'["{country}"]', JSONB))
            )
        if organization:
            stmt = stmt.where(
                DocumentDB.organizations.op("@>")(cast(f'["{organization}"]', JSONB))
            )
        if region:
            stmt = stmt.where(DocumentDB.regions.op("@>")(cast(f'["{region}"]', JSONB)))

        stmt = stmt.order_by(rank.desc()).limit(top_k)
        result = await session.execute(stmt)
        documents = result.fetchall()
        return documents
    except Exception as e:
        logger.error(f"Error performing keyword search: {e}")
        raise


async def hybrid_search(
    session: AsyncSession,
    query_str: str,
    country: Optional[str] = None,
    organization: Optional[str] = None,
    region: Optional[str] = None,
) -> List[DocumentSearchResult]:
    """
    Hybrid search combining semantic and keyword search with reranking.

    Args:
        session: Database session
        query_str: Search query string
        country: Optional filter by country
        organization: Optional filter by organization
        region: Optional filter by region

    Returns:
        List of DocumentSearchResult objects
    """
    try:
        # Embed the query
        embedding_response = await embed_query(query_str)

        # Perform semantic and keyword searches with the higher `INITIAL_TOP_K`
        semantic_results = await perform_semantic_search(
            session,
            embedding_response.embeddings[0],
            INITIAL_TOP_K,
            country=country,
            organization=organization,
            region=region,
        )

        keyword_results = await perform_keyword_search(
            session,
            query_str,
            INITIAL_TOP_K,
            country=country,
            organization=organization,
            region=region,
        )

        # Combine results and remove duplicates
        combined_results = semantic_results + keyword_results
        unique_matches = {
            (doc.id, doc.page_number): (doc, score) for doc, score in combined_results
        }
        combined_results = list(unique_matches.values())

        # Collect texts and match info for reranking
        texts = []
        match_info = []


        for doc, _score in combined_results:
            text = doc.contextualized_chunk
            texts.append(text)
            match_info.append(
                {
                    "doc": doc,
                    "page_number": doc.page_number,
                }
            )

        if not texts:
            return []

        # Rerank using Cohere
        rerank_response = co.rerank(
            model="rerank-english-v3.0",
            query=query_str,
            documents=texts,
            top_n=None,
            return_documents=False,
        )

        # Collect reranked matches
        reranked_matches = []
        for rank, result in enumerate(rerank_response.results):
            index = result.index
            info = match_info[index]
            doc = info["doc"]
            reranked_matches.append(
                {
                    "doc": doc,
                    "page_number": info["page_number"],
                    "rank": rank + 1,
                }
            )

        # Take top matches
        top_matches = reranked_matches[:FINAL_TOP_RESULTS]

        # Generate explanations and extract highlight keyphrases
        # Create tasks for both explanations and highlight keyphrases
        explanation_tasks = [
            generate_query_match_explanation(
                query_str, match["doc"].contextualized_chunk
            )
            for match in top_matches
        ]

        keyphrase_tasks = [
            extract_highlight_keyphrase(
                query_str, match["doc"].contextualized_chunk
            )
            for match in top_matches
        ]

        # Run all tasks concurrently for better performance
        all_results = await asyncio.gather(*explanation_tasks, *keyphrase_tasks)

        # Split the results - first half are explanations, second half are keyphrases
        explanations = all_results[: len(top_matches)]
        keyphrases = all_results[len(top_matches) :]

        # Group matches by document_id and build final results
        documents = {}
        for i, match in enumerate(top_matches):
            doc = match["doc"]
            document_id = doc.document_id
            if document_id not in documents:
                documents[document_id] = {
                    "doc": doc,
                    "matches": [],
                    "best_rank": match["rank"],
                }
            explanation = explanations[i]
            matched_chunk = MatchedChunk(
                page_number=match["page_number"],
                rank=match["rank"],
                explanation=explanation,
                # Use the extracted keyphrase for intelligent highlighting
                starting_keyphrase=(
                    keyphrases[i]
                    if keyphrases[i]
                    else (
                        doc.contextualized_chunk[:30]
                        if doc.contextualized_chunk
                        else ""
                    )
                ),
            )
            documents[document_id]["matches"].append(matched_chunk)

            if match["rank"] < documents[document_id]["best_rank"]:
                documents[document_id]["best_rank"] = match["rank"]

        # Sort documents by best_rank and create final search results
        sorted_documents = sorted(documents.values(), key=lambda x: x["best_rank"])
        final_results = [
            DocumentSearchResult(
                metadata=create_metadata(doc_entry["doc"]),
                matches=doc_entry["matches"],
                num_matches=len(doc_entry["matches"]),
            )
            for doc_entry in sorted_documents
        ]

        return final_results

    except Exception as e:
        logger.error(f"Error performing hybrid search: {e}")
        raise
