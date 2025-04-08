"use client"

import type { FC } from "react"
import { Card, CardContent, CardFooter } from "../components/ui/card"
import type { DocumentSearchResult } from "../interfaces"
import { MapPin, Building, FileSearch } from "lucide-react"

interface SearchResultCardProps {
  result: DocumentSearchResult
  onClick: (result: DocumentSearchResult) => void
  isSelected: boolean
}

const MatchIcon: FC<{ className?: string }> = ({ className }) => {
  return <FileSearch className={className} />
}

const SearchResultCard: FC<SearchResultCardProps> = ({ result, onClick, isSelected }) => {
  // Function to truncate text with ellipsis if it's too long
  const truncateText = (text: string, maxLength: number) => {
    if (!text) return "N/A"
    return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text
  }

  // Format metadata for display
  const regions = result.metadata.regions?.join(", ") || "N/A"
  const countries = result.metadata.countries?.join(", ") || "N/A"
  const organizations = result.metadata.organizations?.join(", ") || "N/A"

  return (
    <Card
      onClick={() => onClick(result)}
      className={`cursor-pointer transition-all duration-200 border-0 ${
        isSelected ? "bg-[#CC7722] shadow-lg transform scale-[1.02]" : "bg-[#4169E1] hover:bg-[#000080] hover:shadow-md"
      }`}
      role="button"
      aria-pressed={isSelected}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          onClick(result)
        }
      }}
    >
      {/* Strategy 1: Replace CardHeader with a custom div for more control */}
      <div className="px-3 pt-1.5 pb-0 -mt-4" >
        <h3 className="text-lg font-semibold text-white leading-tight">{result.metadata.title}</h3>
      </div>

      {/* Strategy 2: Use negative margin to pull content up */}
      <CardContent className="py-0 px-3 -mt-1 space-y-0.5">
        <div className="grid grid-cols-1 gap-0.5 text-sm text-white/90 -mt-3">
          <div className="flex items-center gap-2">
            <MapPin className="h-3.5 w-3.5 flex-shrink-0 text-white" />
            <span className="truncate" title={`Region: ${regions}, Country: ${countries}`}>
              <span className="font-medium">Location:</span> {truncateText(`${regions}, ${countries}`, 40)}
            </span>
          </div>

          <div className="flex items-center gap-2 ">
            <Building className="h-3.5 w-3.5 flex-shrink-0 text-white" />
            <span className="truncate" title={`Organization: ${organizations}`}>
              <span className="font-medium">Org:</span> {truncateText(organizations, 40)}
            </span>
          </div>
        </div>

        <p className="text-sm text-white/90" title={result.metadata.summary}>
          {result.metadata.summary || "No summary available"}
        </p>
      </CardContent>

      <CardFooter className="pt-0 pb-1 px-3 flex justify-end items-center">
        <div
          className={`
            flex items-center gap-1 px-2 py-1 -mt-5 -mb-5  rounded-md
            ${isSelected ? "bg-white/90 text-[#CC7722]" : "bg-white/20 text-white"}
            text-sm font-medium
          `}
        >
          <MatchIcon className="h-3.5 w-3.5" />
          <span>
            {result.matches.length} {result.matches.length === 1 ? "Match" : "Matches"}
          </span>
        </div>
      </CardFooter>
    </Card>
  )
}

export default SearchResultCard
