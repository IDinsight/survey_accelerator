import React, { useState } from 'react';

const countries = ['USA', 'Canada', 'UK', 'Germany', 'France', 'Japan'];
const organizations = ['UN', 'WHO', 'UNESCO', 'UNICEF', 'World Bank'];
const regions = ['North America', 'Europe', 'Asia', 'Africa', 'South America', 'Oceania'];

const AdvancedSearchEngine: React.FC = () => {
  const [searchResults, setSearchResults] = useState<{
    id: number,
    title: string,
    year: string,
    organization: string,
    country: string,
    region: string,
    summary: string,
    pdfUrl: string
  }[]>([]);
  const [selectedPDF, setSelectedPDF] = useState<string | null>(null);
  const [selectedCardId, setSelectedCardId] = useState<number | null>(null);
  const [selectedHighlightedId, setSelectedHighlightedId] = useState<number | null>(null);
  const [searchCollapsed, setSearchCollapsed] = useState<boolean>(false);
  const [precisionSearch, setPrecisionSearch] = useState<boolean>(false);

  const handleSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const query = formData.get('search') as string;
    const country = formData.get('country') as string;
    const organization = formData.get('organization') as string;
    const region = formData.get('region') as string;

    // Mock search results based on inputs
    setSearchResults([
      {
        id: 1,
        title: "Community Questionnaire",
        year: "2022",
        organization: "World Bank",
        country: "USA",
        region: "North America",
        summary: "This document contains a community questionnaire for socio-economic assessment.",
        pdfUrl: "https://storage.googleapis.com/survey_accelerator_files/86_pp_w4_community_quest.pdf#page=4"
      },
      {
        id: 2,
        title: "Health Survey Report",
        year: "2023",
        organization: "WHO",
        country: "UK",
        region: "Europe",
        summary: "Annual health survey report for the United Kingdom.",
        pdfUrl: "https://example.com/health-survey-report.pdf"
      },
      {
        id: 3,
        title: "Education Statistics",
        year: "2021",
        organization: "UNESCO",
        country: "France",
        region: "Europe",
        summary: "Comprehensive education statistics for France.",
        pdfUrl: "https://example.com/education-statistics.pdf"
      },
      {
        id: 4,
        title: "Child Welfare Study",
        year: "2022",
        organization: "UNICEF",
        country: "Brazil",
        region: "South America",
        summary: "In-depth study on child welfare in Brazil.",
        pdfUrl: "https://example.com/child-welfare-study.pdf"
      },
      {
        id: 5,
        title: "Economic Impact Analysis",
        year: "2023",
        organization: "IMF",
        country: "Japan",
        region: "Asia",
        summary: "Analysis of economic impacts in Japan.",
        pdfUrl: "https://example.com/economic-impact-analysis.pdf"
      },
      {
        id: 6,
        title: "Agricultural Production Survey",
        year: "2021",
        organization: "FAO",
        country: "India",
        region: "Asia",
        summary: "Survey on agricultural production in India.",
        pdfUrl: "https://example.com/agricultural-production-survey.pdf"
      },
      {
        id: 7,
        title: "Labor Market Analysis",
        year: "2022",
        organization: "ILO",
        country: "Germany",
        region: "Europe",
        summary: "Comprehensive analysis of the German labor market.",
        pdfUrl: "https://example.com/labor-market-analysis.pdf"
      },
      {
        id: 8,
        title: "Trade Flow Report",
        year: "2023",
        organization: "WTO",
        country: "Australia",
        region: "Oceania",
        summary: "Report on international trade flows for Australia.",
        pdfUrl: "https://example.com/trade-flow-report.pdf"
      }
    ]);
    setSearchCollapsed(true);
  };

  const handleToggleSearch = () => {
    setSearchCollapsed(!searchCollapsed);
    if (!searchCollapsed) {
      // Reset to initial state when expanding search
      setSearchResults([]);
      setSelectedPDF(null);
      setSelectedCardId(null);
      setSelectedHighlightedId(null);
    }
  };

  const handleCardClick = (result: {
    id: number,
    pdfUrl: string
  }) => {
    setSelectedPDF(result.pdfUrl);
    setSelectedCardId(result.id);
    setSelectedHighlightedId(1); // Set the first highlighted match as selected by default
  };

  const handleHighlightedMatchClick = (page: number, id: number) => {
    setSelectedHighlightedId(id);
    // Update the PDF URL to include the page number explicitly to trigger a re-render
    setSelectedPDF(`https://storage.googleapis.com/survey_accelerator_files/86_pp_w4_community_quest.pdf#page=${page}#${new Date().getTime()}`);
  };

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
          background: 'linear-gradient(to right, #c2e0ff 0%, #c2e0ff 96%, #b8d8f8 100%)', // Very subtle transition to a slightly darker blue
          padding: '20px' // Create a visible gap with a consistent inner padding
        }}
      >
        {/* Search Form */}
        <div className="mb-6">
          <img
            src="banner.png"
            alt="Banner"
            className="w-full h-auto object-cover mb-4 rounded-lg shadow-lg"
          />
          <div className={`transition-all duration-500 ease-in-out ${searchCollapsed ? 'h-0 overflow-hidden' : 'h-auto'}`}>
            {!searchCollapsed && (
              <form onSubmit={handleSearch} className="space-y-4">
                {/* Search Query */}
                <input
                  name="search"
                  type="text"
                  placeholder="Enter your search query"
                  className="w-full p-2 border rounded shadow-md focus:outline-none"
                  required
                />
                {/* Region Dropdown */}
                <select name="region" className="w-full p-2 border rounded shadow-md">
                  <option value="">Select Region</option>
                  {regions.map((region) => (
                    <option key={region} value={region}>{region}</option>
                  ))}
                </select>
                {/* Country Dropdown */}
                <select name="country" className="w-full p-2 border rounded shadow-md">
                  <option value="">Select Country</option>
                  {countries.map((country) => (
                    <option key={country} value={country}>{country}</option>
                  ))}
                </select>
                {/* Organization Dropdown */}
                <select name="organization" className="w-full p-2 border rounded shadow-sm">
                  <option value="">Select Organization</option>
                  {organizations.map((org) => (
                    <option key={org} value={org}>{org}</option>
                  ))}
                </select>
                {/* Precision Question Toggle */}
                <div className="flex items-center p-2 rounded-lg">
                  <input
                    type="checkbox"
                    id="precisionSearch"
                    checked={precisionSearch}
                    onChange={handlePrecisionToggle}
                    className="mr-2 w-5 h-5"
                  />
                  <label htmlFor="precisionSearch" className="text-base font-medium">Precision Question Search</label>
                </div>
                {/* Search Button */}
                <button type="submit" className="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600 mt-4 shadow-md">
                  Search
                </button>
              </form>
            )}
          </div>
          {searchCollapsed && (
            <button onClick={handleToggleSearch} className="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600 mt-4 shadow-md">
              Create another search
            </button>
          )}
        </div>

        {/* Search Results */}
        <div className="space-y-4">
          {searchResults.length > 0 && (
            <h3 className="text-xl font-semibold">Search Results:</h3>
          )}

          {searchResults.length === 0 ? (
            <div className="h-full flex items-center justify-center text-gray-500">
              Search results will appear here.
            </div>
          ) : (
            searchResults.map((result, index) => (
              <div
                key={result.id}
                onClick={() => handleCardClick(result)}
                className={
                  `bg-[#4169E1] text-white p-4 rounded-xl cursor-pointer transition-colors duration-200 ${
                    selectedCardId === result.id ? 'bg-[#CC7722]' : 'hover:bg-[#000080]'
                  }`
                }
                style={{ position: 'relative' }}
              >
                <h4 className="text-lg font-semibold">{result.title} ({result.year})</h4>
                <p className="text-sm mt-1">Region: {result.region}, Country: {result.country}, Org: {result.organization}</p>
                <p className="text-sm mt-2">{result.summary}</p>

                {/* Hits Badge */}
                <span
                  className="absolute top-2 right-2 text-xs bg-white text-[#4169E1] px-2 py-1 rounded-full shadow-sm"
                >
                  {index + 3} hits
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Right Side - PDF Viewer */}
      <div className="p-6 border-l border-gray-300 flex flex-col justify-between" style={{ width: '72%' }}>        <div className="flex-grow mb-4">
          {selectedPDF ? (
            <iframe
              key={selectedPDF} // Adding key to force re-render on URL change
              src={selectedPDF}
              className="w-full h-full border-none"
              title="PDF Viewer"
            />
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500">
              Select a search result to view the PDF
            </div>
          )}
        </div>
        <div className="p-4 bg-white rounded-lg shadow flex flex-col items-start">
          <h3 className="text-lg font-semibold mb-2">Highlighted matches:</h3>
          {selectedCardId ? (
            <div className="w-full space-y-2">
              <div
                onClick={() => handleHighlightedMatchClick(4, 1)}
                className={
                  `p-3 rounded-lg cursor-pointer transition-colors duration-200 border ${
                    selectedHighlightedId === 1 ? 'bg-[#CC7722] text-white' : 'bg-[#4169E1] text-white hover:bg-[#000080]'
                  }`
                }
              >
                "What can I do about breastfeeding?" - Page 4
              </div>
              <div
                onClick={() => handleHighlightedMatchClick(7, 2)}
                className={
                  `p-3 rounded-lg cursor-pointer transition-colors duration-200 border ${
                    selectedHighlightedId === 2 ? 'bg-[#CC7722] text-white' : 'bg-[#4169E1] text-white hover:bg-[#000080]'
                  }`
                }
              >
                "What are your sources of water?" - Page 7
              </div>
              <div
                onClick={() => handleHighlightedMatchClick(10, 3)}
                className={
                  `p-3 rounded-lg cursor-pointer transition-colors duration-200 border ${
                    selectedHighlightedId === 3 ? 'bg-[#CC7722] text-white' : 'bg-[#4169E1] text-white hover:bg-[#000080]'
                  }`
                }
              >
                "How do you manage sanitation?" - Page 10
              </div>
            </div>
          ) : (
            <div className="text-gray-500">
              Highlighted matches will show up here
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdvancedSearchEngine;
