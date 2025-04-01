import React, { FC } from "react";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { Label } from "../components/ui/label";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import YoutubeSearchedForIcon from "@mui/icons-material/YoutubeSearchedFor";

interface SearchFormProps {
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
}

const organizations = ["IDHS", "IDinsight", "National Statistics Bureau", "UNICEF", "USAID", "World Bank"];
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
];

const SearchForm: FC<SearchFormProps> = ({ onSubmit }) => {
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
          className="mt-1 block w-full text-white mt-2 placeholder-white/70 focus-visible:ring-transparent"
          required
        />
      </div>

      {/* Organization Select */}
      <div>
        <Label htmlFor="organization" className="block text-sm font-medium text-white">
          Filter Search (Optional)
        </Label>
        <Select name="organization">
        <SelectTrigger className="w-full mt-2 mb-2.5 bg-[#111130] text-white focus-visible:ring-transparent">
          <SelectValue placeholder="Select Organization" className="text-white focus-visible:ring-transparent" />
        </SelectTrigger>
          <SelectContent className="bg-[#111130] text-white focus-visible:ring-transparent">
            <SelectGroup>
              {organizations.map((org) => (
                <SelectItem key={org} value={org} className="text-white focus-visible:ring-transparent">
                  {org}
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
        <Select name="surveyType">
          <SelectTrigger className="w-full mt-1 bg-[#111130] text-white">
            <SelectValue placeholder="Select Survey Type" className="text-white" />
          </SelectTrigger>
          <SelectContent className="bg-[#111130] text-white">
            <SelectGroup>
              {surveytypes.map((type) => (
                <SelectItem key={type} value={type} className="text-white">
                  {type}
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
      </div>

      {/* Submit Button and Icon */}
      <div className="flex items-stretch mt-4 gap-3.5">
        <Button type="submit" className="w-[83%] bg-white text-black flex items-center justify-center">
          Search
        </Button>
        <Button
          type="button"
          title="Search history"
          className="w-[13.5%] bg-[#d29e01] text-white flex flex-col items-center justify-center p-2"
        >
          <YoutubeSearchedForIcon className="w-20 h-20" />
        </Button>
      </div>
    </form>
  );
};

export default SearchForm;
