import React, { useRef, useEffect, useState } from 'react';

interface PDFJSSimpleViewerProps {
  pdfUrl: string;
  pageNumber?: number;
  searchText?: string;
}

/**
 * A simplified PDF viewer for pre-highlighted PDFs.
 * This component works with PDFs that have highlights already added by the backend.
 */
const PDFJSSimpleViewer: React.FC<PDFJSSimpleViewerProps> = ({ pdfUrl, pageNumber = 1 }) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(pageNumber);
  
  // Load the PDF viewer with the pre-highlighted PDF
  useEffect(() => {
    if (!pdfUrl) return;
    
    console.log("Loading PDF viewer with pre-highlighted PDF");
    setIsLoading(true);
    setError(null);
    
    try {
      const iframe = iframeRef.current;
      if (!iframe) return;
      
      // Check if the PDF URL is a relative URL
      // If so, use the full backend URL
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
      const fullPdfUrl = pdfUrl.startsWith('http') ? pdfUrl : `${backendUrl}${pdfUrl}`;
      
      // Just navigate to the specified page - no search parameters needed
      // since the highlights are already in the PDF
      const viewerUrl = `https://mozilla.github.io/pdf.js/web/viewer.html?file=${encodeURIComponent(fullPdfUrl)}#page=${pageNumber}`;
      
      console.log("Loading PDF viewer with URL:", viewerUrl);
      console.log("Full PDF URL:", fullPdfUrl);
      iframe.src = viewerUrl;
      
      // Handle load event
      const handleLoad = () => {
        console.log("PDF viewer loaded");
        setIsLoading(false);
        setCurrentPage(pageNumber);
      };
      
      // Handle error event
      const handleError = () => {
        console.error("Failed to load PDF viewer");
        setError('Failed to load PDF viewer');
        setIsLoading(false);
      };
      
      iframe.addEventListener('load', handleLoad);
      iframe.addEventListener('error', handleError);
      
      return () => {
        iframe.removeEventListener('load', handleLoad);
        iframe.removeEventListener('error', handleError);
      };
    } catch (err) {
      console.error('Error setting up PDF viewer:', err);
      setError('Failed to initialize PDF viewer');
      setIsLoading(false);
    }
  }, [pdfUrl]); // Only rerun when PDF URL changes
  
  // Handle page navigation
  useEffect(() => {
    if (!iframeRef.current || !pdfUrl || isLoading) return;
    
    if (pageNumber !== currentPage) {
      console.log(`Navigating to page ${pageNumber}`);
      
      try {
        const iframe = iframeRef.current;
        
        // Use the full backend URL for relative paths
        const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
        const fullPdfUrl = pdfUrl.startsWith('http') ? pdfUrl : `${backendUrl}${pdfUrl}`;
        
        // Update only the page number in the hash
        const viewerUrl = `https://mozilla.github.io/pdf.js/web/viewer.html?file=${encodeURIComponent(fullPdfUrl)}#page=${pageNumber}`;
        iframe.src = viewerUrl;
        
        setCurrentPage(pageNumber);
      } catch (err) {
        console.error('Error navigating to page:', err);
      }
    }
  }, [pageNumber, pdfUrl, isLoading, currentPage]);
  
  // Page navigation controls
  const navigateToPage = (direction: 'prev' | 'next') => {
    const newPage = direction === 'prev' ? Math.max(1, currentPage - 1) : currentPage + 1;
    setCurrentPage(newPage);
    
    if (iframeRef.current) {
      // Use the full backend URL for relative paths
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
      const fullPdfUrl = pdfUrl.startsWith('http') ? pdfUrl : `${backendUrl}${pdfUrl}`;
      
      const viewerUrl = `https://mozilla.github.io/pdf.js/web/viewer.html?file=${encodeURIComponent(fullPdfUrl)}#page=${newPage}`;
      iframeRef.current.src = viewerUrl;
    }
  };
  
  return (
    <div className="w-full h-full relative">
      {/* Empty state */}
      {!pdfUrl && (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-500">Select a document to view.</p>
        </div>
      )}

      {/* Loading indicator */}
      {isLoading && pdfUrl && (
        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-80 z-30">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mb-2"></div>
            <p>Loading pre-highlighted PDF...</p>
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90 z-30">
          <div className="bg-red-100 text-red-700 p-4 rounded-lg shadow-lg">
            <p className="font-bold">Error</p>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* PDF.js viewer iframe */}
      <iframe
        ref={iframeRef}
        className="w-full h-full border-0"
        title="PDF Viewer"
        style={{
          display: pdfUrl ? 'block' : 'none',
          backgroundColor: '#f8f9fa'
        }}
      />

      {/* Page navigation controls */}
      <div className="absolute bottom-2 right-2 bg-white rounded-lg shadow-md p-1 flex items-center">
        <button 
          onClick={() => navigateToPage('prev')}
          className="bg-blue-500 text-white px-3 py-1 rounded-l-md hover:bg-blue-600"
          disabled={currentPage <= 1}
        >
          ← Prev
        </button>
        <span className="px-3">Page {currentPage}</span>
        <button 
          onClick={() => navigateToPage('next')}
          className="bg-blue-500 text-white px-3 py-1 rounded-r-md hover:bg-blue-600"
        >
          Next →
        </button>
      </div>
      
      {/* Information display */}
      <div className="absolute bottom-2 left-2 text-xs font-semibold bg-yellow-100 text-yellow-800 px-2 py-1 rounded shadow-sm">
        Viewing pre-highlighted PDF (highlights added by backend)
      </div>
    </div>
  );
};

export default PDFJSSimpleViewer;
