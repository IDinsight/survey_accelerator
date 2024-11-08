# utils/openai_utils.py

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

    Here is the chunk we want to situate within the whole document
    <chunk>
    {chunk_content}
    </chunk>

    Please give a short succinct context to situate this chunk within the overall
    document which is a survey questionnaire for the purposes of improving search
    retrieval of the chunk.
    Answer only with the succinct context and nothing else.
    """
    prompt += "\n"
    try:
        # Comment out the OpenAI API call
        # response = client.chat.completions.create(
        #     model="gpt-4o-mini",
        #     messages=[
        #         {"role": "user", "content": prompt},
        #     ],
        #     max_tokens=150,
        #     temperature=0,
        # )
        # summary = response.choices[0].message.content.strip()

        # Return a dummy summary
        summary = (
            "This chunk contains questions about contraception awareness and attitudes."
        )

        return summary
    except Exception as e:
        logger.error(f"Unexpected error generating contextual summary: {e}")
        return ""


def generate_brief_summary(document_content: str) -> str:
    """
    Generate a concise summary of the entire document in 10-15 words.
    """
    # Construct the prompt (optional)
    prompt = (
        f"Summarize the following document in 10 to 15 words:\n\n{document_content}"
    )
    prompt += "\n"

    try:
        # Comment out the OpenAI API call
        # response = client.chat.completions.create(
        #     model="gpt-4o-mini",
        #     messages=[
        #         {"role": "user", "content": prompt},
        #     ],
        #     max_tokens=20,
        #     temperature=0.5,
        # )
        # summary = response.choices[0].message.content.strip()

        # Return a dummy brief summary
        summary = "Survey questionnaire focusing on men's reproductive health."

        return summary
    except Exception as e:
        logger.error(f"Error generating brief summary: {e}")
        return ""


def generate_smart_filename(file_name: str, document_content: str) -> str:
    """
    Generate an elegant filename devoid of year numbers.

    Args:
        file_name: Original file name.
        document_content: Content of the document.

    Returns:
        An elegant filename as a string.
    """
    # Construct the prompt (optional)
    prompt = f"""
    Given the original file name "{file_name}" and the first few
    pages of content below, generate an elegant
    and descriptive filename without any year numbers.

    Do not include any dates in the filename.

    Content excerpt:
    {document_content[:2000]}

    Filename:
    """
    prompt += "\n"
    try:
        # Comment out the OpenAI API call
        # response = client.chat.completions.create(
        #     model="gpt-4o-mini",
        #     messages=[
        #         {"role": "user", "content": prompt},
        #     ],
        #     max_tokens=10,
        #     temperature=0.5,
        # )
        # smart_name = response.choices[0].message.content.strip()

        # Return a dummy filename
        smart_name = "Men's Health Survey Questionnaire"

        return smart_name
    except Exception as e:
        logger.error(f"Error generating elegant filename: {e}")
        return ""


def extract_question_answer_from_page(chunk_content: str) -> list[dict]:
    """
    Extract questions and answers from a chunk of text.
    """
    # Construct the prompt (optional)
    prompt = f"""
    <chunk>
    {chunk_content}
    </chunk>

    Extract questions and answering options from the chunk above of a survey
    questionnaire instrument. The survey may be messy but take time to reason through
    your response.

    THE OUTPUT FORMAT MUST BE IN THE FORM OF A **VALID JSON LIST OF DICTIONARIES**
    STRUCTURED AS FOLLOWS:
    [
        {{"question": "Do you have a car?", "answers": ["Yes", "No"]}},
        {{"question": "How many times do you eat out?", "answers": ["Once a week",
        "Twice a week", "Never"]}}
    ]

    IF NO QUESTIONS OR ANSWERS ARE FOUND, RETURN AN EMPTY LIST: []

    RETURN ONLY THE JSON LIST. DO NOT INCLUDE ANY OTHER TEXT IN YOUR ANSWER.

    Your answer:
    """
    prompt += "\n"

    try:
        # Comment out the OpenAI API call
        # response = client.chat.completions.create(
        #     model="gpt-4o-mini",
        #     messages=[
        #         {"role": "user", "content": prompt},
        #     ],
        #     max_tokens=1000,  # Increase to ensure full responses
        #     temperature=0,
        # )
        # qa_pairs_str = response.choices[0].message.content.strip()

        # Return dummy QA pairs
        qa_pairs = [
            {
                "question": "Have you heard about family planning on the radio?",
                "answers": ["Yes", "No"],
            },
            {
                "question": "Do you agree  contraception is a woman's concern a man?",
                "answers": ["Agree", "Disagree", "Don't know"],
            },
            {
                "question": "Do you watch television at least once a or not at all?",
                "answers": [
                    "At least once a week",
                    "Less than once a week",
                    "Not at all",
                ],
            },
        ]

        # If you want to test with an empty list, you can uncomment the line below
        # qa_pairs = []

        return qa_pairs
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
    prompt += "\n"

    try:
        # response = client.chat.completions.create(
        #     model="gpt-4o-mini",
        #     messages=[
        #         {"role": "user", "content": prompt},
        #     ],
        #     max_tokens=1000,  # Increase to ensure full responses
        #     temperature=0,
        # )
        # qa_pairs_str = response.choices[0].message.content.strip()

        # Dummy explanation for testing
        explanation = f"""Mentions how '{query}' relates to contraception and family
        planning."""

        return explanation
    except Exception as e:
        logger.error(f"Error generating match explanation: {e}")
        return "Unable to generate explanation."
