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
import ContributeSurveyModal from "./components/ContributeSurveyModal"
import { searchDocuments } from "./api"
import type { DocumentSearchResult } from "./interfaces"
import { getMatchStrength } from "./interfaces"
import { LogOut, Settings, HelpCircle, Upload } from "lucide-react"
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
  const [showContributeModal, setShowContributeModal] = useState(false)
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

      // Check if we have no results but filters were applied
      if (results.length === 0 && (organizations.length > 0 || survey_types.length > 0)) {
        toast.info("No results match your filters", {
          description: "Try broadening your search by removing some filters.",
          duration: 5000,
        })
      }

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

  const handleClearResults = () => {
    // Clear all search results
    setSearchResults([])

    // Clear PDF viewer state
    setSelectedPDF(null)
    setSelectedCardId(null)
    setCurrentPageNumber(null)
    setSelectedHighlightedId(null)

    // Optional: Show a message to the user
    toast.info("Search results and PDF view cleared")
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

      <ContributeSurveyModal
        isOpen={showContributeModal}
        onClose={() => setShowContributeModal(false)}
      />

      <div className="grid grid-cols-[28%_72%] h-screen">
        {/* Left Panel */}
        <div className="p-6 overflow-y-auto custom-scrollbar">
          <div className="mb-2">
            {/* Logo and icons in separate rows with proper spacing */}
            <div className="flex flex-col mb-4">
              {/* Full-width logo */}
              <div className="w-full">
                <img
                  src="/SurveyAcceleratorLogo-Stacked-White.svg"
                  alt="Survey Accelerator"
                  className="w-full h-auto object-contain"
                />
              </div>

              {/* Utility buttons row - positioned below the logo */}
              <div className="flex justify-end w-full mt-2">
                <Button
                  onClick={() => setShowFAQ(true)}
                  variant="outline"
                  size="sm"
                  className="text-white bg-black/70 hover:bg-black/90 backdrop-blur-sm border-gray-700 flex items-center gap-1 px-2 py-0.5 h-7 mr-2 text-xs"
                  title="Help"
                >
                  <HelpCircle className="h-3.5 w-3.5" />
                  <span>Help</span>
                </Button>
                <Button
                  onClick={() => setShowSettings(true)}
                  variant="outline"
                  size="sm"
                  className="text-white bg-black/70 hover:bg-black/90 backdrop-blur-sm border-gray-700 flex items-center gap-1 px-2 py-0.5 h-7 mr-2 text-xs"
                  title="Settings"
                >
                  <Settings className="h-3.5 w-3.5" />
                  <span>Settings</span>
                </Button>
                <Button
                  onClick={handleLogout}
                  variant="outline"
                  size="sm"
                  className="text-white bg-black/70 hover:bg-black/90 backdrop-blur-sm border-gray-700 flex items-center gap-1 px-2 py-0.5 h-7 mr-2 text-xs"
                  title="Logout"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  <span>Logout</span>
                </Button>
                <Button
                  onClick={() => setShowContributeModal(true)}
                  variant="outline"
                  size="sm"
                  className="text-white bg-black/70 hover:bg-black/90 backdrop-blur-sm border-gray-700 flex items-center gap-1 px-2 py-0.5 h-7 text-xs"
                  title="Contribute Survey"
                >
                  <Upload className="h-3.5 w-3.5" />
                  <span>Contribute</span>
                </Button>
              </div>
            </div>

            {/* Search form with glass effect */}
            <div className="bg-black/30 backdrop-blur-sm rounded-lg p-4 search-form-container">
              <SearchForm
                onSubmit={handleSearch}
                loading={loading}
                onClear={handleClearResults}
              />
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
