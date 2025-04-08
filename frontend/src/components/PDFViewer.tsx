"use client"

import { type FC, useMemo } from "react"

interface PDFViewerProps {
  pdfUrl: string
  pageNumber?: number
}

const PDFViewer: FC<PDFViewerProps> = ({ pdfUrl, pageNumber }) => {
  // Process the PDF URL
  const processedUrl = useMemo(() => {
    if (!pdfUrl) return ""
    const isHighlightedPdf = pdfUrl.includes("/highlighted_pdfs/")
    const backendUrl = "http://localhost:8000"
    let fullUrl
    if (isHighlightedPdf) {
      const cleanPath = pdfUrl.startsWith("/") ? pdfUrl.substring(1) : pdfUrl
      fullUrl = `${backendUrl}/${cleanPath}`
    } else {
      fullUrl = pdfUrl
    }
    return pageNumber ? `${fullUrl}#page=${pageNumber}` : fullUrl
  }, [pdfUrl, pageNumber])

  return (
    <div className="relative w-full h-full rounded-lg overflow-hidden">
      {pdfUrl ? (
        // When there's a PDF to display, show it with a glass effect
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
        // When there's no PDF, just show the text directly on the background
        <div className="absolute inset-0 flex items-center justify-center">
          <p className="text-white text-center leading-7">
            Enter a query in the left panel to search.
            <br />
            PDF previews with highlights tailored to your search will then be shown here.
          </p>
        </div>
      )}
    </div>
  )
}

export default PDFViewer
