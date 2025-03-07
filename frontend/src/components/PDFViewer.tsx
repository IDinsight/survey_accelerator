import React from 'react';

interface PDFViewerProps {
  pdfUrl: string;
  pageNumber?: number;
}

const PDFViewer: React.FC<PDFViewerProps> = ({ pdfUrl, pageNumber }) => {
  // Process the PDF URL to ensure we're using the highlighted PDF from backend
  const processedUrl = React.useMemo(() => {
    if (!pdfUrl) return '';
    
    // Is this a highlighted PDF URL?
    const isHighlightedPdf = pdfUrl.includes('/highlighted_pdfs/');
    
    // Backend URL (hardcoded for reliability)
    const backendUrl = 'http://localhost:8000';
    
    let fullUrl;
    if (isHighlightedPdf) {
      // For highlighted PDFs, always use the backend URL
      const cleanPath = pdfUrl.startsWith('/') ? pdfUrl.substring(1) : pdfUrl;
      fullUrl = `${backendUrl}/${cleanPath}`;
    } else {
      // For regular PDFs (from cloud storage), use as is
      fullUrl = pdfUrl;
    }
    
    // Add page number if provided
    return pageNumber ? `${fullUrl}#page=${pageNumber}` : fullUrl;
  }, [pdfUrl, pageNumber]);

  return (
    <div className="w-full h-full relative">
      {pdfUrl ? (
        <object
          key={`pdf-${pdfUrl}-${pageNumber || 'default'}`}
          data={processedUrl}
          type="application/pdf"
          className="w-full h-full"
          style={{ border: 'none', display: 'block' }}
        >
          <div className="w-full h-full flex items-center justify-center bg-gray-100 p-4">
            <p>Unable to display PDF.</p>
          </div>
        </object>
      ) : (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-500">Select a document to view.</p>
        </div>
      )}
    </div>
  );
};

export default PDFViewer;