import React, { FC } from 'react';

interface SearchFormProps {
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  precisionSearch: boolean;
  onPrecisionToggle: () => void;
}

const regions = ["Africa", "Global"];
const countries = ["Ethiopia", "Global", "Nigeria", "Tanzania", "Uganda"];
const organizations = ["UNICEF", "USAID", "World Bank"];

const SearchForm: FC<SearchFormProps> = ({ onSubmit, precisionSearch, onPrecisionToggle }) => {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <input name="search" type="text" placeholder="Enter your search query" className="w-full p-2 border rounded shadow-md focus:outline-none" required />
      <select name="region" className="w-full p-2 border rounded shadow-md">
        <option value="">Select Region</option>
        {regions.map(region => <option key={region} value={region}>{region}</option>)}
      </select>
      <select name="country" className="w-full p-2 border rounded shadow-md">
        <option value="">Select Country</option>
        {countries.map(country => <option key={country} value={country}>{country}</option>)}
      </select>
      <select name="organization" className="w-full p-2 border rounded shadow-sm">
        <option value="">Select Organization</option>
        {organizations.map(org => <option key={org} value={org}>{org}</option>)}
      </select>
      <div className="flex items-center p-1 rounded-lg">
        <input type="checkbox" id="precisionSearch" checked={precisionSearch} onChange={onPrecisionToggle} className="mr-2 w-5 h-5" />
        <label htmlFor="precisionSearch" className="text-base font-medium">Precision Question Search</label>
      </div>
      <button type="submit" className="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600 mt-4 shadow-md">Search</button>
    </form>
  );
};

export default SearchForm;
