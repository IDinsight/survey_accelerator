import React, { FC } from 'react';
import { DocumentSearchResult } from '../interfaces';

interface SearchResultCardProps {
  result: DocumentSearchResult;
  onClick: (result: DocumentSearchResult) => void;
  isSelected: boolean;
  precisionSearch: boolean;
}

const SearchResultCard: FC<SearchResultCardProps> = ({ result, onClick, isSelected, precisionSearch }) => {
  const matchType = precisionSearch ? 'QA Matches' : 'Page Matches';

  return (
    <div
      key={result.metadata.id}
      onClick={() => onClick(result)}
      className={`bg-[#4169E1] text-white p-4 rounded-xl cursor-pointer transition-colors duration-200 ${
        isSelected ? 'bg-[#CC7722]' : 'hover:bg-[#000080]'
      }`}
    >
      <h4 className="text-lg font-semibold">
        {result.metadata.title} ({result.metadata.year})
      </h4>
      <p className="text-sm mt-1">
        Region: {result.metadata.regions?.join(', ') || 'N/A'}, Country: {result.metadata.countries?.join(', ') || 'N/A'}, Org:{' '}
        {result.metadata.organizations?.join(', ') || 'N/A'}
      </p>
      <p className="text-sm mt-2">{result.metadata.summary}</p>
      <p className="text-sm mt-2">
        <strong>{matchType}:</strong> {result.matches.length}
      </p>
    </div>
  );
};

export default SearchResultCard;
