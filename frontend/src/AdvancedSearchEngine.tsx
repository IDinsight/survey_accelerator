import React, { useState } from 'react';
import SearchForm from './components/SearchForm';
import SearchResultCard from './components/SearchResultCard';
import PDFViewer from './components/PDFViewer';
import { searchDocuments } from './api';
import { DocumentSearchResult, MatchedChunk, MatchedQAPair } from './interfaces';

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
          padding: '20px',
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
      <div
        className="p-6 border-l border-gray-300 flex flex-col justify-between"
        style={{ width: '72%' }}
      >
        <PDFViewer pdfUrl={selectedPDF || ''} pageNumber={currentPageNumber || undefined} />

        {selectedCardId && (() => {
          const selectedResult = searchResults.find((res) => res.metadata.id === selectedCardId);
          const matches = selectedResult?.matches ?? [];

          if (precisionSearch) {
            // QA Search Mode
            return (
              <div className="mt-4 p-4 bg-white rounded-lg shadow">
                <h4 className="text-lg font-semibold">QA Matches for Selected Result:</h4>
                <ul className="space-y-2 mt-2">
                  {matches
                    .filter((match): match is MatchedQAPair => 'question' in match)
                    .map((match: MatchedQAPair, index: number) => (
                      <li key={index} className="text-sm">
                        <strong>Rank {match.rank}:</strong> {match.question}
                      </li>
                    ))}
                </ul>
              </div>
            );
          } else {
            // Regular Search Mode
            return (
              <div className="mt-4 p-4 bg-white rounded-lg shadow">
                <h4 className="text-lg font-semibold">Matches for Selected Result:</h4>
                <ul className="space-y-2 mt-2">
                  {matches
                    .filter((match): match is MatchedChunk => 'explanation' in match)
                    .map((match: MatchedChunk, index: number) => (
                      <li
                        key={index}
                        className="text-sm cursor-pointer"
                        onClick={() => handleMatchClick(match.page_number)}
                      >
                        <strong>
                          Rank {match.rank}, Page {match.page_number}:
                        </strong>{' '}
                        {match.explanation}
                      </li>
                    ))}
                </ul>
              </div>
            );
          }
        })()}
      </div>
    </div>
  );
};

export default AdvancedSearchEngine;
