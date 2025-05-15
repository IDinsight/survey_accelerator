"use client";

import { useMemo, useState, useEffect } from "react";

interface PDFViewerProps {
  // A fully constructed PDF URL returned by the backend
  pdfUrl: string;
  // Optionally, the page number to display
  pageNumber?: number;
}

const PDFViewer: React.FC<PDFViewerProps> = ({ pdfUrl, pageNumber }) => {
  const exampleQueries = [
    "child mortality rates",
    "vaccination coverage",
    "maternal health indicators",
    "school enrollment statistics",
    "agricultural productivity",
    "clean water access",
    "gender equality metrics",
    "community health programs",
  ];

  const [currentQueryIndex, setCurrentQueryIndex] = useState(0);
  const [nextQueryIndex, setNextQueryIndex] = useState(1);
  const [animationState, setAnimationState] = useState("idle"); // "idle" | "animating"

  // Rotate through example queries with sliding animation
  useEffect(() => {
    const queryDisplayTime = 2500; // Change frequency: every 2.5 seconds
    const animationDuration = 1800; // Keep the same slow, smooth animation duration

    const rotationInterval = setInterval(() => {
      // Start the animation
      setAnimationState("animating");

      // After animation completes, update indices and reset animation state
      setTimeout(() => {
        setCurrentQueryIndex(nextQueryIndex);
        setNextQueryIndex((nextQueryIndex + 1) % exampleQueries.length);
        setAnimationState("idle");
      }, animationDuration);

    }, queryDisplayTime);

    return () => clearInterval(rotationInterval);
  }, [nextQueryIndex, exampleQueries.length]);

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
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <p className="text-white text-center text-3xl font-inter mb-4">
            Try searching for:
          </p>
          {/* Outer wrapper with mask to clip content outside boundaries */}
          <div
            className="relative h-16 w-full"
            style={{
              maskImage: 'linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%)',
              WebkitMaskImage: 'linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%)'
            }}
          >
            {/* Inner animation container */}
            <div className="relative h-full w-full overflow-hidden">
              <div className="absolute inset-0 flex items-center justify-center">
                {/* Current query - visible and slides down and out when animating */}
                <div
                  key={`current-${currentQueryIndex}`}
                  className={`absolute text-white text-center transition-transform duration-[1800ms] ease-in-out ${
                    animationState === "animating" ? 'transform translate-y-[130%]' : 'transform translate-y-0'
                  }`}
                >
                  <p className="text-4xl font-bold font-inter">{exampleQueries[currentQueryIndex]}</p>
                </div>

                {/* Next query that slides in from above */}
                <div
                  key={`next-${nextQueryIndex}`}
                  className={`absolute text-white text-center transition-transform duration-[1800ms] ease-in-out ${
                    animationState === "animating" ? 'transform translate-y-0' : 'transform -translate-y-[130%]'
                  }`}
                >
                  <p className="text-4xl font-bold font-inter">{exampleQueries[nextQueryIndex]}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PDFViewer;
