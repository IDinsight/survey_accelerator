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

        # Prepare for reranking: collect texts and match info.
        texts = []
        match_info = []
        for doc, _score in combined_results:
            texts.append(doc.contextualized_chunk)
            match_info.append(
                {
                    "doc": doc,
                    "page_number": doc.page_number,
                }
            )

        if not texts:
            return []

        # Rerank using Cohere (or another service).
        rerank_response = co.rerank(
            model="rerank-english-v3.0",
            query=query_str,
            documents=texts,
            top_n=None,
            return_documents=False,
        )

        # Assemble reranked matches with strength labels.
        reranked_matches = []
        for rank_index, result_item in enumerate(rerank_response.results):
            index = result_item.index
            info = match_info[index]
            doc = info["doc"]
            match_result = {
                "doc": doc,
                "page_number": info["page_number"],
                "rank": rank_index + 1,
                "strength": (
                    "Strong"
                    if (rank_index + 1) <= 12
                    else "Moderate" if (rank_index + 1) <= 20 else "Weak"
                ),
            }
            reranked_matches.append(match_result)

        # Take top matches according to the provided max_results.
        top_matches = reranked_matches[:max_results]

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
                }
            # Count strengths.
            if match["strength"] == "Strong":
                documents_group[document_id]["strong_count"] += 1
            elif match["strength"] == "Moderate":
                documents_group[document_id]["moderate_count"] += 1
            else:
                documents_group[document_id]["weak_count"] += 1

            matched_chunk = MatchedChunk(
                page_number=match["page_number"],
                rank=match["rank"],
                explanation=explanations[i],
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
            documents_group[document_id]["matches"].append(matched_chunk)

        # Sort documents by strong_count (primary) and moderate_count (secondary).
        sorted_documents = sorted(
            documents_group.values(),
            key=lambda d: (d["strong_count"], d["moderate_count"], -d["weak_count"]),
            reverse=True,
        )

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
