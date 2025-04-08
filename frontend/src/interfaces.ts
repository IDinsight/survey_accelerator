export interface DocumentSearchResult {
  metadata: {
    title: string
    summary?: string
    year: string
    regions?: string[]
    countries?: string[]
    organizations?: string[]
    id: number
    pdf_url?: string
    highlighted_pdf_url?: string
  }
  matches: Match[]
  num_matches?: number
  strongMatchesCount?: number
}

export interface Match {
  page_number: number
  rank: number
  contextualized_chunk?: string
  explanation: string
  starting_keyphrase?: string
  strength?: "strong" | "moderate" | "weak"
}

export interface MatchedChunk {
  page_number: number
  rank: number
  explanation: string
}

export interface MatchedQAPair {
  page_number: number
  rank: number
  question: string
  answer: string
}

// Helper function to determine match strength based on rank
export function getMatchStrength(rank: number): "strong" | "moderate" | "weak" {
  if (rank <= 12) return "strong"
  if (rank <= 20) return "moderate"
  return "weak"
}
