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
  // Optional coarse year range, used for URL params
  year_range?: {
    start?: number;
    end?: number;
  };
  sources?: ('pubmed' | 'clinical_trials' | 'fda')[];
  study_types?: string[];
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

