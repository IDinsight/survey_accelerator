// src/components/PDFViewer.tsx

import React from 'react';

interface PDFViewerProps {
  pdfUrl: string;
  pageNumber?: number;
  highlightText?: string; // Keep this for interface compatibility
}

const PDFViewer: React.FC<PDFViewerProps> = ({ pdfUrl, pageNumber }) => {
  // Simply append the page number to the URL if provided
  const src = pageNumber ? `${pdfUrl}#page=${pageNumber}` : pdfUrl;

  return (
    <div className="w-full h-full">
      {pdfUrl ? (
        <iframe
          key={`${pdfUrl}-page-${pageNumber}`} // Unique key to force re-render
          src={src}
          className="w-full h-full"
          title="PDF Viewer"
        />
      ) : (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-500">Select a document to view.</p>
        </div>
      )}
    </div>
  );
};

export default PDFViewer;
