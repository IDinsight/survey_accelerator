// interfaces.ts

export interface Metadata {
    id: number;
    file_id: string;
    file_name: string;
    title: string;
    summary: string;
    pdf_url: string;
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
  }

  export interface MatchedQAPair {
    page_number: number;
    question: string;
    answer: string;
    relevance_score: number;
    rank: number;
  }

  export interface DocumentSearchResult {
    metadata: Metadata;
    matches: (MatchedChunk | MatchedQAPair)[];
  }

  export type Match = MatchedChunk | MatchedQAPair;
