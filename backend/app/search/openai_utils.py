# utils / openai_utils.py


# utils / openai_utils.py
import os

import openai
from openai import AsyncOpenAI

from app.utils import setup_logger

logger = setup_logger()

# Instantiate the OpenAI client (you can keep this or comment it out)
client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def generate_query_match_explanation(query: str, chunk_content: str) -> str:
    """
    Generate a short explanation of how the query matches the contextualized chunk.
    """
    prompt = f"""
    Given the following query:
    "{query}"

    And the following chunk from a document:
    "{chunk_content}"

    Provide a one-sentence, 12 word maximum explanation starting with "Mentions ..."
    to explain why the
    chunk matches the query.

    Be extremely specific to the document at hand and avoid generalizations
    or inferences. Do not mention the query in the explanation.
    Do not include any additional text outside the explanation.
    """

    try:
        response = await async_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=250,
            temperature=0,
        )
        explanation = response.choices[0].message.content.strip()
        return explanation
    except Exception as e:
        logger.error(f"Error generating match explanation: {e}")
        return "Unable to generate explanation."


async def extract_highlight_keyphrase(query: str, chunk_content: str) -> str:
    """
    Extract single important words from the chunk that best match the query
    for highlighting in the PDF viewer.

    Args:
        query: The search query
        chunk_content: The text chunk content with METADATA, CONTEXT, and RAW TEXT sections

    Returns:
        A single important word from the chunk that can be used to locate
        and highlight the relevant parts of the PDF
    """
    # Extract the RAW TEXT section from the chunk_content if it's in the new format
    raw_text = ""
    context_info = ""

    # Check if the chunk has the new structured format with METADATA, CONTEXT, and RAW TEXT
    if "METADATA:" in chunk_content:
        # Try to extract the RAW TEXT part
        parts = chunk_content.split("RAW TEXT:")
        if len(parts) > 1:
            raw_text = parts[1].strip()

        # Extract CONTEXT section if available for reasoning
        context_parts = chunk_content.split("CONTEXT:")
        if len(context_parts) > 1:
            context_section = (
                context_parts[1].split("RAW TEXT:")[0]
                if "RAW TEXT:" in context_parts[1]
                else context_parts[1]
            )
            context_info = context_section.strip()

    # If we couldn't find the RAW TEXT section or it's empty, use the original chunk
    if not raw_text:
        logger.warning("RAW TEXT section not found or empty, using full chunk content")
        raw_text = chunk_content

    prompt = f"""
    TASK: Extract a list of 1-6 SINGLE WORDS from the RAW TEXT that appear verbatim and would be useful to highlight in the document.

    CRITICAL REQUIREMENTS:
    1. Each word MUST EXIST WORD-FOR-WORD in the RAW TEXT - verify this before responding
    2. Extract EXACTLY as written - same capitalization
    3. Choose words that relate directly to the user query
    4. Each word should be MEANINGFUL and DISTINCTIVE (avoid common words like "the", "and", "is")
    5. Return ONLY a comma-separated list of singular words with no quotes or additional text

    IF NO EXACT MATCH: If you cannot find ANY suitable words in the RAW TEXT that relate to the query, respond only with "NO_MATCH_FOUND"

    USER QUERY: "{query}"

    SELECTION CONTEXT:
    {context_info}

    RAW TEXT TO SEARCH IN:
    {raw_text}

    YOUR RESPONSE MUST BE:
    - A comma-separated list of 1-6 individual words (example: "health, nutrition, program, children")
    - OR "NO_MATCH_FOUND" if no suitable words exist
    """
    logger.info(raw_text)
    try:
        response = await async_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0,
        )
        keyword_list = response.choices[0].message.content.strip()
        logger.info(keyword_list)

        # Handle the explicit no match case
        if keyword_list == "NO_MATCH_FOUND":
            logger.warning("No suitable match found for highlighting")
            fallback = raw_text[: min(30, len(raw_text))]
            return fallback

        # Convert the comma-separated list into an actual list
        keywords = [word.strip() for word in keyword_list.split(",")]

        # Verify each keyword exists in the raw text content
        valid_keywords = []
        for keyword in keywords:
            if keyword and keyword in raw_text:
                # Additional verification to ensure it's a proper word with meaningful length
                if len(keyword.strip()) >= 3:
                    logger.info(f"Successfully found valid keyword: '{keyword}'")
                    valid_keywords.append(keyword)
                else:
                    logger.warning(f"Keyword too short: '{keyword}'")
            else:
                logger.warning(
                    f"Extracted keyword not found verbatim in chunk: '{keyword}'"
                )

        # If we found valid keywords, return them as a comma-separated string
        if valid_keywords:
            return ",".join(valid_keywords)

        # If we get here, no valid keywords were found

        # Try to find simple but distinctive words from the query in the text
        query_words = [word.lower() for word in query.split() if len(word) > 3]
        found_words = []

        for word in query_words:
            # Find the word in the raw text (case insensitive)
            raw_text_lower = raw_text.lower()
            if word in raw_text_lower:
                # Find the actual position in the original text to extract with correct case
                start_pos = raw_text_lower.find(word)
                original_word = raw_text[start_pos : start_pos + len(word)]

                if len(original_word) >= 3:
                    logger.info(f"Found word based on query: '{original_word}'")
                    found_words.append(original_word)

        if found_words:
            return ",".join(found_words)

        # Last resort fallback - extract meaningful words from the first sentence
        first_period = raw_text.find(".", 0, 100)
        if first_period != -1 and first_period > 5:
            first_sentence = raw_text[: first_period + 1].strip()
            words = [
                w
                for w in first_sentence.split()
                if len(w) > 3
                and w.lower()
                not in [
                    "this",
                    "that",
                    "with",
                    "from",
                    "have",
                    "been",
                    "were",
                    "their",
                    "there",
                ]
            ]
            if words:
                logger.info(
                    f"Using words from first sentence as fallback: '{','.join(words[:5])}'"
                )
                return ",".join(words[:5])

        # Absolute last resort - just the first few characters
        fallback = raw_text[: min(30, len(raw_text))].strip()
        logger.info(f"Using first 30 chars as fallback: '{fallback}'")
        return fallback

    except Exception as e:
        logger.error(f"Error extracting highlight keywords: {e}")
        return raw_text[: min(30, len(raw_text))]


async def rank_search_results(query: str, document_chunks: list[dict]) -> list[dict]:
    """
    Rank search results based on both contextual relevance and direct text matching.

    Args:
        query: The search query
        document_chunks: List of dictionaries containing document chunks with their info
                         Each dict must have 'doc' key with a 'contextualized_chunk' attribute

    Returns:
        List of ranked results with added metadata:
        - rank: Overall ranking position (1-based)
        - contextual_score: 0-10 score for contextual relevance
        - direct_match_score: 0-10 score for direct matching
        - strength: "Strong", "Moderate", or "Weak"
        - match_type: "direct", "balanced", or "contextual" based primarily on direct match score
    """
    if not document_chunks:
        return []

    import asyncio

    async def analyze_single_document(item):
        """Analyze a single document with LLM for contextual and direct match scoring"""
        doc = item["doc"]
        chunk_text = doc.contextualized_chunk

        # Extract raw text if it exists in the structured format
        raw_text = chunk_text
        if "RAW TEXT:" in chunk_text:
            parts = chunk_text.split("RAW TEXT:")
            if len(parts) > 1:
                raw_text = parts[1].strip()

        prompt = f"""
USER QUERY: "{query}"

Score the given page on two dimensions:
1. CONTEXTUAL MATCH (0–10): How well the page addresses the **intent** of the query (even if via paraphrase, related examples, background analysis, etc.).
2. DIRECT QUESTION MATCH (0–10): How clearly the page contains an **explicit question** about the query topic (e.g. a survey question “Do you read to your child daily?” for “child literacy”).

Then assign:
- contextual_score (1–10)
- direct_match_score (1–10)
- match_type:
    • "direct"    if direct_match_score ≥ 7 (contains a clear, on‐topic question)
    • "balanced"  if 4 ≤ direct_match_score ≤ 6
    • "contextual" if direct_match_score ≤ 3

EXAMPLES

Example 1  
Query: "child literacy"  
Page:  
> RAW TEXT: “LIT4. How often do you read stories to your child?  
> 1. Daily  2. Weekly  3. Monthly  4. Never.”  
Scoring:
```
{"contextual_score": 10, "direct_match_score": 10, "match_type": "direct"}
Reasoning: Contains an explicit survey question about reading to a child, directly addressing “child literacy.”

Example 2
Query: "child literacy"
Page:

RAW TEXT: “Literacy levels among children improved by 15% in Region A since 2019, driven by after‐school tutoring programs.”
Scoring:




{"contextual_score": 9, "direct_match_score": 0, "match_type": "contextual"}
Reasoning: Strong context (trend data on child literacy) but no actual question about the topic, so direct_match_score = 0.

Example 3
Query: "maternal health services accessibility"
Page:

RAW TEXT: “QMH5: How far do you travel to receive prenatal care?

< 5 km 2. 5–10 km 3. > 10 km”
Scoring:




{"contextual_score": 10, "direct_match_score": 8, "match_type": "direct"}
Reasoning: Contains an explicit accessibility question (“How far…prenatal care”) so high direct_match_score.

Example 4
Query: "education program effectiveness"
Page:

CONTEXT: Discusses government spending on school infrastructure.
RAW TEXT: “Since 2020, investment in classroom buildings rose by 20%.”
Scoring:




{"contextual_score": 7, "direct_match_score": 2, "match_type": "contextual"}
Reasoning: Relevant background on education investment, but no question probing program outcomes.

DOCUMENT TO ANALYZE:
{chunk_text[:20000]}

Return  only, with exactly:




{
  "contextual_score": N,
  "direct_match_score": N,
  "match_type": "direct|balanced|contextual"
}
        """

        try:
            response = await async_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=200,
                temperature=0,
            )

            result_json = response.choices[0].message.content
            import json

            try:
                result_data = json.loads(result_json)

                # Create a copy of the document info to avoid modifying the original
                doc_info = item.copy()

                # Add scores from the LLM
                contextual_score = result_data.get("contextual_score", 5)
                direct_score = result_data.get("direct_match_score", 5)

                doc_info["contextual_score"] = contextual_score
                doc_info["direct_match_score"] = direct_score

                # Determine match type based on direct score thresholds, ignoring LLM's classification
                if direct_score >= 7:
                    doc_info["match_type"] = "direct"
                elif direct_score >= 4:
                    doc_info["match_type"] = "balanced"
                else:
                    doc_info["match_type"] = "contextual"

                # Calculate an overall score (weighted heavily toward direct matches)
                doc_info["overall_score"] = (contextual_score * 0.3) + (
                    direct_score * 0.7
                )

                return doc_info

            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response as JSON: {result_json}")
                # Fall back to simpler scoring for this document
                doc_info = item.copy()
                doc_info["contextual_score"] = 5  # Neutral score
                doc_info["direct_match_score"] = 5  # Neutral score
                doc_info["match_type"] = "balanced"
                doc_info["overall_score"] = 5
                return doc_info

        except Exception as e:
            logger.error(f"Error ranking document with LLM: {e}")
            # Fall back to neutral scoring
            doc_info = item.copy()
            doc_info["contextual_score"] = 5
            doc_info["direct_match_score"] = 5
            doc_info["match_type"] = "balanced"
            doc_info["overall_score"] = 5
            return doc_info

    # Process documents in parallel (limit concurrency to avoid rate limits)
    # Use semaphore to limit concurrency to 10 parallel requests
    semaphore = asyncio.Semaphore(10)

    async def analyze_with_semaphore(item):
        async with semaphore:
            return await analyze_single_document(item)

    # Run all document analyses in parallel
    tasks = [analyze_with_semaphore(item) for item in document_chunks]
    ranked_results = await asyncio.gather(*tasks)

    # Sort by overall score
    ranked_results.sort(key=lambda x: x["overall_score"], reverse=True)

    # Add rank and strength labels
    for rank_index, result in enumerate(ranked_results):
        result["rank"] = rank_index + 1

        # Determine strength based on overall score
        overall_score = result["overall_score"]
        if overall_score >= 9:
            result["strength"] = "Strong"
        elif overall_score >= 5.0:
            result["strength"] = "Moderate"
        else:
            result["strength"] = "Weak"

    return ranked_results
