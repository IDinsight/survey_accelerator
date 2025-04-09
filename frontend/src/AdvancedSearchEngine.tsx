"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { toast } from "sonner"
import SearchForm from "./components/SearchForm"
import SearchResultCard from "./components/SearchResultCard"
import PDFViewer from "./components/PDFViewer"
import IslandLayout from "./components/IslandLayout"
import SettingsPopup from "./components/SettingsPopup"
import FAQModal from "./components/FAQModal"
import { searchDocuments } from "./api"
import type { DocumentSearchResult } from "./interfaces"
import { getMatchStrength } from "./interfaces"
import { LogOut, Settings, HelpCircle } from "lucide-react"
import { Button } from "./components/ui/button"
import "./styles/scrollbar.css"
import "./styles/dropdown.css"

interface User {
  email: string
  user_id: number
}

interface AdvancedSearchEngineProps {
  onLogout?: () => void
  user?: User | null
}

const AdvancedSearchEngine: React.FC<AdvancedSearchEngineProps> = ({ onLogout, user }) => {
  const [searchResults, setSearchResults] = useState<DocumentSearchResult[]>([])
  const [selectedPDF, setSelectedPDF] = useState<string | null>(null)
  const [selectedCardId, setSelectedCardId] = useState<number | null>(null)
  const [currentPageNumber, setCurrentPageNumber] = useState<number | null>(null)
  const [selectedHighlightedId, setSelectedHighlightedId] = useState<number | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [showSettings, setShowSettings] = useState(false)
  const [showFAQ, setShowFAQ] = useState(false)
  const [resultsCount, setResultsCount] = useState(25) // Default to 25 results

  // Load saved preferences on component mount
  useEffect(() => {
    const savedResultsCount = localStorage.getItem("resultsCount")
    if (savedResultsCount) {
      setResultsCount(Number.parseInt(savedResultsCount, 10))
    }
  }, [])

  const handleSearch = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoading(true)
    const formData = new FormData(event.currentTarget)
    const query = formData.get("search") as string

    // Parse the JSON strings from hidden inputs
    let organizations: string[] = []
    let survey_types: string[] = []

    try {
      const orgsJson = formData.get("organizations") as string
      if (orgsJson) {
        organizations = JSON.parse(orgsJson)
      }

      const typesJson = formData.get("survey_types") as string
      if (typesJson) {
        survey_types = JSON.parse(typesJson)
      }
    } catch (error) {
      console.error("Error parsing form data:", error)
    }

    try {
      // Call the API with the correct parameters
      const results = await searchDocuments(query, organizations, survey_types)

      // Sort results by number of strong matches
      const sortedResults = results
        .map((result: DocumentSearchResult) => {
          // Count strong matches
          const strongMatchesCount = result.matches.filter((match) => getMatchStrength(match.rank) === "strong").length

          return {
            ...result,
            strongMatchesCount,
          }
        })
        .sort(
          (
            a: DocumentSearchResult & { strongMatchesCount: number },
            b: DocumentSearchResult & { strongMatchesCount: number },
          ) => b.strongMatchesCount - a.strongMatchesCount,
        )

      setSearchResults(sortedResults)

      // Don't set any PDF or selection states - wait for user to select a card
      setSelectedPDF(null)
      setSelectedCardId(null)
      setCurrentPageNumber(null)
      setSelectedHighlightedId(null)
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

  const handleUpdateResultsCount = (count: number) => {
    setResultsCount(count)
    localStorage.setItem("resultsCount", count.toString())
    // If you want to store in DB, you would make an API call here
  }

  // Create a default user object if none is provided
  const defaultUser = {
    email: localStorage.getItem("email") || "user@example.com",
    user_id: Number.parseInt(localStorage.getItem("user_id") || "0", 10),
  }

  // Default logout handler if none is provided
  const handleLogout = () => {
    if (onLogout) {
      onLogout()
    } else {
      // Default logout behavior
      localStorage.removeItem("token")
      localStorage.removeItem("user")
      localStorage.removeItem("email")
      localStorage.removeItem("user_id")
      // Redirect to login page
      window.location.href = "/login"
    }
  }

  return (
    <IslandLayout>
      {showSettings && (
        <SettingsPopup
          user={user || defaultUser}
          onClose={() => setShowSettings(false)}
          onUpdateResultsCount={handleUpdateResultsCount}
          resultsCount={resultsCount}
        />
      )}

      <FAQModal isOpen={showFAQ} onClose={() => setShowFAQ(false)} />

      <div className="grid grid-cols-[28%_72%] h-screen">
        {/* Left Panel */}
        <div className="p-6 overflow-y-auto custom-scrollbar">
          <div className="mb-2">
            {/* Logo and icons in a single row */}
            <div className="flex flex-col mb-2">
              {/* Full-width logo */}
              <div className="w-full mb-1">
                <img
                  src="/SurveyAcceleratorLogo-White.svg"
                  alt="Survey Accelerator"
                  className="w-full h-auto object-contain"
                />
              </div>

              {/* Icons row - very compact */}
              <div className="flex justify-end">
                <div className="flex gap-1">
                  <Button
                    onClick={() => setShowFAQ(true)}
                    variant="ghost"
                    size="sm"
                    className="text-white hover:bg-white/10 h-7 w-7 p-0"
                    title="Help"
                  >
                    <HelpCircle className="h-4 w-4" />
                  </Button>
                  <Button
                    onClick={() => setShowSettings(true)}
                    variant="ghost"
                    size="sm"
                    className="text-white hover:bg-white/10 h-7 w-7 p-0"
                    title="Settings"
                  >
                    <Settings className="h-4 w-4" />
                  </Button>
                  <Button
                    onClick={handleLogout}
                    variant="ghost"
                    size="sm"
                    className="text-white hover:bg-white/10 h-7 w-7 p-0"
                    title="Logout"
                  >
                    <LogOut className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Search form with glass effect */}
            <div className="bg-black/30 backdrop-blur-sm rounded-lg p-4 search-form-container">
              <SearchForm onSubmit={handleSearch} loading={loading} />
            </div>
          </div>

          {/* Search results without glass effect */}
          <div className="results-container">
            {searchResults.length > 0 && <h3 className="text-xl font-semibold text-white mb-2 text-center">Results</h3>}
            <div className="space-y-3">
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
