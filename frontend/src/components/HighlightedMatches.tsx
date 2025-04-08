"use client"

import type { FC } from "react"
import { Card, CardContent } from "./ui/card"
import { Badge } from "./ui/badge"
import type { Match } from "../interfaces"
import { FileSearch } from "lucide-react"

interface HighlightedMatchesProps {
  matches: Match[]
  onClick: (page: number, id: number) => void
  selectedHighlightedId: number | null
}

const HighlightedMatches: FC<HighlightedMatchesProps> = ({ matches, onClick, selectedHighlightedId }) => {
  return (
    <div className="w-full space-y-1.5">
      {matches.map((match) => (
        <Card
          key={match.rank}
          onClick={() => onClick(match.page_number, match.rank)}
          className={`cursor-pointer transition-all duration-200 border-0 backdrop-blur-sm ${
            selectedHighlightedId === match.rank
              ? "bg-[#CC7722]/80 shadow-md transform scale-[1.01]"
              : "bg-black/30 hover:bg-black/40 hover:shadow-sm"
          }`}
          role="button"
          aria-pressed={selectedHighlightedId === match.rank}
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault()
              onClick(match.page_number, match.rank)
            }
          }}
        >
          <CardContent className="p-2.5 pt-2">
            <div className="flex items-start">
              <FileSearch className="h-4 w-4 mt-0.5 mr-2 flex-shrink-0 text-white" />
              <div className="flex-1">
                <div className="text-sm font-medium text-white">
                  {/* Type Guard to determine the type of match */}
                  {"question" in match ? (
                    <span className="italic">"{match.question}"</span>
                  ) : (
                    <span>{match.contextualized_chunk}</span>
                  )}
                </div>
                <div className="flex justify-between items-center mt-1">
                  <div className="text-xs text-white/80">Rank {match.rank}</div>
                  <Badge
                    variant="outline"
                    className={`${
                      selectedHighlightedId === match.rank ? "bg-white/80 text-[#CC7722]" : "bg-white/20 text-white"
                    }`}
                  >
                    Page {match.page_number}
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}

      {matches.length === 0 && (
        <Card className="bg-black/30 backdrop-blur-sm border-0">
          <CardContent className="p-4 text-center text-white/70 italic">No matches found</CardContent>
        </Card>
      )}
    </div>
  )
}

export default HighlightedMatches
