"use client"

import type React from "react"
import { type FC, useState, useRef, useEffect } from "react"
import { Input } from "../components/ui/input"
import { Button } from "../components/ui/button"
import { Label } from "../components/ui/label"
import { Check, ChevronDown, Loader2 } from "lucide-react"
import { cn } from "../lib/utils"
import YoutubeSearchedForIcon from "@mui/icons-material/YoutubeSearchedFor"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../components/ui/tooltip"

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

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      {/* Search Query Input */}
      <div>
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
                onClick={onHistoryClick}
                className="w-[13.5%] bg-[#cc7722] text-white flex flex-col items-center justify-center p-2"
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
    </form>
  )
}

export default SearchForm
