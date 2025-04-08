"use client"

import type { FC } from "react"
import { useState, useEffect } from "react"
import { Card, CardContent } from "./ui/card"
import type { DocumentSearchResult } from "../interfaces"
import { getMatchStrength } from "../interfaces"
import { MapPin, Building, FileSearch } from "lucide-react"

interface SearchResultCardProps {
  result: DocumentSearchResult
  onClick: (result: DocumentSearchResult) => void
  isSelected: boolean
  onMatchClick: (pageNumber: number, matchId: number) => void
  selectedHighlightedId: number | null
}

const MatchIcon: FC<{ className?: string }> = ({ className }) => {
  return <FileSearch className={className} />
}

// Helper function to get badge color based on match strength
const getStrengthColor = (strength: "strong" | "moderate" | "weak") => {
  switch (strength) {
    case "strong":
      return "bg-green-500/80 text-white"
    case "moderate":
      return "bg-green-300/60 text-white"
    case "weak":
      return "bg-gray-400/60 text-white"
    default:
      return "bg-gray-400/60 text-white"
  }
}

const SearchResultCard: FC<SearchResultCardProps> = ({
  result,
  onClick,
  isSelected,
  onMatchClick,
  selectedHighlightedId,
}) => {
  const [isExpanded, setIsExpanded] = useState(false)

  // Calculate match strengths
  const matchesWithStrength = result.matches.map((match: any) => ({
    ...match,
    strength: getMatchStrength(match.rank),
  }))

  // Count strong matches for display
  const strongMatchesCount = matchesWithStrength.filter((m) => m.strength === "strong").length

  // Update expansion state when selection changes
  useEffect(() => {
    if (isSelected && !isExpanded) {
      setIsExpanded(true)
    } else if (!isSelected) {
      setIsExpanded(false)
    }
  }, [isSelected])

  // Function to truncate text with ellipsis if it's too long
  const truncateText = (text: string, maxLength: number) => {
    if (!text) return "N/A"
    return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text
  }

  // Format metadata for display
  const regions = result.metadata.regions?.join(", ") || "N/A"
  const countries = result.metadata.countries?.join(", ") || "N/A"
  const organizations = result.metadata.organizations?.join(", ") || "N/A"

  // Calculate badge width for proper text wrapping
  const matchesText = `${result.matches.length} ${result.matches.length === 1 ? "Match" : "Matches"}`
  const strongText = strongMatchesCount > 0 ? `${strongMatchesCount} Strong` : ""
  const badgeWidth = (matchesText.length + strongText.length) * 8 + 40 // Approximate width calculation

  const handleCardClick = () => {
    if (isSelected) {
      // If already selected, toggle expansion
      setIsExpanded(!isExpanded)
    } else {
      // If not selected, select it and expand
      onClick(result)
      setIsExpanded(true)
    }
  }

  return (
    <div className="mb-6">
      <Card
        onClick={handleCardClick}
        className={`cursor-pointer transition-all duration-200 border-0 backdrop-blur-sm ${
          isSelected
            ? "bg-[#CC7722]/80 shadow-lg transform scale-[1.01]"
            : "bg-black/30 hover:bg-black/40 hover:shadow-md"
        }`}
        role="button"
        aria-pressed={isSelected}
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault()
            handleCardClick()
          }
        }}
      >
        {/* Title with your negative margin adjustment */}
        <div className="px-3 pt-1.5 pb-0 -mt-4">
          <h3 className="text-lg font-semibold text-white leading-tight">{result.metadata.title}</h3>
        </div>

        {/* Content with your negative margin adjustment */}
        <CardContent className="py-0 px-3 -mt-1 space-y-0.5">
          <div className="grid grid-cols-1 gap-0.5 text-sm text-white/90 -mt-3">
            <div className="flex items-center gap-2">
              <MapPin className="h-3.5 w-3.5 flex-shrink-0 text-white" />
              <span className="truncate" title={`Region: ${regions}, Country: ${countries}`}>
                <span className="font-medium">Location:</span> {truncateText(`${regions}, ${countries}`, 40)}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Building className="h-3.5 w-3.5 flex-shrink-0 text-white" />
              <span className="truncate" title={`Organization: ${organizations}`}>
                <span className="font-medium">Org:</span> {truncateText(organizations, 40)}
              </span>
            </div>
          </div>

          {/* Description with proper text wrapping around badge */}
          <div className="relative min-h-[60px]">
            {/* Badge positioned absolutely in bottom right */}
            <div
              className={`
                absolute bottom-0 right-0 flex items-center gap-1 px-2 py-1 rounded-md
                ${isSelected ? "bg-white/80 text-[#CC7722]" : "bg-white/20 text-white"}
                text-sm font-medium whitespace-nowrap
              `}
              style={{
                width: `${badgeWidth}px`,
                height: "28px",
              }}
            >
              <MatchIcon className="h-3.5 w-3.5" />
              <span>
                {matchesText}
                {strongMatchesCount > 0 && <span className="ml-1">• {strongText}</span>}
              </span>
            </div>

            {/* Description text with custom styling to wrap around the badge */}
            <p
              className="text-sm text-white/90 m-0"
              style={{
                position: "relative",
                display: "block",
                width: "100%",
                wordWrap: "break-word",
                paddingBottom: "30px", // Space for the badge height
                paddingRight: `${badgeWidth + 8}px`, // Space for the badge width plus margin
              }}
            >
              {result.metadata.summary || "No summary available"}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Accordion content - Match List (only shown when card is selected AND expanded) */}
      {isSelected && isExpanded && result.matches.length > 0 && (
        <div
          id={`matches-${result.metadata.id}`}
          className="mt-1 transition-all duration-300 max-h-[300px] overflow-y-auto space-y-2 pt-2 custom-scrollbar"
          style={{ marginTop: "4px" }}
        >
          {matchesWithStrength.map((match, index) => {
            const strength = match.strength || "weak"
            const strengthColor = getStrengthColor(strength)

            return (
              <div
                key={index}
                className={`
                  bg-black/30 hover:bg-black/40 text-white cursor-pointer
                  transition-all duration-200 rounded-md backdrop-blur-sm
                  ${selectedHighlightedId === match.rank ? "border-l-4 border-[#CC7722]" : ""}
                `}
                onClick={(e) => {
                  e.stopPropagation()
                  onMatchClick(match.page_number, match.rank)
                }}
              >
                <div className="p-1.5">
                  <div className="flex justify-between items-center mb-1">
                    <div className="text-xs text-white/90">Page {match.page_number}</div>
                    <div className={`text-xs px-2 py-0.5 rounded-full ${strengthColor}`}>
                      {strength.charAt(0).toUpperCase() + strength.slice(1)}
                    </div>
                  </div>

                  {/* Display the explanation */}
                  <p className="text-sm mt-0.5 mb-0 leading-tight">{match.explanation || "No explanation available"}</p>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default SearchResultCard
