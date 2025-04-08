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
}

export interface Match {
  page_number: number
  rank: number
  contextualized_chunk: string
  question?: string
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
