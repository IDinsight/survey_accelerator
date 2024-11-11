import React from 'react';
import { MatchedChunk, MatchedQAPair } from '../interfaces';

interface MatchesListProps {
  matches: (MatchedChunk | MatchedQAPair)[];
  onMatchClick: (pageNumber: number) => void;
}

// Type guard to check if a match is of type MatchedChunk
const isMatchedChunk = (match: MatchedChunk | MatchedQAPair): match is MatchedChunk => {
  return (match as MatchedChunk).explanation !== undefined;
};

const MatchesList: React.FC<MatchesListProps> = ({
  matches,
  onMatchClick,
}) => {
  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copied to clipboard!');
    }).catch((error) => {
      console.error('Failed to copy to clipboard:', error);
    });
  };

  return (
    <div
      className=" p-2 bg-white rounded-lg shadow overflow-y-auto"
      style={{ maxHeight: '22vh' }} // Limit height to 22% of viewport height
    >
      <h4 className="text-lg font-semibold">
        Matches for Selected Result:
      </h4>
      <ul className="space-y-2 mt-2">
        {matches.map((match, index) => (
          <li key={index} className="relative">
            <button
              className="text-sm text-left w-full bg-blue-100 hover:bg-blue-200 p-2 rounded"
              onClick={() => onMatchClick(match.page_number)}
            >
              <strong>
                Rank {match.rank}, Page {match.page_number}:
              </strong>{' '}
              {isMatchedChunk(match) ? (
                <p>{match.explanation}</p>
              ) : (
                <>
                  <p><strong>Question:</strong> {match.question}</p>
                  <p><strong>Answer:</strong> {match.answer}</p>
                  {/* Copy button */}
                  <button
                    className="absolute top-2 right-2 mt-1 mr-1 px-2 py-1 text-xs text-white bg-[#FF8500] rounded-full hover:bg-[#e67300]"
                    onClick={(e) => {
                        e.stopPropagation(); // Prevent triggering onMatchClick
                        handleCopyToClipboard(`${match.question} ${match.answer}`);
                    }}
                    >
                    Copy
                    </button>
                </>
              )}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default MatchesList;
