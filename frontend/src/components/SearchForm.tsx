"use client"

import type React from "react"
import { type FC, useState, useRef, useEffect } from "react"
import { Input } from "../components/ui/input"
import { Button } from "../components/ui/button"
import { Label } from "../components/ui/label"
import { Check, ChevronDown, Loader2, Clock, X, ChevronUp } from 'lucide-react'
import { cn } from "../lib/utils"
import YoutubeSearchedForIcon from "@mui/icons-material/YoutubeSearchedFor"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../components/ui/tooltip"
import axios from "axios"
import { toast } from "sonner"
import "../styles/dropdown.css"
import { fetchOrganizations, fetchSurveyTypes } from "../api"

interface SearchFormProps {
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void
  loading: boolean
  onHistoryClick?: () => void
  onClear?: () => void
}

// Custom checkbox component
const CustomCheckbox: FC<{
  checked: boolean
  onChange: (checked: boolean) => void
  children: React.ReactNode
  disabled?: boolean
}> = ({ checked, onChange, children, disabled }) => {
  return (
    <div
      className={cn(
        "relative flex cursor-pointer select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm text-white hover:bg-white/15 dropdown-item",
        disabled && "opacity-50 cursor-not-allowed",
      )}
      onClick={() => {
        if (!disabled) {
          onChange(!checked)
        }
      }}
    >
      <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
        {checked ? <Check className="h-4 w-4 text-white" /> : null}
      </span>
      {children}
    </div>
  )
}

// Custom dropdown component
const CustomDropdown: FC<{
  options: string[]
  selectedOptions: string[]
  onChange: (selected: string[]) => void
  placeholder: string
  label: string
  isLoading?: boolean
}> = ({ options, selectedOptions, onChange, placeholder, label, isLoading = false }) => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Handle clicks outside the dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [])

  const toggleOption = (option: string) => {
    if (selectedOptions.includes(option)) {
      onChange(selectedOptions.filter((item) => item !== option))
    } else {
      onChange([...selectedOptions, option])
    }
  }

  const clearAll = () => {
    onChange([])
  }

  return (
    <div className="dropdown-container" ref={dropdownRef}>
      <Button
        type="button"
        variant="outline"
        className="w-full justify-between text-white"
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
      >
        {isLoading ? (
          <span className="flex items-center">
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Loading...
          </span>
        ) : (
          <span>
            {selectedOptions.length > 0
              ? `${selectedOptions.length} ${label.toLowerCase()}${selectedOptions.length > 1 ? "s" : ""} selected`
              : placeholder}
          </span>
        )}
        <ChevronDown className="h-4 w-4 opacity-50" />
      </Button>

      {isOpen && !isLoading && (
        <div className="dropdown-menu">
          <div className="flex items-center justify-between py-2 px-3 text-sm font-medium text-white">
            <span>{label}</span>
            {selectedOptions.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-xs text-white hover:bg-white/10"
                onClick={clearAll}
              >
                Clear all
              </Button>
            )}
          </div>
          <div className="border-t border-white/20"></div>
          <div className="max-h-[300px] overflow-y-auto">
            {options.length > 0 ? (
              options.map((option) => (
                <CustomCheckbox
                  key={option}
                  checked={selectedOptions.includes(option)}
                  onChange={() => toggleOption(option)}
                >
                  {option}
                </CustomCheckbox>
              ))
            ) : (
              <div className="py-3 px-3 text-sm text-white/70 text-center">No options available</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

const SearchForm: FC<SearchFormProps> = ({ onSubmit, loading, onHistoryClick, onClear }) => {
  const [selectedOrgs, setSelectedOrgs] = useState<string[]>([])
  const [selectedSurveyTypes, setSelectedSurveyTypes] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [showHistory, setShowHistory] = useState(false)
  const [searchHistory, setSearchHistory] = useState<string[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [organizations, setOrganizations] = useState<string[]>([])
  const [surveyTypes, setSurveyTypes] = useState<string[]>([])
  const [isLoadingOptions, setIsLoadingOptions] = useState(true)
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false)
  const historyRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const backendUrl = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000"

  // Fetch organizations and survey types on component mount
  useEffect(() => {
    const fetchOptions = async () => {
      setIsLoadingOptions(true)
      try {
        const [orgsData, typesData] = await Promise.all([
          fetchOrganizations(),
          fetchSurveyTypes()
        ]);

        setOrganizations(orgsData);
        setSurveyTypes(typesData);
      } catch (error) {
        console.error("Error fetching dropdown options:", error);
        toast.error("Failed to load dropdown options.");
        setOrganizations([]);
        setSurveyTypes([]);
      } finally {
        setIsLoadingOptions(false);
      }
    };

    fetchOptions();
  }, []);

  // Handle clicks outside the history dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        historyRef.current &&
        !historyRef.current.contains(event.target as Node) &&
        !(event.target as Element).closest(".history-button")
      ) {
        setShowHistory(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [])

  const fetchSearchHistory = async () => {
    setLoadingHistory(true)
    try {
      const token = localStorage.getItem("token")
      if (!token) {
        throw new Error("Authentication token not found")
      }

      const response = await axios.get(`${backendUrl}/search/search-history`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      })

      setSearchHistory(response.data || [])
    } catch (error) {
      console.error("Error fetching search history:", error)
      toast.error("Failed to load search history")
    } finally {
      setLoadingHistory(false)
    }
  }

  const handleHistoryClick = () => {
    if (!showHistory) {
      fetchSearchHistory()
    }
    setShowHistory(!showHistory)
    if (onHistoryClick) {
      onHistoryClick()
    }
  }

  const handleHistoryItemClick = (query: string) => {
    setSearchQuery(query)
    setShowHistory(false)
    if (searchInputRef.current) {
      searchInputRef.current.focus()
    }
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    // Add the selected organizations and survey types to the form data
    const formElement = e.currentTarget as HTMLFormElement;

    // Create hidden fields for the arrays if they don't exist
    const orgsField = formElement.querySelector('input[name="organizations"]');
    if (!orgsField) {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'organizations';
      input.value = JSON.stringify(selectedOrgs);
      formElement.appendChild(input);
    } else {
      (orgsField as HTMLInputElement).value = JSON.stringify(selectedOrgs);
    }

    const typesField = formElement.querySelector('input[name="survey_types"]');
    if (!typesField) {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'survey_types';
      input.value = JSON.stringify(selectedSurveyTypes);
      formElement.appendChild(input);
    } else {
      (typesField as HTMLInputElement).value = JSON.stringify(selectedSurveyTypes);
    }

    onSubmit(e)
    setShowHistory(false)
  }

  const handleClear = () => {
    setSearchQuery("")
    setSelectedOrgs([])
    setSelectedSurveyTypes([])

    // Call the parent's onClear if provided
    if (onClear) {
      onClear()
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Search Query Input */}
      <div className="dropdown-container">
        <Label htmlFor="search" className="block text-sm font-medium text-white">
          Search
        </Label>
        <div className="relative mt-1">
          <Input
            id="search"
            name="search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Enter your search term"
            className="pr-20 text-white placeholder-white/70 focus-visible:ring-transparent"
            required
            ref={searchInputRef}
            autoComplete="off"
          />
          <div className="absolute inset-y-0 right-0 flex items-center">
            {/* History Button */}
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    onClick={handleHistoryClick}
                    className={`h-8 w-8 mr-1 rounded-full ${
                      showHistory ? "bg-[#a05e1b]" : "bg-transparent"
                    } hover:bg-[#cc7722]/20 flex items-center justify-center history-button`}
                  >
                    <YoutubeSearchedForIcon className="h-4 w-4 text-white/70 hover:text-white" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Search history</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            {/* Clear Button */}
            {searchQuery && (
              <Button
                type="button"
                onClick={() => setSearchQuery("")}
                className="h-8 w-8 rounded-full bg-transparent hover:bg-white/10 flex items-center justify-center"
              >
                <X className="h-4 w-4 text-white/70" />
              </Button>
            )}
          </div>
        </div>

        {/* Search History Dropdown */}
        {showHistory && (
          <div ref={historyRef} className="history-dropdown">
            <div className="flex justify-between items-center py-2 px-3 text-sm font-medium text-white border-b border-white/20">
              <span>Recent Searches</span>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 text-white/70 hover:text-white hover:bg-transparent"
                onClick={() => setShowHistory(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="max-h-[300px] overflow-y-auto">
              {loadingHistory ? (
                <div className="flex justify-center items-center py-4">
                  <Loader2 className="h-5 w-5 animate-spin text-white/70" />
                </div>
              ) : searchHistory.length > 0 ? (
                searchHistory.map((query, index) => (
                  <div
                    key={index}
                    className="flex items-center py-2 px-3 text-sm text-white hover:bg-white/10 cursor-pointer dropdown-item"
                    onClick={() => handleHistoryItemClick(query)}
                  >
                    <Clock className="h-4 w-4 mr-2 text-white/70" />
                    <span className="truncate">{query}</span>
                  </div>
                ))
              ) : (
                <div className="py-3 px-3 text-sm text-white/70 text-center">No recent searches</div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Advanced Settings Toggle */}
      <div className="flex justify-center items-center my-2">
        <Button
          type="button"
          variant="outline"
          className="bg-black/70 text-white hover:bg-black/90 text-sm px-4 py-1 h-auto flex items-center gap-2 border-gray-700"
          onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
        >
          <span>Advanced settings</span>
          {showAdvancedSettings ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </Button>
        {(selectedOrgs.length > 0 || selectedSurveyTypes.length > 0) && (
          <span className="text-xs text-white/70 ml-2">
            {selectedOrgs.length + selectedSurveyTypes.length} filter{selectedOrgs.length + selectedSurveyTypes.length !== 1 ? 's' : ''} applied
          </span>
        )}
      </div>

      {/* Advanced Settings Section */}
      {showAdvancedSettings && (
        <div className="p-4 bg-black/10 backdrop-blur-lg rounded-lg border border-white/30 relative z-[60]">
          {/* Organizations Dropdown */}
          <div className="mb-4">
            <Label className="block text-sm font-medium text-white mb-1">Organizations</Label>
            <CustomDropdown
              options={organizations}
              selectedOptions={selectedOrgs}
              onChange={setSelectedOrgs}
              placeholder="Filter by Organizations (Optional)"
              label="Organization"
              isLoading={isLoadingOptions}
            />
          </div>

          {/* Survey Type Dropdown */}
          <div>
            <Label className="block text-sm font-medium text-white mb-1">Survey Types</Label>
            <CustomDropdown
              options={surveyTypes}
              selectedOptions={selectedSurveyTypes}
              onChange={setSelectedSurveyTypes}
              placeholder="Filter by Survey Types (Optional)"
              label="Survey Type"
              isLoading={isLoadingOptions}
            />
          </div>
        </div>
      )}

      {/* Submit and Clear Buttons */}
      <div className="flex items-stretch mt-4 gap-3">
        <Button
          type="submit"
          className="relative flex-1 bg-white text-black hover:bg-gray-200 flex items-center justify-center"
          disabled={loading || isLoadingOptions}
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Searching...
            </>
          ) : (
            "Search"
          )}
        </Button>

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                onClick={handleClear}
                className="w-20 bg-yellow-500 text-black hover:bg-yellow-400 flex items-center justify-center"
              >
                <span>Clear</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Clear all filters and results</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </form>
  )
}

export default SearchForm
