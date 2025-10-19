/**
 * API client for MedSearch AI backend
 */

// Use relative URL in production (works through nginx proxy)
// Use localhost in development
const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
  ? '' // Relative URL for production (nginx will proxy /api to backend)
  : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');

export interface SearchRequest {
  query: string;
  max_results?: number;
  messages?: Array<{
    role: 'user' | 'assistant';
    content: string;
  }>;
  context?: {
    conversation_id?: string;
    previous_queries?: string[];
  };
}

export interface SearchResponse {
  search_id: string;
  status: string;
  estimated_time: number;
  message: string;
}

export interface Citation {
  citation_id: string;
  source_type: 'pubmed' | 'clinical_trial' | 'drug_info';
  title: string;
  authors?: string[];
  journal?: string;
  publication_date?: string;
  doi?: string;
  pmid?: string;
  nct_id?: string;
  url?: string;
  snippet: string;
  relevance_score: number;
}

export interface SearchResult {
  search_id: string;
  query: string;
  final_response: string;
  citations: Citation[];
  confidence_score: number;
  execution_time: number;
  agents_used: string[];
  created_at: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  environment: string;
  services: {
    elasticsearch: {
      status: string;
      latency_ms: number | null;
      message: string | null;
    };
    redis: {
      status: string;
      latency_ms: number | null;
      message: string | null;
    };
    vertex_ai: {
      status: string;
      latency_ms: number | null;
      message: string | null;
    };
  };
  timestamp: string;
}

/**
 * Create a new search request
 */
export async function createSearch(request: SearchRequest): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Get search result by ID
 */
export async function getSearchResult(searchId: string): Promise<SearchResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/search/${searchId}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Get health status
 */
export async function getHealthStatus(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Export search results as PDF
 */
export async function exportSearchAsPDF(searchId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/v1/search/${searchId}/export/pdf`);

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.blob();
}

/**
 * Export citations as BibTeX
 */
export async function exportCitationsAsBibTeX(searchId: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/v1/search/${searchId}/export/bibtex`);

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.text();
}

