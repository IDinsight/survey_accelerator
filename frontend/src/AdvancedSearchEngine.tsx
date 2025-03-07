import React, { useState } from 'react';
import SearchForm from './components/SearchForm';
import SearchResultCard from './components/SearchResultCard';
import PDFViewer from './components/PDFViewer';
import SelectedResultDisplay from './components/SelectedResultDisplay';
import { searchDocuments } from './api';
import { DocumentSearchResult } from './interfaces';
import { FaSpinner } from 'react-icons/fa';

const AdvancedSearchEngine: React.FC = () => {
  const [searchResults, setSearchResults] = useState<DocumentSearchResult[]>([]);
  const [selectedPDF, setSelectedPDF] = useState<string | null>(null);
  const [selectedCardId, setSelectedCardId] = useState<number | null>(null);
  const [currentPageNumber, setCurrentPageNumber] = useState<number | null>(null);
  const [searchCollapsed, setSearchCollapsed] = useState<boolean>(false);
  const [selectedHighlightedId, setSelectedHighlightedId] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Handle search form submission
  const handleSearch = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setErrorMessage(null);
    const formData = new FormData(event.currentTarget);
    const query = formData.get('search') as string;
    const country = formData.get('country') as string;
    const organization = formData.get('organization') as string;
    const region = formData.get('region') as string;

    try {
      const results = await searchDocuments(query, country, organization, region);
      setSearchResults(results);
      setSearchCollapsed(true);
      if (results.length > 0) {
        const topResult = results[0];
        
        // Use the highlighted PDF URL if available
        if (topResult.metadata.highlighted_pdf_url) {
          setSelectedPDF(topResult.metadata.highlighted_pdf_url);
        } else {
          setSelectedPDF(topResult.metadata.pdf_url ?? null);
        }
        
        setSelectedCardId(topResult.metadata.id);
        if (topResult.matches.length > 0) {
          setCurrentPageNumber(topResult.matches[0].page_number);
          setSelectedHighlightedId(topResult.matches[0].rank);
        }
      }
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage('An unknown error occurred.');
      }
    } finally {
      setLoading(false);
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
      setSelectedHighlightedId(null);
    }
  };

  // Handle card click to display PDF and matches
  const handleCardClick = (result: DocumentSearchResult) => {
    // Always prefer the highlighted PDF if available
    if (result.metadata.highlighted_pdf_url) {
      setSelectedPDF(result.metadata.highlighted_pdf_url);
    } else {
      setSelectedPDF(result.metadata.pdf_url ?? null);
    }
    
    // Set the selected card ID
    setSelectedCardId(result.metadata.id);
    
    // Reset page number and selected highlight
    setCurrentPageNumber(null);
    setSelectedHighlightedId(null);

    // Navigate to the page of the first match
    if (result.matches.length > 0) {
      setCurrentPageNumber(result.matches[0].page_number);
      setSelectedHighlightedId(result.matches[0].rank);
    }
  };

  // Handle match click to navigate PDF to specific page
  const handleMatchClick = (pageNumber: number, matchId: number) => {
    setCurrentPageNumber(pageNumber);
    setSelectedHighlightedId(matchId);
  };


  return (
    <div className="flex h-screen bg-gray-100">
      {/* Left Side - Search Form and Results */}
      <div
        className="p-6 overflow-y-auto shadow-2xl"
        style={{
          flex: '0 0 28%',
          maxWidth: '28%',
          background: 'linear-gradient(to right, #c2e0ff 0%, #c2e0ff 96%, #b8d8f8 100%)',
        }}
      >
        {/* Search Form */}
        <div className="mb-6">
          <img src="/Banner.png" alt="Banner" className="w-full h-auto object-cover mb-4 rounded-lg shadow-lg" />
          <div
            className={`transition-all duration-500 ease-in-out ${
              searchCollapsed ? 'h-0 overflow-hidden' : 'h-auto'
            }`}
          >
            {!searchCollapsed && (
              <SearchForm
                onSubmit={handleSearch}
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

        {/* Loading Spinner */}
        {loading && (
          <div className="flex justify-center items-center">
            <FaSpinner className="animate-spin text-blue-500 text-3xl" />
          </div>
        )}

        {/* Error Message */}
        {errorMessage && (
          <div className="mt-4 p-4 text-red-500 bg-red-100 rounded-lg">
            {errorMessage}
          </div>
        )}

        {/* Search Results */}
        {!loading && !errorMessage && (
          <div className="space-y-4">
            {searchResults.length > 0 && <h3 className="text-xl font-semibold">Search Results:</h3>}
            {searchResults.map((result) => (
              <div key={result.metadata.id}>
                <SearchResultCard
                  result={result}
                  onClick={handleCardClick}
                  isSelected={selectedCardId === result.metadata.id}
                />
              </div>
            ))}
            
          </div>
        )}
      </div>

      {/* Right Side - PDF Viewer and Matches */}
      <div className="flex flex-col flex-grow h-full overflow-hidden">
        {/* PDF Viewer */}
        <div className="flex-grow min-h-0 overflow-hidden">
          <PDFViewer
            key={`${selectedPDF}-${currentPageNumber}`}
            pdfUrl={selectedPDF || ''}
            pageNumber={currentPageNumber || undefined}
          />
        </div>

        {/* Selected Result Display */}
        {selectedCardId && (() => {
          const selectedResult = searchResults.find(
            (res) => res.metadata.id === selectedCardId
          );

          return selectedResult ? (
            <div className="overflow-y-auto p-0 bg-white shadow" style={{ maxHeight: '30%' }}>
              <SelectedResultDisplay
                selectedResult={selectedResult}
                onMatchClick={handleMatchClick}
              />
            </div>
          ) : null;
        })()}
      </div>
    </div>
  );
};

export default AdvancedSearchEngine;