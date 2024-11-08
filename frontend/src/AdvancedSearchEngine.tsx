// src/AdvancedSearchEngine.tsx

import React, { useState } from 'react';
import SearchForm from './components/SearchForm';
import SearchResultCard from './components/SearchResultCard';
import PDFViewer from './components/PDFViewer';
import SelectedResultDisplay from './components/SelectedResultDisplay';
import { searchDocuments } from './api';
import { DocumentSearchResult } from './interfaces';

const AdvancedSearchEngine: React.FC = () => {
  const [searchResults, setSearchResults] = useState<DocumentSearchResult[]>([]);
  const [selectedPDF, setSelectedPDF] = useState<string | null>(null);
  const [selectedCardId, setSelectedCardId] = useState<number | null>(null);
  const [currentPageNumber, setCurrentPageNumber] = useState<number | null>(null);
  const [searchCollapsed, setSearchCollapsed] = useState<boolean>(false);
  const [precisionSearch, setPrecisionSearch] = useState<boolean>(false);

  // Handle search form submission
  const handleSearch = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const query = formData.get('search') as string;
    const country = formData.get('country') as string;
    const organization = formData.get('organization') as string;
    const region = formData.get('region') as string;

    try {
      const results = await searchDocuments(query, 10, precisionSearch, country, organization, region);
      setSearchResults(results);
      setSearchCollapsed(true);
    } catch (error) {
      console.error('Error searching documents:', error);
    }
  };

  // Toggle search form visibility
  const handleToggleSearch = () => {
    setSearchCollapsed(!searchCollapsed);
    if (!searchCollapsed) {
      setSearchResults([]);
      setSelectedPDF(null);
      setSelectedCardId(null);
      setCurrentPageNumber(null);
    }
  };

  // Handle card click to display PDF and matches
  const handleCardClick = (result: DocumentSearchResult) => {
    setSelectedPDF(result.metadata.pdf_url ?? null);
    setSelectedCardId(result.metadata.id);
    setCurrentPageNumber(null);
  };

  // Handle match click to navigate PDF to specific page
  const handleMatchClick = (pageNumber: number) => {
    setCurrentPageNumber(pageNumber);
  };

  // Toggle between precision (QA) search and regular search
  const handlePrecisionToggle = () => {
    setPrecisionSearch(!precisionSearch);
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Left Side - Search Form and Results */}
      <div
        className="p-6 overflow-y-auto shadow-2xl relative"
        style={{
          width: '28%',
          background: 'linear-gradient(to right, #c2e0ff 0%, #c2e0ff 96%, #b8d8f8 100%)',
        }}
      >
        {/* Search Form */}
        <div className="mb-6">
          <img src="banner.png" alt="Banner" className="w-full h-auto object-cover mb-4 rounded-lg shadow-lg" />
          <div
            className={`transition-all duration-500 ease-in-out ${
              searchCollapsed ? 'h-0 overflow-hidden' : 'h-auto'
            }`}
          >
            {!searchCollapsed && (
              <SearchForm
                onSubmit={handleSearch}
                precisionSearch={precisionSearch}
                onPrecisionToggle={handlePrecisionToggle}
              />
            )}
          </div>
          {searchCollapsed && (
            <button
              onClick={handleToggleSearch}
              className="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600 mt-4 shadow-md"
            >
              Create another search
            </button>
          )}
        </div>

        {/* Search Results */}
        <div className="space-y-4">
          {searchResults.length > 0 && <h3 className="text-xl font-semibold">Search Results:</h3>}
          {searchResults.map((result) => (
            <div key={result.metadata.id}>
              <SearchResultCard
                result={result}
                onClick={handleCardClick}
                isSelected={selectedCardId === result.metadata.id}
                precisionSearch={precisionSearch}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Right Side - PDF Viewer and Matches */}
      <div className="flex flex-col flex-grow h-full">
        {/* PDF Viewer */}
        <div className="flex-grow min-h-0">
          <PDFViewer pdfUrl={selectedPDF || ''} pageNumber={currentPageNumber || undefined} />
        </div>

        {/* Selected Result Display */}
        {selectedCardId && (() => {
          const selectedResult = searchResults.find(
            (res) => res.metadata.id === selectedCardId
          );

          return selectedResult ? (
            <SelectedResultDisplay
              selectedResult={selectedResult}
              onMatchClick={handleMatchClick}
            />
          ) : null;
        })()}
      </div>
    </div>
  );
};

export default AdvancedSearchEngine;
