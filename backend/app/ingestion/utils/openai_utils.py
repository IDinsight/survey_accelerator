# utils / openai_utils.py

import json
import os

import openai

from app.utils import setup_logger

logger = setup_logger()

# Instantiate the OpenAI client (you can keep this or comment it out)
client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))


def generate_contextual_summary(document_content: str, chunk_content: str) -> str:
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
        response = client.chat.completions.create(
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


def generate_brief_summary(document_content: str) -> str:
    """
    Generate a concise summary of the entire document in 10-15 words.
    """
    # Construct the prompt (optional)
    prompt = f"""Summarize the following document in 10 to 15 in a sentence that
        starts with the word 'Covers'
        e.g. 'Covers womens health and contraception awareness.' or
        'Covers the impact of climate change on agriculture.'
        Respond only with the summary and nothing else.
        ENSURE YOUR ANSWER NEVER EXCEEDS 15 WORDS.
        Below is the content to summarize:
        \n\n{document_content}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=20,
            temperature=0.2,
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        logger.error(f"Error generating brief summary: {e}")
        return ""


def generate_smart_filename(file_name: str, document_content: str) -> str:
    """
    Generate a specific and elegant filename devoid of year numbers.

    Args:
        file_name: Original file name.
        document_content: Content of the document.

    Returns:
        A descriptive filename as a plain text string.
    """
    # Construct the prompt with precise instructions
    prompt = f"""
    Given the original file name "{file_name}" and the content excerpt below, generate
    a specific and descriptive filename that includes relevant information, such as the
    organization name (e.g., 'USAID', 'UNICEF') and the main topic of the document.

    The filename should:
    - Avoid any dates or year numbers
    - Exclude prefixes like 'Filename:', asterisks, or other symbols
    - Be concise, specific, and relevant to the document content

    Examples of appropriate filenames might include:
    - 'USAID Family Health Survey'
    - 'UNICEF Maternal Health Questionnaire'
    - 'DHS Reproductive Health Analysis'

    Content excerpt:
    {document_content[:2000]}

    Plain text filename:
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=10,
            temperature=0.2,
        )
        smart_name = response.choices[0].message.content.strip()

        # Optional: Ensure there's no unexpected text or symbols
        smart_name = smart_name.split(":", 1)[
            -1
        ].strip()  # Remove anything before a colon

        return smart_name
    except Exception as e:
        logger.error(f"Error generating elegant filename: {e}")
        return ""


def extract_question_answer_from_page(chunk_content: str) -> list[dict]:
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
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
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


def generate_query_match_explanation(query: str, chunk_content: str) -> str:
    """
    Generate a short explanation of how the query matches the contextualized chunk.
    """
    prompt = f"""
    Given the following query:
    "{query}"

    And the following chunk from a document:
    "{chunk_content}"

    Provide a one-sentence explanation starting with "Mentions ..." to explain why the
    chunk matches the query.
    """

    try:
        response = client.chat.completions.create(
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
