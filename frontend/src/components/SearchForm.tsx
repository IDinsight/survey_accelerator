"use client"

import type React from "react"
import { type FC, useState, useRef, useEffect } from "react"
import { Input } from "../components/ui/input"
import { Button } from "../components/ui/button"
import { Label } from "../components/ui/label"
import { Check, ChevronDown, Loader2, Clock, X } from "lucide-react"
import { cn } from "../lib/utils"
import YoutubeSearchedForIcon from "@mui/icons-material/YoutubeSearchedFor"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../components/ui/tooltip"
import axios from "axios"
import { toast } from "sonner"

interface SearchFormProps {
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void
  loading: boolean
  onHistoryClick?: () => void
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
        "relative flex cursor-pointer select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm text-white hover:bg-[#1e1e4a]",
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
}> = ({ options, selectedOptions, onChange, placeholder, label }) => {
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

  return (
    <div className="relative" ref={dropdownRef}>
      <Button
        type="button"
        variant="outline"
        className="w-full justify-between text-white"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span>
          {selectedOptions.length > 0
            ? `${selectedOptions.length} ${label.toLowerCase()}${selectedOptions.length > 1 ? "s" : ""} selected`
            : placeholder}
        </span>
        <ChevronDown className="h-4 w-4 opacity-50" />
      </Button>

      {isOpen && (
        <div className="absolute z-[100] mt-1 w-full rounded-md border border-gray-700 bg-[#111130] shadow-lg">
          <div className="py-2 px-3 text-sm font-medium text-white">{label}</div>
          <div className="border-t border-gray-700"></div>
          <div className="max-h-[300px] overflow-y-auto">
            {options.map((option) => (
              <CustomCheckbox
                key={option}
                checked={selectedOptions.includes(option)}
                onChange={() => toggleOption(option)}
              >
                {option}
              </CustomCheckbox>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

const organizations = ["IDHS", "IDinsight", "National Statistics Bureau", "UNICEF", "USAID", "World Bank"]

const surveytypes = [
  "DHS Survey",
  "DOH HPLS Round 1",
  "DOH HPLS Round 2",
  "DOH HPLS Round 3",
  "DOH HPLS Round 4",
  "Global Findex Survey 2021",
  "IHDS Round 2",
  "LSMS-ISA ESS Wave 4",
  "LSMS-ISA GHS Panel Year 4",
  "LSMS-ISA TZNPS Year 4",
  "LSMS-ISA UNPS 2019-20",
  "MICS7 Base Questionnaire",
  "MICS7 Complementary Questionnaires",
  "National household income and expenditure survey",
  "National labor force survey",
  "SPA Questionnaire",
  "TKPI Round 1",
  "UNICEF WaSHPALS Handwashing Nudges Evaluation",
  "Village Enterprise Development Impact Bond (VE DIB) Evaluation",
]

const SearchForm: FC<SearchFormProps> = ({ onSubmit, loading, onHistoryClick }) => {
  const [selectedOrgs, setSelectedOrgs] = useState<string[]>([])
  const [selectedSurveyTypes, setSelectedSurveyTypes] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [showHistory, setShowHistory] = useState(false)
  const [searchHistory, setSearchHistory] = useState<string[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const historyRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const backendUrl = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000"

  // Handle clicks outside the history dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (historyRef.current && !historyRef.current.contains(event.target as Node)) {
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
    onSubmit(e)
    setShowHistory(false)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Search Query Input */}
      <div className="relative">
        <Label htmlFor="search" className="block text-sm font-medium text-white focus-visible:ring-transparent">
          Search Query
        </Label>
        <Input
          id="search"
          name="search"
          type="text"
          placeholder="Enter your search query"
          className="mt-1 block w-full text-white placeholder-white/70 focus-visible:ring-transparent"
          required
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          ref={searchInputRef}
        />
      </div>

      {/* Organizations Dropdown */}
      <div>
        <CustomDropdown
          options={organizations}
          selectedOptions={selectedOrgs}
          onChange={setSelectedOrgs}
          placeholder="Select Organizations"
          label="Organization"
        />
        {/* Hidden input to submit selected organizations */}
        <input type="hidden" name="organization" value={selectedOrgs.join(",")} />
      </div>

      {/* Survey Type Dropdown */}
      <div>
        <CustomDropdown
          options={surveytypes}
          selectedOptions={selectedSurveyTypes}
          onChange={setSelectedSurveyTypes}
          placeholder="Select Survey Types"
          label="Survey Type"
        />
        {/* Hidden input to submit selected survey types */}
        <input type="hidden" name="surveyType" value={selectedSurveyTypes.join(",")} />
      </div>

      {/* Submit and History Buttons */}
      <div className="flex items-stretch mt-4 gap-3.5">
        <Button
          type="submit"
          className="relative w-[83%] bg-white text-black flex items-center justify-center"
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              <span>Searching...</span>
            </>
          ) : (
            <span>Search</span>
          )}
        </Button>

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                onClick={handleHistoryClick}
                className={`w-[13.5%] ${
                  showHistory ? "bg-[#a05e1b]" : "bg-[#cc7722]"
                } text-white flex flex-col items-center justify-center p-2`}
              >
                <YoutubeSearchedForIcon className="w-20 h-20" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Search history</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Search History Dropdown */}
      {showHistory && (
        <div
          ref={historyRef}
          className="absolute z-[100] mt-1 w-full rounded-md border border-gray-700 bg-[#111130] shadow-lg"
          style={{ marginTop: "0.5rem" }}
        >
          <div className="flex justify-between items-center py-2 px-3 text-sm font-medium text-white border-b border-gray-700">
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
                  className="flex items-center py-2 px-3 text-sm text-white hover:bg-[#1e1e4a] cursor-pointer"
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
    </form>
  )
}

export default SearchForm
