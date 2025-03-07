import React, { useRef, useEffect, useState } from 'react';

interface PDFJSSimpleViewerProps {
  pdfUrl: string;
  pageNumber?: number;
  searchText?: string;
}

const PDFJSSimpleViewer: React.FC<PDFJSSimpleViewerProps> = ({ pdfUrl, pageNumber, searchText }) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load PDF with hard-coded settings
  useEffect(() => {
    console.log("Loading PDF viewer with hard-coded settings");
    setIsLoading(true);
    setError(null);

    try {
      const iframe = iframeRef.current;
      if (!iframe) return;

      // Hard-coded URL with exact PDF and search term
      // Using the format that works with your target PDF and search term
      const pdfUrl = 'https://storage.googleapis.com/survey_accelerator_dev_bucket/101_KIHBS%202015-16%20Q1C%20Consumption%20Expenditure%20Information.pdf';
      const hardCodedUrl = `https://mozilla.github.io/pdf.js/web/viewer.html?file=${encodeURIComponent(pdfUrl)}#page=1&search=pulses`;

      console.log("Loading PDF with hard-coded URL:", hardCodedUrl);

      // Set iframe src
      iframe.src = hardCodedUrl;

      // Handle load event
      const handleLoad = () => {
        console.log("PDF viewer loaded");
        setIsLoading(false);
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
  }, []); // Only run once on component mount

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
            <p>Loading PDF and searching for "pulses"...</p>
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

      {/* Search indicator */}
      <div className="absolute bottom-2 left-2 text-xs font-semibold bg-yellow-100 text-yellow-800 px-2 py-1 rounded shadow-sm">
        Always searching for: "pulses" on page 1
      </div>
    </div>
  );
};

export default PDFJSSimpleViewer;
