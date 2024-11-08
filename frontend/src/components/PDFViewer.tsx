import React from 'react';

interface PDFViewerProps {
  pdfUrl: string;
  pageNumber?: number;
}

const PDFViewer: React.FC<PDFViewerProps> = ({ pdfUrl, pageNumber }) => {
  const pdfWithPage = pageNumber ? `${pdfUrl}#page=${pageNumber}` : pdfUrl;

  return (
    <iframe
      src={pdfWithPage}
      width="100%"
      height="100%"
      style={{ border: 'none' }}
      title="PDF Viewer"
    />
  );
};

export default PDFViewer;
