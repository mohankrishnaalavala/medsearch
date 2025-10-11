import { Citation } from './index';

export interface SearchHistoryItem {
  id: string;
  query: string;
  timestamp: Date;
  resultsCount: number;
  avgConfidence: number;
  sources: string[];
  citations: Citation[];
  isSaved: boolean;
  conversationId?: string;
}

export interface SearchFilters {
  dateRange?: {
    start: Date;
    end: Date;
  };
  sources?: ('pubmed' | 'clinical_trials' | 'fda')[];
  minConfidence?: number;
  sortBy?: 'date' | 'relevance' | 'confidence';
}

export interface ConversationMetadata {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  lastQuery?: string;
}

