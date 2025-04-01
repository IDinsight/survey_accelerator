import React, { useState } from "react";
import { toast } from "sonner";
import SearchForm from "./components/SearchForm";
import SearchResultCard from "./components/SearchResultCard";
import PDFViewer from "./components/PDFViewer";
import SelectedResultDisplay from "./components/SelectedResultDisplay";
import { searchDocuments } from "./api";
import { DocumentSearchResult } from "./interfaces";
import SequentialSpinner from "./components/SequentialSpinner";

const AdvancedSearchEngine: React.FC = () => {
  const [searchResults, setSearchResults] = useState<DocumentSearchResult[]>([]);
  const [selectedPDF, setSelectedPDF] = useState<string | null>(null);
  const [selectedCardId, setSelectedCardId] = useState<number | null>(null);
  const [currentPageNumber, setCurrentPageNumber] = useState<number | null>(null);
  const [selectedHighlightedId, setSelectedHighlightedId] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const resultsReady = searchResults.length > 0;

  const handleSearch = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    const formData = new FormData(event.currentTarget);
    const query = formData.get("search") as string;
    const country = formData.get("country") as string;
    const organization = formData.get("organization") as string;
    const region = formData.get("region") as string;

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
    } catch (error: any) {
      if (error instanceof Error) {
        toast(error.message, {
          description: "Please try again or reach out to support at surveyaccelerator@idinsight.org",
          duration: 4500,
        });
      } else {
        toast("An unknown error occurred.", {
          description: "Please try again.",
          duration: 4000,
        });
      }
    } finally {
      setLoading(false);
    }
  };

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

  const handleMatchClick = (pageNumber: number, matchId: number) => {
    setCurrentPageNumber(pageNumber);
    setSelectedHighlightedId(matchId);
  };

  return (
<div className="grid grid-cols-[28%_72%] h-screen bg-gray-100">
  {/* Left Panel: 1/3 width */}
      <div className="p-6 overflow-y-auto shadow-2xl bg-[#111130]">
        <div className="mb-6">
          <img
            src="/SurveyAcceleratorLogo-White.svg"
            alt="Banner"
            className="w-full h-auto object-cover mb-4 rounded-lg shadow-lg"
          />
          <SearchForm onSubmit={handleSearch} />
        </div>
        {loading && (
          <div className="flex justify-center items-center">
            <SequentialSpinner onComplete={() => {}} resultsReady={resultsReady} />
          </div>
        )}
        {/* No error card; errors are shown via toast */}
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
      </div>

      {/* Right Panel: 2/3 width */}
      <div className="relative flex flex-col h-full overflow-hidden">
        <div className="relative flex-grow min-h-0 overflow-hidden">
          <PDFViewer
            key={`${selectedPDF}-${currentPageNumber}`}
            pdfUrl={selectedPDF || ""}
            pageNumber={currentPageNumber || undefined}
          />
        </div>
        {selectedCardId && (
          <div className="overflow-y-auto p-0 bg-white shadow" style={{ maxHeight: "30%" }}>
            <SelectedResultDisplay
              selectedResult={
                searchResults.find((res) => res.metadata.id === selectedCardId)!
              }
              onMatchClick={handleMatchClick}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default AdvancedSearchEngine;
