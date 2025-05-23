import asyncio
import os
from typing import List, Tuple

import cohere
from sqlalchemy import ARRAY, Text, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.models import DocumentDB
from app.search.openai_utils import (
    extract_highlight_keyphrase,
    generate_query_match_explanation,
    rank_search_results,
)
from app.search.schemas import DocumentMetadata, DocumentSearchResult, MatchedChunk
from app.utils import setup_logger

logger = setup_logger()

INITIAL_TOP_K = 50

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
    organizations: List[str],
    survey_types: List[str],
) -> List[Tuple[DocumentDB, float]]:
    try:
        distance = DocumentDB.content_embedding.cosine_distance(embedding).label(
            "distance"
        )
        stmt = select(DocumentDB, distance)

        if organizations:
            stmt = stmt.where(
                DocumentDB.organizations.op("?|")(cast(organizations, ARRAY(Text)))
            )
        if survey_types:
            stmt = stmt.where(DocumentDB.survey_type.in_(survey_types))

        stmt = stmt.order_by(distance).limit(top_k)
        result = await session.execute(stmt)
        return result.fetchall()
    except Exception as e:
        logger.error(f"Error performing semantic search: {e}")
        raise


async def perform_keyword_search(
    session: AsyncSession,
    query_str: str,
    top_k: int,
    organizations: List[str],
    survey_types: List[str],
) -> List[Tuple[DocumentDB, float]]:
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
        if organizations:
            stmt = stmt.where(
                DocumentDB.organizations.op("?|")(cast(organizations, ARRAY(Text)))
            )
        if survey_types:
            stmt = stmt.where(DocumentDB.survey_type.in_(survey_types))
        stmt = stmt.order_by(rank.desc()).limit(top_k)
        result = await session.execute(stmt)
        return result.fetchall()
    except Exception as e:
        logger.error(f"Error performing keyword search: {e}")
        raise


async def hybrid_search(
    session: AsyncSession,
    query_str: str,
    max_results: int,
    organizations: List[str],
    survey_types: List[str],
) -> List[DocumentSearchResult]:
    """
    Hybrid search combining semantic and keyword search with reranking.

    Args:
        session: Database session.
        query_str: Search query string.
        max_results: Maximum number of results to return.
        organizations: Optional list of organization filters.
        survey_types: Optional list of survey type filters.

    Returns:
        List of DocumentSearchResult objects.
    """
    try:
        # Embed the query.
        embedding_response = await embed_query(query_str)

        # Perform semantic and keyword searches with the higher INITIAL_TOP_K.
        semantic_results = await perform_semantic_search(
            session,
            embedding_response.embeddings[0],
            top_k=INITIAL_TOP_K,
            organizations=organizations,
            survey_types=survey_types,
        )

        keyword_results = await perform_keyword_search(
            session,
            query_str,
            top_k=INITIAL_TOP_K,
            organizations=organizations,
            survey_types=survey_types,
        )

        # Combine results and remove duplicates based on (document_id, page_number).
        combined_results = semantic_results + keyword_results
        unique_matches = {
            (doc.document_id, doc.page_number): (doc, score)
            for doc, score in combined_results
        }
        combined_results = list(unique_matches.values())

        # Prepare documents for LLM-based reranking
        document_chunks = []
        for i, (doc, _score) in enumerate(combined_results):
            document_chunks.append(
                {"doc": doc, "page_number": doc.page_number, "index": i}  # Keep track of original index for later
            )

        if not document_chunks:
            return []

        # Use our new LLM-based reranker
        reranked_results = await rank_search_results(
            query=query_str, document_chunks=document_chunks
        )

        # Convert the reranked results to the expected format for further processing
        top_matches = []
        for ranked_item in reranked_results[:max_results]:
            match_result = {
                "doc": ranked_item["doc"],
                "page_number": ranked_item["page_number"],
                "rank": ranked_item["rank"],
                "strength": ranked_item["strength"],
                # Adding the new score fields to be available for the frontend
                "contextual_score": ranked_item["contextual_score"],
                "direct_match_score": ranked_item["direct_match_score"],
                "match_type": ranked_item["match_type"],
            }
            top_matches.append(match_result)

        # Generate explanations and extract highlight keyphrases concurrently.
        explanation_tasks = [
            generate_query_match_explanation(
                query_str, match["doc"].contextualized_chunk
            )
            for match in top_matches
        ]
        keyphrase_tasks = [
            extract_highlight_keyphrase(query_str, match["doc"].contextualized_chunk)
            for match in top_matches
        ]
        all_tasks = explanation_tasks + keyphrase_tasks
        all_results = await asyncio.gather(*all_tasks)
        explanations = all_results[: len(top_matches)]
        keyphrases = all_results[len(top_matches) :]

        # Group matches by document_id and count strength levels for sorting.
        documents_group = {}
        for i, match in enumerate(top_matches):
            doc = match["doc"]
            document_id = doc.document_id
            if document_id not in documents_group:
                documents_group[document_id] = {
                    "doc": doc,
                    "matches": [],
                    "strong_count": 0,
                    "moderate_count": 0,
                    "weak_count": 0,
                    "contextual_score_sum": 0,  # Track total contextual score
                    "direct_score_sum": 0,      # Track total direct match score
                    "contextual_matches": 0,    # Count of contextual matches
                    "direct_matches": 0,        # Count of direct matches
                    "balanced_matches": 0       # Count of balanced matches
                }
            # Count strengths.
            if match["strength"] == "Strong":
                documents_group[document_id]["strong_count"] += 1
            elif match["strength"] == "Moderate":
                documents_group[document_id]["moderate_count"] += 1
            else:
                documents_group[document_id]["weak_count"] += 1
                
            # Track match types and scores
            contextual_score = match.get("contextual_score", 5)
            direct_score = match.get("direct_match_score", 5)
            match_type = match.get("match_type", "balanced")
            
            documents_group[document_id]["contextual_score_sum"] += contextual_score
            documents_group[document_id]["direct_score_sum"] += direct_score
            
            if match_type == "contextual":
                documents_group[document_id]["contextual_matches"] += 1
            elif match_type == "direct":
                documents_group[document_id]["direct_matches"] += 1
            elif match_type == "balanced":
                documents_group[document_id]["balanced_matches"] += 1

            # Create a matched chunk with both traditional and new ranking information
            matched_chunk = MatchedChunk(
                page_number=match["page_number"],
                rank=match["rank"],
                explanation=explanations[i],
                starting_keyphrase=keyphrases[i] if keyphrases[i] else (
                    doc.contextualized_chunk[:30] if doc.contextualized_chunk else ""
                ),
                # Add the new detailed scoring data
                contextual_score=match.get("contextual_score", 5),
                direct_match_score=match.get("direct_match_score", 5),
                match_type=match.get("match_type", "balanced"),
            )
            documents_group[document_id]["matches"].append(matched_chunk)

        # Sort documents by score factors: strong count, average scores, moderate count
        sorted_documents = sorted(
            documents_group.values(),
            key=lambda d: (
                d["strong_count"], 
                (d["contextual_score_sum"] + d["direct_score_sum"]) / max(len(d["matches"]), 1),
                d["moderate_count"], 
                -d["weak_count"]
            ),
            reverse=True,
        )

        final_results = [
            DocumentSearchResult(
                metadata=create_metadata(doc_entry["doc"]),
                matches=doc_entry["matches"],
                num_matches=len(doc_entry["matches"]),
                # Add new match type summary stats
                contextual_matches=doc_entry["contextual_matches"],
                direct_matches=doc_entry["direct_matches"],
                balanced_matches=doc_entry["balanced_matches"],
            )
            for doc_entry in sorted_documents
        ]

        return final_results

    except Exception as e:
        logger.error(f"Error performing hybrid search: {e}")
        raise
