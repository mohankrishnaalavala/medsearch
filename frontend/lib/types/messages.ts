/**
 * WebSocket message type definitions for MedSearch AI
 * Based on technical specification from medsearch-technical-spec.md
 */

// ============================================================================
// Client -> Server Messages
// ============================================================================

export interface SearchRequest {
  type: 'search_start';
  payload: {
    query: string;
    search_id: string;
    filters?: SearchFilters;
    context?: ConversationContext;
  };
}

export interface SearchCancel {
  type: 'search_cancel';
  payload: {
    search_id: string;
  };
}

export interface KeepAlive {
  type: 'ping';
  payload: {
    timestamp: number;
  };
}

export type ClientMessage = SearchRequest | SearchCancel | KeepAlive;

// ============================================================================
// Server -> Client Messages
// ============================================================================

export interface SearchProgress {
  type: 'search_progress';
  payload: {
    search_id: string;
    agent: string;
    status: 'started' | 'completed' | 'failed';
    progress: number; // 0-100
    message?: string;
  };
}

export interface SearchResult {
  type: 'search_result';
  payload: {
    search_id: string;
    content: string;
    citations: Citation[];
    confidence: number;
    is_final: boolean;
    agent_source: string;
  };
}

export interface SearchError {
  type: 'search_error';
  payload: {
    search_id: string;
    error: string;
    error_code: string;
    retry_possible: boolean;
    agent?: string;
  };
}

export interface SearchComplete {
  type: 'search_complete';
  payload: {
    search_id: string;
    final_response: string;
    total_citations: number;
    confidence_score: number;
    execution_time: number;
    agents_used: string[];
  };
}

export interface KeepAliveResponse {
  type: 'pong';
  payload: {
    timestamp: number;
  };
}

export type ServerMessage =
  | SearchProgress
  | SearchResult
  | SearchError
  | SearchComplete
  | KeepAliveResponse;

// ============================================================================
// Supporting Types
// ============================================================================

export interface SearchFilters {
  date_range?: {
    start: string;
    end: string;
  };
  study_types?: string[];
  locations?: string[];
  languages?: string[];
}

export interface ConversationContext {
  previous_queries: string[];
  entities_mentioned: Record<string, string[]>;
  conversation_id: string;
}

export interface Citation {
  id: string;
  source_type: 'pubmed' | 'clinical_trial' | 'fda_drug';
  title: string;
  authors?: string[];
  journal?: string;
  publication_date?: string;
  doi?: string;
  pmid?: string;
  nct_id?: string;
  abstract?: string;
  relevance_score: number;
  confidence_score: number;
}

// ============================================================================
// Error Codes
// ============================================================================

export const ERROR_CODES = {
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',
  SEARCH_TIMEOUT: 'SEARCH_TIMEOUT',
  AGENT_FAILURE: 'AGENT_FAILURE',
  ELASTICSEARCH_ERROR: 'ELASTICSEARCH_ERROR',
  VERTEX_AI_ERROR: 'VERTEX_AI_ERROR',
  WEBSOCKET_ERROR: 'WEBSOCKET_ERROR',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
} as const;

export type ErrorCode = (typeof ERROR_CODES)[keyof typeof ERROR_CODES];

