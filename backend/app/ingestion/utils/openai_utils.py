# utils/openai_utils.py

import openai
from app.config import OPENAI_API_KEY
from app.utils import setup_logger
import os

logger = setup_logger()

# Instantiate the OpenAI client
client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))


def generate_contextual_summary(document_content, chunk_content):
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

    Please give a short succinct context to situate this chunk within the overall document which is a survey questionnaire for the purposes of improving search retrieval of the chunk.
    Answer only with the succinct context and nothing else.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
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
