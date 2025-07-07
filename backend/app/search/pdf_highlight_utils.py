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

# Ensure BACKEND_API_URL includes scheme - default to production domain if not set
BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "https://survey.idinsight.io/api")

# Directory to store highlighted PDFs
HIGHLIGHT_DIR = os.environ.get("HIGHLIGHT_DIR", "./highlighted_pdfs")
# Ensure HIGHLIGHT_DIR is an absolute path
if not os.path.isabs(HIGHLIGHT_DIR):
    HIGHLIGHT_DIR = os.path.abspath(HIGHLIGHT_DIR)

logger.info(f"Using highlighted PDF directory: {HIGHLIGHT_DIR}")
os.makedirs(HIGHLIGHT_DIR, exist_ok=True)

# Highlight color (RGB values as a tuple)
HIGHLIGHT_COLOR = (1, 0.8, 0.2)  # Yellow-orange

# Cache to track PDFs currently being processing
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
    # Create a permanent file in the same directory as the highlighted PDFs
    # instead of a temporary one that gets deleted
    pdf_filename = hashlib.md5(pdf_url.encode()).hexdigest() + "_original.pdf"
    pdf_path = os.path.join(HIGHLIGHT_DIR, pdf_filename)
    
    try:
        # If we already downloaded this PDF before, don't download it again
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000:
            logger.info(f"Using previously downloaded PDF: {pdf_path}")
        else:
            # Download directly from the provided PDF URL
            logger.info(f"Downloading PDF from {pdf_url}")

            # Download
            async with aiohttp.ClientSession() as session:
                async with session.get(pdf_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download PDF from {pdf_url}: HTTP {response.status}")
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Failed to download PDF: HTTP {response.status}",
                        )
                    with open(pdf_path, "wb") as f:
                        content = await response.read()
                        f.write(content)
                        logger.info(f"Downloaded {len(content)} bytes to {pdf_path}")

            # Verify file was downloaded and has content
            if not os.path.exists(pdf_path):
                logger.error(f"Downloaded file doesn't exist at {pdf_path}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Downloaded PDF file missing at {pdf_path}",
                )
                
            file_size = os.path.getsize(pdf_path)
            if file_size == 0:
                logger.error(f"Downloaded file is empty: {pdf_path}")
                raise HTTPException(
                    status_code=500,
                    detail="Downloaded PDF file is empty",
                )
            
            logger.info(f"Successfully downloaded PDF ({file_size} bytes)")

        # Highlight
        if page_keywords:
            logger.info("Adding page-specific highlights to PDF")
            _add_page_specific_highlights(pdf_path, output_path, page_keywords)
        else:
            logger.info(
                f"Adding highlights for term '{search_term}' to PDF (all pages)"
            )
            _add_highlights(pdf_path, output_path, search_term)

        # Verify the highlighted PDF was created
        if not os.path.exists(output_path):
            logger.error(f"Highlighted PDF wasn't created at {output_path}")
            raise HTTPException(
                status_code=500,
                detail="Failed to create highlighted PDF",
            )
        
        logger.info(f"Successfully created highlighted PDF at {output_path}")

    except Exception as e:
        logger.error(f"Error processing PDF {pdf_url}: {str(e)}")
        raise


def _add_page_specific_highlights(
    input_path: str, output_path: str, page_keywords: Dict[int, List[str]]
) -> None:
    """Add highlights to specific pages of a PDF."""
    try:
        # Ensure both paths are absolute
        input_path = os.path.abspath(input_path)
        output_path = os.path.abspath(output_path)
        
        logger.info(f"Opening PDF for highlighting: {input_path}")
        
        # Try to open the PDF with more specific error handling
        try:
            doc = fitz.open(input_path)
            if doc.is_closed or doc.page_count == 0:
                logger.error(f"Failed to open PDF: {input_path} (document is closed or empty)")
                raise ValueError(f"PDF could not be opened or is empty: {input_path}")
            logger.info(f"Successfully opened PDF with {doc.page_count} pages")
        except Exception as e:
            logger.error(f"Failed to open PDF: {input_path}, Error: {str(e)}")
            # Try to get more information about the file
            if os.path.exists(input_path):
                file_size = os.path.getsize(input_path)
                logger.info(f"File exists, size: {file_size} bytes")
                if file_size < 1000:  # If file is small, log its content for debugging
                    try:
                        with open(input_path, 'rb') as f:
                            logger.info(f"File content (first 100 bytes): {f.read(100)}")
                    except Exception as read_err:
                        logger.error(f"Failed to read file content: {str(read_err)}")
            raise
        
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
                logger.debug(f"Searching for keyword: '{keyword}' on page {page_num+1}")
                quads = page.search_for(keyword, quads=True)
                for quad in quads:
                    annot = page.add_highlight_annot(quad)
                    annot.set_colors(stroke=HIGHLIGHT_COLOR)
                    annot.set_opacity(0.6)
                    annot.update()
                    highlights_added = True
        
        # Save the highlighted PDF
        logger.info(f"Saving highlighted PDF to: {output_path}")
        doc.save(output_path)
        doc.close()
        
        if highlights_added:
            logger.info("Highlights added successfully")
        else:
            logger.warning("No highlights were added to the PDF")
            
    except Exception as e:
        logger.error(f"Error in _add_page_specific_highlights: {str(e)}")
        raise


def _add_highlights(input_path: str, output_path: str, search_terms: str) -> None:
    """Add highlights for all occurrences of search terms across all pages."""
    try:
        # Ensure both paths are absolute
        input_path = os.path.abspath(input_path)
        output_path = os.path.abspath(output_path)
        
        logger.info(f"Opening PDF for highlighting: {input_path}")
        
        # Try to open the PDF with more specific error handling
        try:
            doc = fitz.open(input_path)
            if doc.is_closed or doc.page_count == 0:
                logger.error(f"Failed to open PDF: {input_path} (document is closed or empty)")
                raise ValueError(f"PDF could not be opened or is empty: {input_path}")
            logger.info(f"Successfully opened PDF with {doc.page_count} pages")
        except Exception as e:
            logger.error(f"Failed to open PDF: {input_path}, Error: {str(e)}")
            raise
            
        terms = (
            [t.strip() for t in search_terms.split(",")]
            if "," in search_terms
            else [search_terms]
        )
        
        highlights_added = False
        for page in doc:
            for term in terms:
                if len(term) < 2:
                    continue
                logger.debug(f"Searching for term: '{term}' on page {page.number+1}")
                quads = page.search_for(term, quads=True)
                for quad in quads:
                    annot = page.add_highlight_annot(quad)
                    annot.set_colors(stroke=HIGHLIGHT_COLOR)
                    annot.set_opacity(0.6)
                    annot.update()
                    highlights_added = True
        
        # Save the highlighted PDF
        logger.info(f"Saving highlighted PDF to: {output_path}")
        doc.save(output_path)
        doc.close()
        
        if highlights_added:
            logger.info("Highlights added successfully")
        else:
            logger.warning("No highlights were added to the PDF")
            
    except Exception as e:
        logger.error(f"Error in _add_highlights: {str(e)}")
        raise
