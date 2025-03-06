# utils / openai_utils.py

import json
import os

import openai
from app.utils import setup_logger
from openai import AsyncOpenAI

logger = setup_logger()

# Instantiate the OpenAI client (you can keep this or comment it out)
client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def generate_contextual_summary(document_content: str, chunk_content: str) -> str:
    """
    Generate a concise contextual summary for a chunk.
    """
    # Construct the prompt (optional, you can comment this out if not needed)
    prompt = f"""
        <document>
        {document_content}
        </document>

        Here is a specific page from the document:
        <chunk>
        {chunk_content}
        </chunk>

        Please provide a concise, contextually accurate summary for the above page based
        strictly on its visible content.
        DO NOT include generic survey topics (e.g., contraception) unless clearly
        mentioned on the page.
        This is to improve precise search relevance and must reflect what is
        explicitly covered on this page AND HOW IT SITUATES WITHIN THE LARGER DOCUMENT.
        Answer only with the context, avoiding any inferred topics.
        """
    try:
        response = await async_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=150,
            temperature=0,
        )
        summary = response.choices[0].message.content.strip()

        return summary

    except Exception as e:
        logger.error(f"Unexpected error generating contextual summary: {e}")
        return ""


async def extract_question_answer_from_page(chunk_content: str) -> list[dict]:
    """
    Extract questions and answers from a chunk of text.
    """
    prompt = f"""
    You are to extract questions and their possible answers from the following survey
    questionnaire chunk. The survey may be messy, but take time to reason through your
    response.

    **Provide the output as a JSON list of dictionaries in the following format without
    any code block or markdown formatting**:
    [
        {{"question": "Question text", "answers": ["Answer 1", "Answer 2"]}},
        ...
    ]

    **Do not include any additional text outside the JSON array. Do not include any code
    block notation, such as triple backticks or language identifiers like
json.**

    If no questions or answers are found, return an empty list: []

    Chunk:
    {chunk_content}
    """

    try:
        response = await async_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=2500,
            temperature=0,
        )
        qa_pairs_str = response.choices[0].message.content.strip()
        qa_pairs = json.loads(qa_pairs_str)
        return qa_pairs
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        logger.error(f"Response was: {qa_pairs_str}")
        return []
    except Exception as e:
        logger.error(f"Error extracting questions and answers: {e}")
        return []


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
    Extract a verbatim text snippet from the chunk that best matches the query
    for highlighting in the PDF viewer.

    Args:
        query: The search query
        chunk_content: The text chunk content with METADATA, CONTEXT, and RAW TEXT sections

    Returns:
        A verbatim text snippet (5-15 words) from the chunk that can be used to locate
        the relevant part of the PDF for highlighting
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
    TASK: Extract EXACTLY 2-3 consecutive words from the RAW TEXT that appear verbatim and would be useful to highlight in the document.

    CRITICAL REQUIREMENTS:
    1. The words MUST EXIST WORD-FOR-WORD in the RAW TEXT - verify this before responding
    2. Extract EXACTLY as written - same capitalization, spacing, and punctuation
    3. Choose words that relate directly to the user query
    4. Check that your selected words appear CONSECUTIVELY and UNALTERED in the RAW TEXT
    5. Return ONLY the extracted words with no quotes or additional text

    IF NO EXACT MATCH: If you cannot find ANY 2-3 word sequence that appears verbatim in the RAW TEXT and relates to the query, respond only with "NO_MATCH_FOUND"

    USER QUERY: "{query}"

    SELECTION CONTEXT:
    {context_info}

    RAW TEXT TO SEARCH IN:
    {raw_text}

    YOUR RESPONSE MUST BE EITHER:
    - EXACTLY 2-3 consecutive words that appear verbatim in the RAW TEXT
    - OR "NO_MATCH_FOUND" if no suitable text exists
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
        keyphrase = response.choices[0].message.content.strip()
        logger.info(keyphrase)
        # Handle the explicit no match case
        if keyphrase == "NO_MATCH_FOUND":
            logger.warning("No suitable match found for highlighting")
            fallback = raw_text[: min(30, len(raw_text))]
            return fallback

        # Verify the keyphrase exists in the raw text content
        if keyphrase and keyphrase in raw_text:
            # Additional verification to ensure it's a proper substring with meaningful length
            if len(keyphrase.strip()) >= 2:
                logger.info(f"Successfully found valid keyphrase: '{keyphrase}'")
                return keyphrase
            else:
                logger.warning(f"Keyphrase too short: '{keyphrase}'")
        else:
            logger.warning(
                f"Extracted keyphrase not found verbatim in chunk: '{keyphrase}'"
            )

        # If we get here, the keyphrase was invalid or not found

        # Try to find simple but distinctive words from the query in the text
        query_words = [word.lower() for word in query.split() if len(word) > 3]
        for word in query_words:
            # Find the word in the raw text (case insensitive)
            raw_text_lower = raw_text.lower()
            if word in raw_text_lower:
                # Find the actual position in the original text
                start_pos = raw_text_lower.find(word)

                # Extract a context window around the found word (find a space before and after)
                # Look for a space before
                context_start = raw_text.rfind(" ", max(0, start_pos - 30), start_pos)
                if context_start == -1:
                    context_start = max(0, start_pos - 10)

                # Look for a space after
                context_end = raw_text.find(
                    " ",
                    start_pos + len(word),
                    min(len(raw_text), start_pos + len(word) + 30),
                )
                if context_end == -1:
                    context_end = min(len(raw_text), start_pos + len(word) + 10)

                # Extract the context with the exact casing from the original text
                extracted_text = raw_text[context_start:context_end].strip()
                if len(extracted_text) >= 2:
                    logger.info(
                        f"Found fallback text based on query word '{word}': '{extracted_text}'"
                    )
                    return extracted_text

        # Last resort fallback - try to get a meaningful chunk from the beginning
        # Look for the first period or sentence boundary within the first 50 chars
        first_period = raw_text.find(".", 0, 50)
        if first_period != -1 and first_period > 5:
            fallback = raw_text[: first_period + 1].strip()
            logger.info(f"Using first sentence as fallback: '{fallback}'")
            return fallback

        # Absolute last resort - just the first few characters
        fallback = raw_text[: min(30, len(raw_text))].strip()
        logger.info(f"Using first 30 chars as fallback: '{fallback}'")
        return fallback

    except Exception as e:
        logger.error(f"Error extracting highlight keyphrase: {e}")
        return raw_text[: min(30, len(raw_text))]
