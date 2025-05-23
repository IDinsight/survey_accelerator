"use client"

import type { FC } from "react"
import { useState, useEffect } from "react"
import { Card, CardContent } from "./ui/card"
import type { DocumentSearchResult } from "../interfaces"
import { getMatchStrength } from "../interfaces"
import { MapPin, Building, FileSearch, Brain, TextSearch, BarChart2 } from 'lucide-react'

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
      return "bg-green-600 text-white" // Darker green for strong matches
    case "moderate":
      return "bg-amber-500 text-white" // Amber/orange for moderate matches
    case "weak":
      return "bg-gray-600 text-white" // Darker gray for weak matches
    default:
      return "bg-gray-600 text-white"
  }
}

// Helper function to get match type icon and color
const getMatchTypeInfo = (matchType: string | undefined) => {
  switch (matchType) {
    case "direct":
      return {
        icon: <TextSearch className="h-3.5 w-3.5" />,
        color: "bg-blue-500 text-white",
        label: "Direct"
      }
    case "contextual":
      return {
        icon: <Brain className="h-3.5 w-3.5" />,
        color: "bg-purple-500 text-white",
        label: "Context"
      }
    default:
      return {
        icon: <BarChart2 className="h-3.5 w-3.5" />,
        color: "bg-teal-500 text-white",
        label: "Balanced"
      }
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
  
  // Match type counts (with fallback for older data)
  const contextualCount = result.contextual_matches || 0
  const directCount = result.direct_matches || 0
  const balancedCount = result.balanced_matches || 0

  // Auto-expand when selected
  useEffect(() => {
    if (isSelected) {
      setIsExpanded(true)
    } else {
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

  // Calculate match text
  const matchesText = `${result.matches.length} ${result.matches.length === 1 ? "Match" : "Matches"}`

  const handleCardClick = () => {
    if (isSelected) {
      // If already selected, toggle expansion
      setIsExpanded(!isExpanded)
    } else {
      // If not selected, select it
      onClick(result)
      // Expansion will happen automatically via useEffect
    }
  }

  return (
    <div>
      <Card
        onClick={handleCardClick}
        className={`cursor-pointer z-1 transition-all duration-200 border-none ${
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
        {/* Title */}
        <div className="px-4 pt-2 pb-0 -mb-5 -mt-4">
          <h3 className="text-lg font-semibold text-white leading-tight">{result.metadata.title}</h3>
        </div>

        {/* Content */}
        <CardContent className="py-2 px-4 space-y-2">
          <div className="grid grid-cols-1 gap-1 text-sm text-white/90">
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

          {/* Description - now full width with no wrapping around badge */}
          <p className="text-sm text-white/90 mt-0.5 mb-2">{result.metadata.summary || "No summary available"}</p>

          {/* Match stats badges */}
          <div className="flex justify-between items-center">
            {/* Match Type Distribution */}
            <div className="flex gap-1">
              {directCount > 0 && (
                <div className="flex items-center gap-0.5 px-1.5 py-0.5 rounded-md text-xs font-medium bg-blue-500/80 text-white">
                  <TextSearch className="h-3 w-3" />
                  <span>{directCount} Direct</span>
                </div>
              )}
              {contextualCount > 0 && (
                <div className="flex items-center gap-0.5 px-1.5 py-0.5 rounded-md text-xs font-medium bg-purple-500/80 text-white">
                  <Brain className="h-3 w-3" />
                  <span>{contextualCount} Context</span>
                </div>
              )}
              {balancedCount > 0 && (
                <div className="flex items-center gap-0.5 px-1.5 py-0.5 rounded-md text-xs font-medium bg-teal-500/80 text-white">
                  <BarChart2 className="h-3 w-3" />
                  <span>{balancedCount} Balanced</span>
                </div>
              )}
            </div>
            
            {/* Total Match Count */}
            <div
              className={`
                flex items-center gap-1 px-2 py-1 rounded-md -mb-3.5
                ${isSelected ? "bg-white/80 text-[#CC7722]" : "bg-white/20 text-white"}
                text-sm font-medium whitespace-nowrap
              `}
            >
              <MatchIcon className="h-3.5 w-3.5" />
              <span>
                {matchesText}
                {strongMatchesCount > 0 && <span className="ml-1">• {strongMatchesCount} Strong</span>}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Accordion content - Match List (only shown when card is selected AND expanded) */}
      {isSelected && isExpanded && result.matches.length > 0 && (
        <div
          id={`matches-${result.metadata.id}`}
          className="mt-1 transition-all duration-300 max-h-[300px] overflow-y-auto space-y-1.5 pt-1.5 custom-scrollbar"
          style={{ marginTop: "3px" }}
        >
          {matchesWithStrength.map((match, index) => {
            const strength = match.strength || "weak"
            const strengthColor = getStrengthColor(strength)
            const matchTypeInfo = getMatchTypeInfo(match.match_type)
            
            // Calculate score indicators for contextual and direct matches
            const contextualScore = match.contextual_score || 5
            const directScore = match.direct_match_score || 5
            
            return (
              <div
                key={index}
                className={`
                  bg-black/30 hover:bg-black/40 text-white cursor-pointer
                  transition-all duration-200 rounded-lg backdrop-blur-sm
                  ${selectedHighlightedId === match.rank
                    ? "border border-white border-l-4"
                    : "border border-[#CC7722]/70 border-opacity-50"
                  }
                `}
                onClick={(e) => {
                  e.stopPropagation()
                  onMatchClick(match.page_number, match.rank)
                }}
              >
                <div className="p-2">
                  {/* Top row with page number, match type and strength */}
                  <div className="flex justify-between items-center mb-1">
                    <div className="text-xs text-white/90">Page {match.page_number}</div>
                    <div className="flex gap-1 items-center">
                      {/* Match type indicator */}
                      <div className={`text-xs px-1.5 py-0.5 rounded-md flex items-center gap-0.5 ${matchTypeInfo.color}`}>
                        {matchTypeInfo.icon}
                        <span>{matchTypeInfo.label}</span>
                      </div>
                      
                      {/* Strength indicator */}
                      <div className={`text-xs px-2 py-0.5 rounded-full ${strengthColor}`}>
                        {strength.charAt(0).toUpperCase() + strength.slice(1)}
                      </div>
                    </div>
                  </div>

                  {/* Display the explanation */}
                  <p className="text-sm mt-0.5 mb-1 leading-tight">{match.explanation || "No explanation available"}</p>
                  
                  {/* Score bars */}
                  <div className="mt-1 grid grid-cols-2 gap-2 px-1">
                    {/* Contextual score bar */}
                    <div className="flex flex-col">
                      <div className="flex justify-between items-center mb-0.5 text-xs">
                        <span className="text-purple-300 flex items-center">
                          <Brain className="h-3 w-3 mr-0.5" /> Context
                        </span>
                        <span>{contextualScore}/10</span>
                      </div>
                      <div className="h-1 bg-gray-700 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-purple-500 rounded-full" 
                          style={{ width: `${contextualScore * 10}%` }} 
                        />
                      </div>
                    </div>
                    
                    {/* Direct score bar */}
                    <div className="flex flex-col">
                      <div className="flex justify-between items-center mb-0.5 text-xs">
                        <span className="text-blue-300 flex items-center">
                          <TextSearch className="h-3 w-3 mr-0.5" /> Direct
                        </span>
                        <span>{directScore}/10</span>
                      </div>
                      <div className="h-1 bg-gray-700 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-blue-500 rounded-full" 
                          style={{ width: `${directScore * 10}%` }} 
                        />
                      </div>
                    </div>
                  </div>
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
