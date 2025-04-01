import React, { FC } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { DocumentSearchResult } from "../interfaces";

interface SearchResultCardProps {
  result: DocumentSearchResult;
  onClick: (result: DocumentSearchResult) => void;
  isSelected: boolean;
}

const SearchResultCard: FC<SearchResultCardProps> = ({ result, onClick, isSelected }) => {
  const matchType = "Matches";

  return (
    <Card
      onClick={() => onClick(result)}
      className={`cursor-pointer transition-colors duration-200 ${
        isSelected ? "bg-[#CC7722]" : "bg-[#4169E1] hover:bg-[#000080]"
      }`}
    >
      <CardHeader>
        <CardTitle className="text-lg font-semibold">
          {result.metadata.title} ({result.metadata.year})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm">
          Region: {result.metadata.regions?.join(", ") || "N/A"}, Country:{" "}
          {result.metadata.countries?.join(", ") || "N/A"}, Org:{" "}
          {result.metadata.organizations?.join(", ") || "N/A"}
        </p>
        <p className="text-sm mt-2">{result.metadata.summary}</p>
        <p className="text-sm mt-2">
          <strong>{matchType}:</strong> {result.matches.length}
        </p>
      </CardContent>
    </Card>
  );
};

export default SearchResultCard;
