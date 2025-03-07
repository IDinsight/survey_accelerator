"""Utilities for highlighting PDF documents based on search terms."""

import asyncio
import hashlib
import json
import os
import tempfile
from typing import Dict, List, Optional

import aiohttp
import fitz
from app.utils import setup_logger
from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles

logger = setup_logger()

# Directory to store highlighted PDFs
HIGHLIGHT_DIR = os.environ.get("HIGHLIGHT_DIR", "./highlighted_pdfs")
os.makedirs(HIGHLIGHT_DIR, exist_ok=True)

# Highlight color (RGB values as a tuple)
HIGHLIGHT_COLOR = (1, 0.8, 0.2)  # Yellow-orange

# Cache to track PDFs currently being processed
processing_pdfs: Dict[str, asyncio.Task] = {}


async def get_highlighted_pdf(
    pdf_url: str,
    search_term: str,
    bucket_url_prefix: Optional[str] = None,
    page_keywords: Optional[Dict[int, List[str]]] = None,
) -> str:
    """
    Get URL to a highlighted version of a PDF.
    If the highlighted PDF doesn't exist, create it first.

    Args:
        pdf_url: URL to the original PDF
        search_term: Text to highlight in the PDF (used as fallback)
        bucket_url_prefix: Optional URL prefix for cloud storage bucket
        page_keywords: Optional dict mapping page numbers to keywords to highlight on that page

    Returns:
        URL to the highlighted PDF
    """
    # Create a unique filename based on the PDF URL and search data
    # If we have page-specific keywords, include them in the cache key
    if page_keywords:
        # Convert page_keywords dict to a stable string representation
        page_keywords_str = json.dumps(page_keywords, sort_keys=True)
        cache_key = (
            f"{pdf_url}_paged_{hashlib.md5(page_keywords_str.encode()).hexdigest()}"
        )
    else:
        cache_key = f"{pdf_url}_{search_term}"

    pdf_filename = hashlib.md5(cache_key.encode()).hexdigest() + ".pdf"
    highlighted_path = os.path.join(HIGHLIGHT_DIR, pdf_filename)

    # Check if the highlighted PDF already exists
    if os.path.exists(highlighted_path):
        logger.info(f"Found pre-highlighted PDF for {pdf_url}")
        return (
            f"/highlighted_pdfs/{pdf_filename}"
            if not bucket_url_prefix
            else f"{bucket_url_prefix}/{pdf_filename}"
        )

    # Check if this PDF is already being processed
    if cache_key in processing_pdfs and not processing_pdfs[cache_key].done():
        logger.info(f"Waiting for highlighting of {pdf_url} to complete")
        # Wait for the existing process to finish
        try:
            await processing_pdfs[cache_key]
        except Exception as e:
            logger.error(f"Error waiting for PDF processing: {e}")
            # Continue to reprocess since the previous attempt failed

    # Start processing the PDF
    task = asyncio.create_task(
        _process_and_highlight_pdf(
            pdf_url, search_term, highlighted_path, page_keywords
        )
    )
    processing_pdfs[cache_key] = task

    try:
        # Wait for the task to complete
        await task
        logger.info(f"Successfully created highlighted PDF for {pdf_url}")
        return (
            f"/highlighted_pdfs/{pdf_filename}"
            if not bucket_url_prefix
            else f"{bucket_url_prefix}/{pdf_filename}"
        )
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

    Args:
        pdf_url: URL to the PDF to download
        search_term: Term to highlight in the PDF (used as fallback)
        output_path: Path where the highlighted PDF should be saved
        page_keywords: Optional dict mapping page numbers to keywords to highlight on that page
    """
    # Create a temporary file for the downloaded PDF
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        # Download the PDF
        logger.info(f"Downloading PDF from {pdf_url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(pdf_url) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Failed to download PDF: HTTP {response.status}",
                    )

                # Write the PDF to the temporary file
                with open(temp_path, "wb") as f:
                    f.write(await response.read())

        # Add highlights, using page-specific keywords if available
        if page_keywords and len(page_keywords) > 0:
            logger.info("Adding page-specific highlights to PDF")
            _add_page_specific_highlights(temp_path, output_path, page_keywords)
        else:
            # Fall back to using the search term for all pages
            logger.info(
                f"Adding highlights for term '{search_term}' to PDF (all pages)"
            )
            _add_highlights(temp_path, output_path, search_term)

    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def _add_page_specific_highlights(
    input_path: str, output_path: str, page_keywords: Dict[int, List[str]]
) -> None:
    """
    Add highlights to specific pages of a PDF based on provided keywords.

    Args:
        input_path: Path to the original PDF
        output_path: Path where the highlighted PDF should be saved
        page_keywords: Dict mapping page numbers to lists of keywords to highlight on that page
    """
    logger.info(f"Processing PDF {input_path} with page-specific highlights")
    logger.info(f"Page keywords: {page_keywords}")

    try:
        # Open the PDF document
        doc = fitz.open(input_path)

        # Track if any highlights were added
        highlights_added = False

        # Process each page that has keywords
        for page_num_str, keywords in page_keywords.items():
            try:
                # Convert page_num string to int
                page_num = int(page_num_str) - 1  # Convert from 1-indexed to 0-indexed

                # Skip if page number is out of bounds
                if page_num < 0 or page_num >= len(doc):
                    logger.warning(
                        f"Page number {page_num+1} is out of bounds for PDF with {len(doc)} pages"
                    )
                    continue

                # Get the page
                page = doc[page_num]
                page_highlights_count = 0

                # Process each keyword for this page
                for keyword in keywords:
                    if not keyword or len(keyword) < 2:
                        continue

                    # Search for the keyword (case-insensitive)
                    text_instances = page.search_for(keyword, quads=True)

                    # Skip if no matches found on this page for this keyword
                    if not text_instances:
                        continue

                    # Add highlights for each match
                    for quads in text_instances:
                        # Create a highlight annotation
                        highlight = page.add_highlight_annot(quads)

                        # Set the highlight color
                        highlight.set_colors(stroke=HIGHLIGHT_COLOR)

                        # Set highlight opacity/alpha
                        highlight.set_opacity(0.6)  # 60% opacity

                        # Update the annotation
                        highlight.update()

                        highlights_added = True
                        page_highlights_count += 1

                if page_highlights_count > 0:
                    logger.info(
                        f"Page {page_num+1}: Added {page_highlights_count} highlights for keywords {keywords}"
                    )

            except ValueError:
                logger.error(f"Invalid page number format: {page_num_str}")
                continue

        # Save the highlighted PDF
        if highlights_added:
            doc.save(output_path)
            logger.info(f"Saved highlighted PDF to {output_path}")
        else:
            # If no highlights were added, save a copy of the original file
            doc.save(output_path)
            logger.info(f"No highlights added, saved original PDF to {output_path}")

        # Close the document
        doc.close()

    except Exception as e:
        logger.error(f"Error adding page-specific highlights to PDF: {e}")
        raise Exception(f"Failed to add highlights: {str(e)}")


def _add_highlights(input_path: str, output_path: str, search_terms: str) -> None:
    """
    Add highlights to a PDF for all occurrences of search terms across all pages.

    Args:
        input_path: Path to the original PDF
        output_path: Path where the highlighted PDF should be saved
        search_terms: Comma-separated list of terms to highlight in the PDF
    """
    # Check if we have a comma-separated list of words or a single term
    if "," in search_terms:
        # Split by comma and strip whitespace
        terms_list = [term.strip() for term in search_terms.split(",")]
        logger.info(
            f"Processing PDF {input_path} to highlight multiple terms: {terms_list}"
        )
    else:
        # Handle as a single term for backward compatibility
        terms_list = [search_terms]
        logger.info(f"Processing PDF {input_path} to highlight term: '{search_terms}'")

    try:
        # Open the PDF document
        doc = fitz.open(input_path)

        # Track if any highlights were added
        highlights_added = False

        # Process each page
        for page_num, page in enumerate(doc):
            page_highlights_count = 0

            # Process each search term
            for term in terms_list:
                if not term or len(term) < 2:
                    continue

                # Search for the term (case-insensitive)
                # The 'quads' parameter returns quadrilaterals for more precise highlighting
                text_instances = page.search_for(term, quads=True)

                # Skip if no matches found on this page for this term
                if not text_instances:
                    continue

                # Add highlights for each match
                for quads in text_instances:
                    # Create a highlight annotation
                    highlight = page.add_highlight_annot(quads)

                    # Set the highlight color
                    highlight.set_colors(stroke=HIGHLIGHT_COLOR)

                    # Set highlight opacity/alpha
                    highlight.set_opacity(0.6)  # 60% opacity

                    # Update the annotation
                    highlight.update()

                    highlights_added = True
                    page_highlights_count += 1

            if page_highlights_count > 0:
                logger.info(
                    f"Page {page_num+1}: Added {page_highlights_count} highlights"
                )

        # Save the highlighted PDF if any highlights were added
        if highlights_added:
            doc.save(output_path)
            logger.info(f"Saved highlighted PDF to {output_path}")
        else:
            # If no highlights were added, save a copy of the original file
            doc.save(output_path)
            logger.info(f"No highlights added, saved original PDF to {output_path}")

        # Close the document
        doc.close()

    except Exception as e:
        logger.error(f"Error adding highlights to PDF: {e}")
        raise Exception(f"Failed to add highlights: {str(e)}")


def setup_static_file_serving(app):
    """
    Set up serving of highlighted PDFs as static files.

    Args:
        app: FastAPI app instance
    """
    # Mount the directory containing highlighted PDFs
    app.mount(
        "/highlighted_pdfs",
        StaticFiles(directory=HIGHLIGHT_DIR),
        name="highlighted_pdfs",
    )

    # Also serve the PDF viewer HTML file at the root
    import os

    # Copy the PDF viewer HTML file to the static directory if needed
    viewer_path = os.path.join(HIGHLIGHT_DIR, "pdf-viewer.html")
    if not os.path.exists(viewer_path):
        logger.info("Creating PDF viewer HTML file")
        with open(viewer_path, "w") as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Viewer</title>
    <style>
        body, html {
            margin: 0;
            padding: 0;
            height: 100%;
            overflow: hidden;
        }
        iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
    </style>
</head>
<body>
    <iframe id="pdfFrame" allowfullscreen></iframe>
    <script>
        // Parse URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const fileUrl = urlParams.get('file');
        const pageNum = urlParams.get('page');
        
        // Set up the iframe source
        if (fileUrl) {
            let viewerUrl = fileUrl;
            if (pageNum) {
                viewerUrl += `#page=${pageNum}`;
            }
            document.getElementById('pdfFrame').src = viewerUrl;
        } else {
            document.body.innerHTML = '<div style="padding: 20px; color: red;">Error: No PDF file specified</div>';
        }
    </script>
</body>
</html>""")

    logger.info("Mounted highlighted PDFs directory at /highlighted_pdfs")
