# utils / openai_utils.py


# utils / openai_utils.py
import os

import openai
from app.utils import setup_logger
from openai import AsyncOpenAI

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
                logger.warning(f"Extracted keyword not found verbatim in chunk: '{keyword}'")

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
                original_word = raw_text[start_pos:start_pos + len(word)]
                
                if len(original_word) >= 3:
                    logger.info(f"Found word based on query: '{original_word}'")
                    found_words.append(original_word)
        
        if found_words:
            return ",".join(found_words)

        # Last resort fallback - extract meaningful words from the first sentence
        first_period = raw_text.find(".", 0, 100)
        if first_period != -1 and first_period > 5:
            first_sentence = raw_text[: first_period + 1].strip()
            words = [w for w in first_sentence.split() if len(w) > 3 and w.lower() not in ["this", "that", "with", "from", "have", "been", "were", "their", "there"]]
            if words:
                logger.info(f"Using words from first sentence as fallback: '{','.join(words[:5])}'")
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
        
        Analyze this document for search relevance by scoring it on two dimensions:
        1. CONTEXTUAL MATCH: How well the document addresses the query's intent and meaning (0-10 scale)
        2. DIRECT TEXT MATCH: How directly the document contains exact query terms and phrases (0-10 scale)
        
        You'll provide:
        - contextual_score (0-10): Higher if document contains information relevant to the query's intent
        - direct_match_score (0-10): Higher if document contains exact query terms or paraphrases
        - match_type: Use these clear guidelines:
          * "direct": if direct_match_score >= 7, indicating strong verbatim match with query terms
          * "balanced": if direct_match_score is 4-6, showing moderate presence of query terms
          * "contextual": if direct_match_score <= 3, meaning few or no direct query terms present
        
        EXAMPLES:
        
        Example 1:
        Query: "vaccination rate trends in rural areas"
        Document: "METADATA: Page 7, Rural Health Survey Report 2022... CONTEXT: This section analyzes healthcare access... RAW TEXT: The vaccination rates in rural counties decreased by 12% between 2020-2022, compared to a 3% decrease in urban areas. Contributing factors include transportation difficulties and workforce shortages."
        Scoring:
        {{"contextual_score": 9, "direct_match_score": 8, "match_type": "direct"}}
        Reasoning: High contextual score because it directly addresses vaccination rate trends in rural areas with specific statistics. High direct match score due to phrases "vaccination rates" and "rural" appearing verbatim in the RAW TEXT.
        
        Example 2:
        Query: "education program effectiveness"
        Document: "METADATA: Page 15, Policy Analysis... CONTEXT: This is from a part of a survey that covers various policy implementations, including education and health... RAW TEXT: Government spending on infrastructure development increased by 24% since the previous fiscal year, with priority given to upgrading transportation systems."
        Scoring:
        {{"contextual_score": 8, "direct_match_score": 1, "match_type": "contextual"}}
        Reasoning: Low contextual score because document discusses government infrastructure spending, not education programs. Zero direct match score because no query terms appear in the RAW TEXT.
        
        Example 3:
        Query: "child nutrition programs in schools"
        Document: "METADATA: Page 23, Educational Policy Report... CONTEXT: This section discusses school meal programs... RAW TEXT: The school lunch program was expanded to include breakfast services, increasing overall student attendance by 7%. Teachers reported improved concentration in morning classes."
        Scoring:
        {{"contextual_score": 8, "direct_match_score": 5, "match_type": "balanced"}}
        Reasoning: High contextual score because it discusses school meal programs which relate directly to child nutrition in schools. Medium direct match score because words like "school" appear but "nutrition" and "child" don't appear verbatim in the RAW TEXT.
        
        Example 4:
        Query: "maternal health services accessibility"
        Document: "METADATA: Page 42, Healthcare Review 2023... CONTEXT: This reviews healthcare systems... RAW TEXT: Women in rural districts reported traveling an average of 27 kilometers to access maternal health services. Community health workers have been deployed to improve accessibility to prenatal care."
        Scoring:
        {{"contextual_score": 9, "direct_match_score": 9, "match_type": "direct"}}
        Reasoning: Very high contextual score for directly addressing the topic. High direct match score because phrases "maternal health services" and "accessibility" appear verbatim in the RAW TEXT.
        
        DOCUMENT TO ANALYZE:
        {chunk_text[:1000]}  
        
        Return your analysis as JSON with this exact structure (no additional text):
        {{
          "contextual_score": N,  // 0-10 score
          "direct_match_score": N,  // 0-10 score
          "match_type": "direct|balanced|contextual"  // pick one based on direct_match_score thresholds
        }}
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
                doc_info["overall_score"] = (contextual_score * 0.3) + (direct_score * 0.7)
                
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