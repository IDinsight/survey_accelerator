// src/components/PDFViewer.tsx

import React, { useState, useEffect, useRef } from 'react';
import {
  PdfLoader,
  PdfHighlighter,
  Highlight,
  Popup,
  AreaHighlight,
  Tip
} from 'react-pdf-highlighter';
import type { IHighlight } from 'react-pdf-highlighter';
import "react-pdf-highlighter/dist/style.css";

interface PDFViewerProps {
  pdfUrl: string;
  pageNumber?: number;
  highlightText?: string;
}

const getNextId = () => String(Math.random()).slice(2);

const PDFViewer: React.FC<PDFViewerProps> = ({ pdfUrl, pageNumber, highlightText }) => {
  const [highlights, setHighlights] = useState<Array<IHighlight>>([]);
  const scrollViewerTo = useRef<(highlight: IHighlight) => void>(() => {});

  // Enhanced popup component
  const HighlightPopup = ({ comment, content }: {
    comment: { text: string; emoji: string },
    content?: { text?: string; image?: string }
  }) => {
    const hasComment = comment && comment.text;
    const hasText = content && content.text;

    if (!hasComment && !hasText) return null;

    return (
      <div className="bg-white shadow-lg rounded p-3 border border-gray-200 max-w-lg">
        {hasComment && (
          <div className="mb-2 font-bold text-blue-800">
            {comment.emoji} {comment.text}
          </div>
        )}
        {hasText && (
          <div className="text-gray-700">
            {content.text}
          </div>
        )}
      </div>
    );
  };

  // Add a new highlight when user selects text
  const addHighlight = (highlight: any) => {
    setHighlights([{ ...highlight, id: getNextId() }, ...highlights]);
  };

  // Based on examples, when a highlight is created by selecting text,
  // the library automatically handles the positioning
  const addHighlightFromSearch = (content: any, position: any) => {
    const highlight = {
      content,
      position,
      comment: {
        text: 'Search result',
        emoji: '🔍'
      }
    };

    // Add the highlight
    const newHighlight = { ...highlight, id: `search-${Date.now()}` };
    setHighlights([newHighlight]);

    // Schedule scrolling to the highlight after it's rendered
    setTimeout(() => {
      if (scrollViewerTo.current) {
        scrollViewerTo.current(newHighlight);
      }
    }, 200);
  };

  // Track document changes
  const previousUrlRef = useRef<string | null>(null);
  // Track current page for navigation
  const currentPageRef = useRef<number | undefined>(undefined);
  // Zoom level state - start with a lower scale (zoomed out)
  const [scale, setScale] = useState<number>(0.8);

  // Simple page navigation - just navigate to the specified page
  useEffect(() => {
    // When document changes, reset
    if (pdfUrl !== previousUrlRef.current) {
      console.log(`New document loaded: ${pdfUrl}`);
      setHighlights([]); // Clear highlights
      previousUrlRef.current = pdfUrl;
      currentPageRef.current = undefined;
    }

    // When page number changes, create a simple navigation highlight
    if (pdfUrl && pageNumber && (pageNumber !== currentPageRef.current)) {
      console.log(`Navigating to page ${pageNumber}`);
      currentPageRef.current = pageNumber;

      // Create a simple page reference for navigation
      const pageNavHighlight: IHighlight = {
        id: `page-${pageNumber}-${Date.now()}`,
        content: { text: "" },
        position: {
          boundingRect: {
            x1: 0,
            y1: 0,
            x2: 100,
            y2: 50,
            width: 100,
            height: 50,
            pageNumber
          },
          rects: [],
          pageNumber
        },
        comment: { text: "", emoji: "" }
      };

      // Set this as the only highlight
      setHighlights([pageNavHighlight]);

      // After a delay, navigate to the page
      setTimeout(() => {
        if (scrollViewerTo.current) {
          scrollViewerTo.current(pageNavHighlight);
        }
      }, 100);
    }
  }, [pdfUrl, pageNumber]);

  // Update an existing highlight (for area highlights)
  function updateHighlight(
    highlightId: string,
    position: any,
    content: any
  ) {
    setHighlights(
      highlights.map((h) => {
        const { id, position: originalPosition, content: originalContent, ...rest } = h;
        return id === highlightId
          ? {
              id,
              position: { ...originalPosition, ...position },
              content: { ...originalContent, ...content },
              ...rest,
            }
          : h;
      })
    );
  }

  if (!pdfUrl) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500">Select a document to view.</p>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative">
      {/* Zoom controls */}
      <div className="absolute top-0 right-0 z-20 bg-white p-1 rounded-bl shadow-md flex items-center">
        <button
          className="bg-blue-500 text-white font-bold px-2 rounded hover:bg-blue-600 mr-1"
          onClick={() => setScale(prevScale => Math.max(0.5, prevScale - 0.1))}
        >
          −
        </button>
        <span className="text-xs mx-1">{Math.round(scale * 100)}%</span>
        <button
          className="bg-blue-500 text-white font-bold px-2 rounded hover:bg-blue-600 ml-1"
          onClick={() => setScale(prevScale => Math.min(2.0, prevScale + 0.1))}
        >
          +
        </button>
      </div>

      {/* Page indicator */}
      <div className="absolute bottom-0 right-0 z-20 bg-white p-1 rounded-tl shadow-md">
        <span className="text-xs font-medium">Page {pageNumber || '?'}</span>
      </div>

      {/* Simplified information banner */}
      {highlightText && (
        <div className="absolute top-0 left-0 right-0 z-10 bg-blue-100 text-blue-800 p-1 shadow-md flex items-center">
          <div className="text-xs">
            <span className="font-bold">Page {pageNumber}:</span> Search for "{highlightText.substring(0, 40)}{highlightText.length > 40 ? '...' : ''}"
          </div>
          <button
            className="bg-blue-500 text-white px-2 py-1 rounded text-xs hover:bg-blue-600 ml-auto"
            onClick={() => document.execCommand('find')}
          >
            Find (Ctrl+F)
          </button>
        </div>
      )}

      <PdfLoader
        url={pdfUrl}
        beforeLoad={<div className="flex justify-center items-center h-full"><p>Loading PDF...</p></div>}
      >
        {(pdfDocument) => (
          <PdfHighlighter
            pdfDocument={pdfDocument}
            enableAreaSelection={(event) => event.altKey}
            onScrollChange={() => {}}
            scrollRef={(scrollTo) => {
              // Just store the scroll function for later use
              scrollViewerTo.current = scrollTo;
              console.log("Scroll function received and stored");
            }}
            // Apply the zoom scale to the viewer - convert to string as required by the component
            pdfScaleValue={scale.toString()}
            onSelectionFinished={(
              position,
              content,
              hideTipAndSelection,
              transformSelection
            ) => (
              <Tip
                onOpen={transformSelection}
                onConfirm={(comment) => {
                  addHighlight({ content, position, comment });
                  hideTipAndSelection();
                }}
              />
            )}
            highlightTransform={(
              highlight,
              index,
              setTip,
              hideTip,
              viewportToScaled,
              screenshot,
              isScrolledTo
            ) => {
              const isTextHighlight = !highlight.content?.image;

              const component = isTextHighlight ? (
                <Highlight
                  isScrolledTo={isScrolledTo}
                  position={highlight.position}
                  comment={highlight.comment}
                />
              ) : (
                <AreaHighlight
                  isScrolledTo={isScrolledTo}
                  highlight={highlight}
                  onChange={(boundingRect) => {
                    updateHighlight(
                      highlight.id,
                      { boundingRect: viewportToScaled(boundingRect) },
                      { image: screenshot(boundingRect) }
                    );
                  }}
                />
              );

              return (
                <Popup
                  popupContent={<HighlightPopup comment={highlight.comment} content={highlight.content} />}
                  onMouseOver={(popupContent) =>
                    setTip(highlight, () => popupContent)
                  }
                  onMouseOut={hideTip}
                  key={index}
                >
                  {component}
                </Popup>
              );
            }}
            highlights={highlights}
          />
        )}
      </PdfLoader>
    </div>
  );
};

export default PDFViewer;
