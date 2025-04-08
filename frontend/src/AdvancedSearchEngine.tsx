"use client"

import type React from "react"
import { useState } from "react"
import { toast } from "sonner"
import SearchForm from "./components/SearchForm"
import SearchResultCard from "./components/SearchResultCard"
import PDFViewer from "./components/PDFViewer"
import IslandLayout from "./components/IslandLayout"
import { searchDocuments } from "./api"
import type { DocumentSearchResult } from "./interfaces"
import "./styles/scrollbar.css"

const AdvancedSearchEngine: React.FC = () => {
  const [searchResults, setSearchResults] = useState<DocumentSearchResult[]>([])
  const [selectedPDF, setSelectedPDF] = useState<string | null>(null)
  const [selectedCardId, setSelectedCardId] = useState<number | null>(null)
  const [currentPageNumber, setCurrentPageNumber] = useState<number | null>(null)
  const [selectedHighlightedId, setSelectedHighlightedId] = useState<number | null>(null)
  const [loading, setLoading] = useState<boolean>(false)

  const handleSearch = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoading(true)
    const formData = new FormData(event.currentTarget)
    const query = formData.get("search") as string
    const country = formData.get("country") as string
    const organization = formData.get("organization") as string
    const region = formData.get("region") as string

    try {
      const results = await searchDocuments(query, country, organization, region)
      setSearchResults(results)
      if (results.length > 0) {
        const topResult = results[0]
        if (topResult.metadata.highlighted_pdf_url) {
          setSelectedPDF(topResult.metadata.highlighted_pdf_url)
        } else {
          setSelectedPDF(topResult.metadata.pdf_url ?? null)
        }
        setSelectedCardId(topResult.metadata.id)
        if (topResult.matches.length > 0) {
          setCurrentPageNumber(topResult.matches[0].page_number)
          setSelectedHighlightedId(topResult.matches[0].rank)
        }
      }
    } catch (error: any) {
      if (error instanceof Error) {
        toast(error.message, {
          description: "Please try again or reach out to support at surveyaccelerator@idinsight.org",
          duration: 4500,
        })
      } else {
        toast("An unknown error occurred.", {
          description: "Please try again.",
          duration: 4000,
        })
      }
    } finally {
      setLoading(false)
    }
  }

  const handleCardClick = (result: DocumentSearchResult) => {
    if (result.metadata.highlighted_pdf_url) {
      setSelectedPDF(result.metadata.highlighted_pdf_url)
    } else {
      setSelectedPDF(result.metadata.pdf_url ?? null)
    }
    setSelectedCardId(result.metadata.id)
    setCurrentPageNumber(null)
    setSelectedHighlightedId(null)
    if (result.matches.length > 0) {
      setCurrentPageNumber(result.matches[0].page_number)
      setSelectedHighlightedId(result.matches[0].rank)
    }
  }

  const handleMatchClick = (pageNumber: number, matchId: number) => {
    setCurrentPageNumber(pageNumber)
    setSelectedHighlightedId(matchId)
  }

  return (
    <IslandLayout>
      <div className="grid grid-cols-[28%_72%] h-screen">
        {/* Left Panel */}
        <div className="p-6 overflow-y-auto custom-scrollbar">
          <div className="mb-6">
            <img
              src="/SurveyAcceleratorLogo-White.svg"
              alt="Banner"
              className="w-full h-auto object-cover mb-4 rounded-lg"
            />
            {/* Search form with glass effect */}
            <div className="bg-black/30 backdrop-blur-sm rounded-lg p-4 mb-6">
              <SearchForm onSubmit={handleSearch} loading={loading} />
            </div>
          </div>

          {/* Search results without glass effect */}
          <div>
            {searchResults.length > 0 && <h3 className="text-xl font-semibold text-white mb-3">Search Results:</h3>}
            {searchResults.map((result) => (
              <SearchResultCard
                key={result.metadata.id}
                result={result}
                onClick={handleCardClick}
                isSelected={selectedCardId === result.metadata.id}
                onMatchClick={handleMatchClick}
                selectedHighlightedId={selectedHighlightedId}
              />
            ))}
          </div>
        </div>

        {/* Right Panel - PDF Viewer Only */}
        <div className="relative flex flex-col h-full overflow-hidden p-4">
          <div className="relative flex-grow min-h-0 overflow-hidden rounded-lg">
            <PDFViewer
              key={`${selectedPDF}-${currentPageNumber}`}
              pdfUrl={selectedPDF || ""}
              pageNumber={currentPageNumber || undefined}
            />
          </div>
        </div>
      </div>
    </IslandLayout>
  )
}

export default AdvancedSearchEngine
