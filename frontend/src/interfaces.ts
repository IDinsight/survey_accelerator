// interfaces.ts

export interface Metadata {
  id: number;
  file_name: string;
  title: string;
  summary: string;
  pdf_url: string;
  highlighted_pdf_url?: string; // URL to the PDF with search term highlights already added
  countries: string[];
  organizations: string[];
  regions: string[];
  year: number;
}

export interface MatchedChunk {
  page_number: number;
  contextualized_chunk: string;
  relevance_score: number;
  rank: number;
  explanation: string;
  starting_keyphrase: string;
}

export interface MatchedQAPair {
  page_number: number;
  question: string;
  answer: string;
  relevance_score: number;
  rank: number;
}

// Legacy interface for backward compatibility
export interface DocumentSearchResult {
  metadata: Metadata;
  matches: (MatchedChunk | MatchedQAPair)[];
  num_matches?: number;
}

// New interfaces for separate search types
export interface GenericDocumentSearchResult {
  metadata: Metadata;
  matches: MatchedChunk[];
  num_matches: number;
}


export type Match = MatchedChunk | MatchedQAPair;

// Response types for the API
export interface GenericSearchResponse {
  query: string;
  results: GenericDocumentSearchResult[];
  message?: string;
}