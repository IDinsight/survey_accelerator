# utils/openai_utils.py

import os

import openai

from app.utils import setup_logger

logger = setup_logger()

# Instantiate the OpenAI client
client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))


def generate_contextual_summary(document_content: str, chunk_content: str) -> str:
    """
    Generate a concise contextual summary for a chunk using OpenAI's GPT-4.
    """
    prompt = f"""
    <document>
    {document_content}
    </document>

    Here is the chunk we want to situate within the whole document
    <chunk>
    {chunk_content}
    </chunk>

    Please give a short succinct context to situate this chunk within the overall
    document     which is a survey questionnaire for the purposes of improving search
    retrieval of the chunk.
    Answer only with the succinct context and nothing else.
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
    prompt = (
        f"Summarize the following document in 10 to 15 words:\n\n{document_content}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=20,
            temperature=0.5,
        )
        summary = response.choices[0].message.content.strip()
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
    prompt = f"""
    Given the original file name "{file_name}" and the first few
    pages of content below, generate an elegant
    and descriptive filename without any year numbers.

    Do not include any dates in the filename.

    Content excerpt:
    {document_content[:2000]}

    Filename:
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=10,
            temperature=0.5,
        )
        smart_name = response.choices[0].message.content.strip()
        return smart_name
    except Exception as e:
        logger.error(f"Error generating elegant filename: {e}")
        return ""


def extract_question_answer_from_page(chunk_content: str) -> str:
    """
    Extract questions and answers from a chunk of text using OpenAI's GPT-4.
    """
    prompt = f"""
    <chunk>
    {chunk_content}
    </chunk>

    Extract questions and answering options from the chunk above of a survey
    questionnaire instrument. The survey may be messy but take time to reason through
    your response.

    THE OUTPUT FORMAT MUST BE IN THE FORM OF A LIST OF DICTIONARIES
    STRUCTURED AS FOLLOWS:
    [
        {{"question": "Do you have a car?", "answers": ["Yes", "No"]}},
        {{"question": "How many times do you eat out?", "answers": ["Once a week",
        "Twice a week", "Never"]}}

    IF NO QUESTIONS OR ANSWERS ARE FOUND, LEAVE THE LIST EMPTY.
    RETURN ONLY THE LIST OF DICTIONARIES. DO NOT INCLUDE ANY OTHER TEXT IN YOUR ANSWER.

    Your answer:
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
        qa_pairs = response.choices[0].message.content.strip()
        return qa_pairs
    except Exception as e:
        logger.error(f"Error extracting questions and answers: {e}")
        return ""
