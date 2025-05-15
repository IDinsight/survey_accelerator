"""Utilities for highlighting PDF documents based on search terms."""

import asyncio
import hashlib
import json
import os
import tempfile
from typing import Dict, List, Optional
from urllib.parse import quote, urljoin

import aiohttp
import fitz
from fastapi import HTTPException

from app.utils import setup_logger

logger = setup_logger()

# Ensure BACKEND_API_URL includes scheme
BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://localhost:8000")

# Directory to store highlighted PDFs
HIGHLIGHT_DIR = os.environ.get("HIGHLIGHT_DIR", "./highlighted_pdfs")
os.makedirs(HIGHLIGHT_DIR, exist_ok=True)

# Highlight color (RGB values as a tuple)
HIGHLIGHT_COLOR = (1, 0.8, 0.2)  # Yellow-orange

# Cache to track PDFs currently being processed
processing_pdfs: Dict[str, asyncio.Task] = {}


def make_pdf_url(filename: str, mode: str = "regular") -> str:
    """
    Build a correctly encoded URL for accessing PDFs:
      http://host:port/pdf/<percent-encoded-filename>?type=<mode>
    """
    safe_name = quote(filename, safe="")
    path = f"/pdf/{safe_name}?type={mode}"
    return urljoin(BACKEND_API_URL, path)


async def get_highlighted_pdf(
    pdf_url: str,
    search_term: str,
    page_keywords: Optional[Dict[int, List[str]]] = None,
) -> str:
    """
    Get URL to a highlighted version of a PDF.
    If the highlighted PDF doesn't exist, create it first.
    """
    # Create cache key
    if page_keywords:
        page_keywords_str = json.dumps(page_keywords, sort_keys=True)
        cache_key = (
            f"{pdf_url}_paged_{hashlib.md5(page_keywords_str.encode()).hexdigest()}"
        )
    else:
        cache_key = f"{pdf_url}_{search_term}"

    pdf_filename = hashlib.md5(cache_key.encode()).hexdigest() + ".pdf"
    highlighted_path = os.path.join(HIGHLIGHT_DIR, pdf_filename)

    # Return existing
    if os.path.exists(highlighted_path):
        return make_pdf_url(pdf_filename, mode="highlighted")

    # Wait if processing
    if cache_key in processing_pdfs and not processing_pdfs[cache_key].done():
        logger.info(f"Waiting for highlighting of {pdf_url} to complete")
        try:
            await processing_pdfs[cache_key]
        except Exception as e:
            logger.error(f"Error waiting for PDF processing: {e}")

    # Start processing
    task = asyncio.create_task(
        _process_and_highlight_pdf(
            pdf_url, search_term, highlighted_path, page_keywords
        )
    )
    processing_pdfs[cache_key] = task

    try:
        await task
        return make_pdf_url(pdf_filename, mode="highlighted")
    except Exception as e:
        logger.error(f"Error highlighting PDF {pdf_url}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create highlighted PDF: {str(e)}"
        )


async def _process_and_highlight_pdf(
    pdf_url: str,
    search_term: str,
    output_path: str,
    page_keywords: Optional[Dict[int, List[str]]] = None,
) -> None:
    """
    Download a PDF and add highlights for the search term.
    """
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        temp_path = tmp.name

    try:
        # Prepare download URL
        filename = os.path.basename(pdf_url)
        download_url = make_pdf_url(filename, mode="regular")
        logger.info(f"Downloading PDF from {download_url}")

        # Download
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Failed to download PDF: HTTP {response.status}",
                    )
                with open(temp_path, "wb") as f:
                    f.write(await response.read())

        # Highlight
        if page_keywords:
            logger.info("Adding page-specific highlights to PDF")
            _add_page_specific_highlights(temp_path, output_path, page_keywords)
        else:
            logger.info(
                f"Adding highlights for term '{search_term}' to PDF (all pages)"
            )
            _add_highlights(temp_path, output_path, search_term)

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def _add_page_specific_highlights(
    input_path: str, output_path: str, page_keywords: Dict[int, List[str]]
) -> None:
    """Add highlights to specific pages of a PDF."""
    doc = fitz.open(input_path)
    highlights_added = False
    for page_str, keywords in page_keywords.items():
        page_num = int(page_str) - 1
        if page_num < 0 or page_num >= len(doc):
            logger.warning(f"Page {page_num+1} out of bounds")
            continue
        page = doc[page_num]
        for keyword in keywords:
            if len(keyword) < 2:
                continue
            quads = page.search_for(keyword, quads=True)
            for quad in quads:
                annot = page.add_highlight_annot(quad)
                annot.set_colors(stroke=HIGHLIGHT_COLOR)
                annot.set_opacity(0.6)
                annot.update()
                highlights_added = True
    doc.save(output_path)
    doc.close()


def _add_highlights(input_path: str, output_path: str, search_terms: str) -> None:
    """Add highlights for all occurrences of search terms across all pages."""
    terms = (
        [t.strip() for t in search_terms.split(",")]
        if "," in search_terms
        else [search_terms]
    )
    doc = fitz.open(input_path)
    highlights_added = False
    for page in doc:
        for term in terms:
            if len(term) < 2:
                continue
            quads = page.search_for(term, quads=True)
            for quad in quads:
                annot = page.add_highlight_annot(quad)
                annot.set_colors(stroke=HIGHLIGHT_COLOR)
                annot.set_opacity(0.6)
                annot.update()
                highlights_added = True
    doc.save(output_path)
    doc.close()
