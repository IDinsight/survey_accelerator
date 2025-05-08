"use client";

import { useMemo } from "react";

interface PDFViewerProps {
  // A fully constructed PDF URL returned by the backend
  pdfUrl: string;
  // Optionally, the page number to display
  pageNumber?: number;
}

const PDFViewer: React.FC<PDFViewerProps> = ({ pdfUrl, pageNumber }) => {
  const processedUrl = useMemo(() => {
    if (!pdfUrl) return "";
    // If a pageNumber is provided, append the page anchor to the provided URL.
    return pageNumber ? `${pdfUrl}#page=${pageNumber}` : pdfUrl;
  }, [pdfUrl, pageNumber]);

  return (
    <div className="relative w-full h-full rounded-lg overflow-hidden">
      {pdfUrl ? (
        <div className="w-full h-full bg-black/30 backdrop-blur-sm rounded-lg">
          <object
            key={`pdf-${pdfUrl}-${pageNumber || "default"}`}
            data={processedUrl}
            type="application/pdf"
            className="w-full h-full"
            style={{ border: "none", display: "block" }}
          >
            <div className="w-full h-full flex items-center justify-center bg-gray-100 p-4">
              <p>Unable to display PDF.</p>
            </div>
          </object>
        </div>
      ) : (
        <div className="absolute inset-0 flex items-center justify-center">
          <p className="text-white text-center leading-7">
            Enter a query in the left panel to search.
            <br />
            PDF previews with highlights tailored to your search will then be shown here.
          </p>
        </div>
      )}
    </div>
  );
};

export default PDFViewer;
