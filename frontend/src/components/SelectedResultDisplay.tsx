// src/components/SelectedResultDisplay.tsx

import React from 'react';
import MatchesList from './MatchesList';
import { DocumentSearchResult } from '../interfaces';

interface SelectedResultDisplayProps {
  selectedResult: DocumentSearchResult;
  onMatchClick: (pageNumber: number, matchId: number) => void;
}

const SelectedResultDisplay: React.FC<SelectedResultDisplayProps> = ({
  selectedResult,
  onMatchClick,
}) => {
  return (
    <MatchesList
      matches={selectedResult.matches}
      onMatchClick={onMatchClick}
    />
  );
};

export default SelectedResultDisplay;
