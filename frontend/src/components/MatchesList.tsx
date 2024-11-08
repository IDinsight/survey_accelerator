// src/components/MatchesList.tsx

import React from 'react';
import { MatchedQAPair } from '../interfaces';

interface MatchesListProps {
  matches: MatchedQAPair[]; // Assuming all matches have 'question' and 'answer'
  onMatchClick: (pageNumber: number) => void;
}

const MatchesList: React.FC<MatchesListProps> = ({
  matches,
  onMatchClick,
}) => {
  return (
    <div
      className="mt-4 p-4 bg-white rounded-lg shadow overflow-y-auto"
      style={{ maxHeight: '22vh' }} // Limit height to 22% of viewport height
    >
      <h4 className="text-lg font-semibold">
        Matches for Selected Result:
      </h4>
      <ul className="space-y-2 mt-2">
        {matches.map((match, index) => (
          <li key={index}>
            <button
              className="text-sm text-left w-full bg-blue-100 hover:bg-blue-200 p-2 rounded"
              onClick={() => onMatchClick(match.page_number)}
            >
              <strong>
                Rank {match.rank}, Page {match.page_number}:
              </strong>{' '}
              {match.question}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default MatchesList;
