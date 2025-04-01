import React, { useState } from 'react';
import SearchForm from './components/SearchForm';
import SearchResultCard from './components/SearchResultCard';
import PDFViewer from './components/PDFViewer';
import SelectedResultDisplay from './components/SelectedResultDisplay';
import { searchDocuments } from './api';
import { DocumentSearchResult } from './interfaces';
import SequentialSpinner from './components/SequentialSpinner';

const AdvancedSearchEngine: React.FC = () => {
  const [searchResults, setSearchResults] = useState<DocumentSearchResult[]>([]);
  const [selectedPDF, setSelectedPDF] = useState<string | null>(null);
  const [selectedCardId, setSelectedCardId] = useState<number | null>(null);
  const [currentPageNumber, setCurrentPageNumber] = useState<number | null>(null);
  const [selectedHighlightedId, setSelectedHighlightedId] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Determine whether search results (or an error) are ready.
  const resultsReady = errorMessage !== null || searchResults.length > 0;

  // Handle search form submission.
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
      if (results.length > 0) {
        const topResult = results[0];
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
      // Wait for spinner sequence to complete before setting loading false.
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage('An unknown error occurred.');
      }
      setLoading(false);
    }
  };

  // Handle card click to display PDF and matches.
  const handleCardClick = (result: DocumentSearchResult) => {
    if (result.metadata.highlighted_pdf_url) {
      setSelectedPDF(result.metadata.highlighted_pdf_url);
    } else {
      setSelectedPDF(result.metadata.pdf_url ?? null);
    }
    setSelectedCardId(result.metadata.id);
    setCurrentPageNumber(null);
    setSelectedHighlightedId(null);
    if (result.matches.length > 0) {
      setCurrentPageNumber(result.matches[0].page_number);
      setSelectedHighlightedId(result.matches[0].rank);
    }
  };

  // Handle match click to navigate PDF to a specific page.
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
          background: '#111130',
        }}
      >
        <div className="mb-6">
          <img
            src="/SurveyAcceleratorLogo-White.svg"
            alt="Banner"
            className="w-full h-auto object-cover mb-4 rounded-lg shadow-lg"
          />
          <SearchForm onSubmit={handleSearch} />
        </div>
        {/* While loading, show the spinner sequence */}
        {loading && (
          <div className="flex justify-center items-center">
            <SequentialSpinner onComplete={() => setLoading(false)} resultsReady={resultsReady} />
          </div>
        )}
        {/* Once loading is complete, show errors or search results */}
        {!loading && errorMessage && (
          <div className="mt-4 p-4 text-red-500 bg-red-100 rounded-lg">{errorMessage}</div>
        )}
        {!loading && !errorMessage && (
          <div className="space-y-4">
            {searchResults.length > 0 && (
              <h3 className="text-xl font-semibold text-white">Search Results:</h3>
            )}
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
      {!loading && (
        <div className="w-[72%] flex flex-col h-full overflow-hidden relative">
          <div className="flex-grow min-h-0 relative overflow-hidden">
            <PDFViewer
              key={`${selectedPDF}-${currentPageNumber}`}
              pdfUrl={selectedPDF || ''}
              pageNumber={currentPageNumber || undefined}
            />
          </div>
          {selectedCardId && (
            <div
              className="overflow-y-auto p-0 bg-white shadow"
              style={{ maxHeight: '30%' }}
            >
              <SelectedResultDisplay
                selectedResult={searchResults.find(
                  (res) => res.metadata.id === selectedCardId
                )!}
                onMatchClick={handleMatchClick}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AdvancedSearchEngine;
