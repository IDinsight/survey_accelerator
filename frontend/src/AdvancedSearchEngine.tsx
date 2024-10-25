// src/AdvancedSearchEngine.tsx

import React, { useState } from 'react';

const countries = ['USA', 'Canada', 'UK', 'Germany', 'France', 'Japan'];
const organizations = ['UN', 'WHO', 'UNESCO', 'UNICEF', 'World Bank'];
const regions = ['North America', 'Europe', 'Asia', 'Africa', 'South America', 'Oceania'];

const AdvancedSearchEngine: React.FC = () => {
  const [searchResults, setSearchResults] = useState<string[]>([]);
  const [selectedPDF, setSelectedPDF] = useState<string | null>(null);

  const handleSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const query = formData.get('search') as string;
    const country = formData.get('country') as string;
    const organization = formData.get('organization') as string;
    const region = formData.get('region') as string;

    // Mock search results based on inputs
    setSearchResults([
      "https://storage.googleapis.com/survey_accelerator_files/86_pp_w4_community_quest.pdf#page=4"
    ]);
  };

  const handlePDFClick = (pdfPath: string) => {
    setSelectedPDF(pdfPath);
  };

  return (
    <div className="h-screen flex">
      {/* Left Side - Search Form and Results */}
      <div className="w-1/3 p-6 flex flex-col">
        {/* Search Form */}
        <div className="mb-6">
          <img
              src="banner.png"
              alt="Banner"
              className="w-full h-auto object-cover"
            />
          <form onSubmit={handleSearch} className="space-y-4">
            {/* Search Query */}
            <input
              name="search"
              type="text"
              placeholder="Enter your search query"
              className="w-full p-2 border rounded"
              required
            /><div className="mb-6">
          </div>


            {/* Region Dropdown */}
            <select name="region" className="w-full p-2 border rounded">
            <option value="">Select Region</option>
            {regions.map((region) => (
            <option key={region} value={region}>{region}</option>
            ))}
            </select>

            {/* Country Dropdown */}
            <select name="country" className="w-full p-2 border rounded">
              <option value="">Select Country</option>
              {countries.map((country) => (
                <option key={country} value={country}>{country}</option>
              ))}
            </select>

            {/* Organization Dropdown */}
            <select name="organization" className="w-full p-2 border rounded">
              <option value="">Select Organization</option>
              {organizations.map((org) => (
                <option key={org} value={org}>{org}</option>
              ))}
            </select>

            {/* Search Button */}
            <button type="submit" className="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600">
              Search
            </button>
          </form>
        </div>

        {/* Search Results */}
        <div className="flex-grow">
          <h3 className="text-xl font-semibold mb-4">Search Results:</h3>
          {searchResults.length === 0 ? (
            <p>No results found.</p>
          ) : (
            <ul className="space-y-2">
              {searchResults.map((result, index) => (
                <li key={index}>
                  <button
                    onClick={() => handlePDFClick(result)}
                    className="w-full text-left p-2 border rounded hover:bg-gray-100"
                  >
                    {result.split('/').pop()?.split('#')[0]}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Right Side - PDF Viewer */}
      <div className="w-2/3 border-l p-6">
        {selectedPDF ? (
          <object
            data={selectedPDF}
            type="application/pdf"
            width="100%"
            height="100%"
          >
            <p>
              It appears you don't have a PDF plugin for this browser.
              You can <a href={selectedPDF}>download the PDF file here.</a>
            </p>
          </object>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-500">
            Select a search result to view the PDF
          </div>
        )}
      </div>
    </div>
  );
};

export default AdvancedSearchEngine;
