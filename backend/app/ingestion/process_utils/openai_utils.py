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

