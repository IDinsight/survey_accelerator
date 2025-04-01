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
          className="mt-1 block w-full text-white placeholder-white/70 focus-visible:ring-transparent"
          required
        />
      </div>

      {/* Organization Select */}
      <div>
        <Label htmlFor="organization" className="block text-sm font-medium text-white">
          Filter Search (Optional)
        </Label>
        <Select name="organization">
        <SelectTrigger className="w-full mt-1 bg-[#111130] text-white focus-visible:ring-transparent">
          <SelectValue placeholder="Select Organization" className="text-white" />
        </SelectTrigger>
          <SelectContent className="bg-[#111130] text-white">
            <SelectGroup>
              <SelectLabel className="bg-[#111130] text-white">Organizations</SelectLabel>
              {organizations.map((org) => (
                <SelectItem key={org} value={org} className="text-white">
                  {org}
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
      </div>

      {/* Submit Button and Icon */}
      <div className="flex items-stretch mt-4 gap-5">
        <Button type="submit" className="w-[83%] bg-white text-black flex items-center justify-center">
          Search
        </Button>
        <Button
          type="button"
          title="Search history"
          className="w-[12%] bg-[#d29e01] text-white flex flex-col items-center justify-center p-2"
        >
          <YoutubeSearchedForIcon className="w-20 h-20" />
        </Button>
      </div>
    </form>
  );
};

export default SearchForm;
