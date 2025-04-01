import React, { FC, useMemo } from "react";
import Particles from "react-tsparticles";
interface PDFViewerProps {
  pdfUrl: string;
  pageNumber?: number;
}

const PDFViewer: FC<PDFViewerProps> = ({ pdfUrl, pageNumber }) => {
  // Process the PDF URL
  const processedUrl = useMemo(() => {
    if (!pdfUrl) return "";
    const isHighlightedPdf = pdfUrl.includes("/highlighted_pdfs/");
    const backendUrl = "http://localhost:8000";
    let fullUrl;
    if (isHighlightedPdf) {
      const cleanPath = pdfUrl.startsWith("/") ? pdfUrl.substring(1) : pdfUrl;
      fullUrl = `${backendUrl}/${cleanPath}`;
    } else {
      fullUrl = pdfUrl;
    }
    return pageNumber ? `${fullUrl}#page=${pageNumber}` : fullUrl;
  }, [pdfUrl, pageNumber]);

  // Triangles configuration adapted from your sample preset
  const trianglesOptions = {
    fullScreen: { enable: false, zIndex: -1 },
    fpsLimit: 60,
    particles: {
      number: { value: 30 },
      shape: { type: "circle" },
      opacity: { value: 0.5 },
      size: { value: { min: 1, max: 3 } },
      links: {
        enable: true,
        distance: 100,
        color: "random",
        opacity: 0.4,
        width: 1,
        triangles: { enable: true, color: "#ffffff", opacity: 0.1 },
      },
      move: {
        enable: true,
        speed: 0.9,
        direction: "none" as const,
        outModes: "out" as const
      },
    },
    background: { color: "#000000" },
    retina_detect: true,
  };

  return (
    <div className="relative w-full h-full">
      {pdfUrl ? (
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
      ) : (
      <>
        <div className="absolute inset-0 bg-gray-900 opacity-50" />
          <Particles
            id="tsparticles"
            options={trianglesOptions}
            style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%" }}
          />
          {/* Background overlay */}
          <div className="absolute inset-0 bg-gray-900 opacity-50" />
          {/* Overlay message */}
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-white text-center leading-7">
              Enter a query in the left panel to search.
              <br />
              PDF previews with highlights tailored to your search will then be shown here.
            </p>
          </div>
        </>
      )}
    </div>
  );
};

export default PDFViewer;
