/**
 * Type definitions for MedSearch AI
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: Date;
  isStreaming?: boolean;
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

export interface AgentStatus {
  name: string;
  status: 'idle' | 'running' | 'complete' | 'error';
  progress: number;
  message: string;
  execution_time?: number;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  created_at: Date;
  updated_at: Date;
}

export interface SearchSession {
  search_id: string;
  query: string;
  status: 'processing' | 'complete' | 'error';
  agents: AgentStatus[];
  citations: Citation[];
  final_response?: string;
  confidence_score?: number;
  execution_time?: number;
}

