import React, { FC } from 'react';
import { Match } from '../interfaces';

interface HighlightedMatchesProps {
  matches: Match[];
  onClick: (page: number, id: number) => void;
  selectedHighlightedId: number | null;
}

const HighlightedMatches: FC<HighlightedMatchesProps> = ({ matches, onClick, selectedHighlightedId }) => {
  return (
    <div className="w-full space-y-2">
      {matches.map((match) => (
        <div
          key={match.rank}
          onClick={() => onClick(match.page_number, match.rank)}
          className={`p-3 rounded-lg cursor-pointer transition-colors duration-200 border ${
            selectedHighlightedId === match.rank ? 'bg-[#CC7722] text-white' : 'bg-[#4169E1] text-white hover:bg-[#000080]'
          }`}
        >
          {/* Type Guard to determine the type of match */}
          {'question' in match ? (
            `"${match.question}" - Page ${match.page_number}`
          ) : (
            `${match.contextualized_chunk} - Page ${match.page_number}`
          )}
        </div>
      ))}
    </div>
  );
};

export default HighlightedMatches;
