'use client';
import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';

const DummyComponent = () => {
  const [questionSearch, setQuestionSearch] = useState('');
  const [moduleSearch, setModuleSearch] = useState('');
  const [region, setRegion] = useState('');
  const [country, setCountry] = useState('');
  const [year, setYear] = useState('');
  const [organization, setOrganization] = useState('');
  const [showTable, setShowTable] = useState(false);

  const handleSearch = () => {
    // Display the dummy table when 'Run search' is clicked
    setShowTable(true);
  };

  // Generate dummy data for the table
  const dummyData = Array.from({ length: 5 }, (_, rowIndex) => ({
    col1: 'dummy data',
    col2: 'dummy data',
    col3: 'dummy data',
    col4: 'dummy data',
  }));

  return (
    <Box sx={{ padding: 4 }}>
      {/* Question Search Bar */}
      <TextField
        variant="outlined"
        label="Question search"
        fullWidth
        value={questionSearch}
        onChange={(e) => setQuestionSearch(e.target.value)}
        sx={{ marginBottom: 2 }}
      />

      {/* Module Search Bar */}
      <TextField
        variant="outlined"
        label="Module search"
        fullWidth
        value={moduleSearch}
        onChange={(e) => setModuleSearch(e.target.value)}
        sx={{ marginBottom: 2 }}
      />

      {/* Dropdowns for Region, Country, Year, Organization */}
      <Box sx={{ display: 'flex', gap: 2, marginBottom: 2 }}>
        {/* Region Dropdown */}
        <FormControl fullWidth>
          <InputLabel id="region-label">Region</InputLabel>
          <Select
            labelId="region-label"
            value={region}
            label="Region"
            onChange={(e) => setRegion(e.target.value)}
          >
            <MenuItem value="">
              <em>All Regions</em>
            </MenuItem>
            <MenuItem value="north-america">North America</MenuItem>
            <MenuItem value="europe">Europe</MenuItem>
            <MenuItem value="asia">Asia</MenuItem>
            {/* Add more regions as needed */}
          </Select>
        </FormControl>

        {/* Country Dropdown */}
        <FormControl fullWidth>
          <InputLabel id="country-label">Country</InputLabel>
          <Select
            labelId="country-label"
            value={country}
            label="Country"
            onChange={(e) => setCountry(e.target.value)}
          >
            <MenuItem value="">
              <em>All Countries</em>
            </MenuItem>
            <MenuItem value="usa">USA</MenuItem>
            <MenuItem value="canada">Canada</MenuItem>
            <MenuItem value="uk">United Kingdom</MenuItem>
            {/* Add more countries as needed */}
          </Select>
        </FormControl>

        {/* Year Dropdown */}
        <FormControl fullWidth>
          <InputLabel id="year-label">Year</InputLabel>
          <Select
            labelId="year-label"
            value={year}
            label="Year"
            onChange={(e) => setYear(e.target.value)}
          >
            <MenuItem value="">
              <em>All Years</em>
            </MenuItem>
            <MenuItem value="2021">2021</MenuItem>
            <MenuItem value="2022">2022</MenuItem>
            <MenuItem value="2023">2023</MenuItem>
            {/* Add more years as needed */}
          </Select>
        </FormControl>

        {/* Organization Dropdown */}
        <FormControl fullWidth>
          <InputLabel id="organization-label">Organization</InputLabel>
          <Select
            labelId="organization-label"
            value={organization}
            label="Organization"
            onChange={(e) => setOrganization(e.target.value)}
          >
            <MenuItem value="">
              <em>All Organizations</em>
            </MenuItem>
            <MenuItem value="org1">Organization 1</MenuItem>
            <MenuItem value="org2">Organization 2</MenuItem>
            {/* Add more organizations as needed */}
          </Select>
        </FormControl>
      </Box>

      {/* Run Search Button */}
      <Button variant="contained" onClick={handleSearch} sx={{ marginBottom: 2 }}>
        Run search
      </Button>

      {/* Dummy Table */}
      {showTable && (
        <Table sx={{ marginTop: 4 }} aria-label="dummy table">
          <TableHead>
            <TableRow>
              <TableCell>Question</TableCell>
              <TableCell>Module</TableCell>
              <TableCell>Org</TableCell>
              <TableCell>Link</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {dummyData.map((row, index) => (
              <TableRow key={index}>
                <TableCell>{row.col1}</TableCell>
                <TableCell>{row.col2}</TableCell>
                <TableCell>{row.col3}</TableCell>
                <TableCell>{row.col4}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Box>
  );
};

export default DummyComponent;