// src/components/SelectedResultDisplay.tsx

import React from 'react';
import MatchesList from './MatchesList';
import { DocumentSearchResult, MatchedQAPair } from '../interfaces';

interface SelectedResultDisplayProps {
  selectedResult: DocumentSearchResult;
  onMatchClick: (pageNumber: number) => void;
}

const SelectedResultDisplay: React.FC<SelectedResultDisplayProps> = ({
  selectedResult,
  onMatchClick,
}) => {
  const matches = selectedResult.matches as MatchedQAPair[]; // Type assertion based on backend response

  return (
    <MatchesList
      matches={matches}
      onMatchClick={onMatchClick}
    />
  );
};

export default SelectedResultDisplay;
