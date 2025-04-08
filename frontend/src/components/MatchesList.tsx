"use client"

import type { FC } from "react"
import type { MatchedChunk, MatchedQAPair } from "../interfaces"

interface MatchesListProps {
  matches: (MatchedChunk | MatchedQAPair)[]
  onMatchClick: (pageNumber: number, matchId: number) => void
}

// Type guard to check if a match is of type MatchedChunk
const isMatchedChunk = (match: MatchedChunk | MatchedQAPair): match is MatchedChunk => {
  return (match as MatchedChunk).explanation !== undefined
}

const MatchesList: FC<MatchesListProps> = ({ matches, onMatchClick }) => {
  return (
    <div className="max-h-[22vh] overflow-y-auto bg-[#111130]">
      <div className="pb-1 pt-2 px-3">
        <h3 className="text-lg font-bold text-white">Matches for Selected Result</h3>
      </div>

      <div className="space-y-2 p-1.5">
        {matches.length > 0 ? (
          matches.map((match, index) => (
            <div
              key={index}
              className="bg-[#4169E1] hover:bg-[#000080] text-white cursor-pointer transition-all duration-200 rounded-md"
              onClick={() => onMatchClick(match.page_number, match.rank)}
            >
              <div className="p-1.5">
                <div className="text-xs text-white/90">
                  Rank {match.rank} from Page {match.page_number}
                </div>

                {isMatchedChunk(match) && <p className="text-sm mt-0.5 mb-0 leading-tight">{match.explanation}</p>}
              </div>
            </div>
          ))
        ) : (
          <div className="p-4 text-center text-gray-300 italic">No matches found</div>
        )}
      </div>
    </div>
  )
}

export default MatchesList
