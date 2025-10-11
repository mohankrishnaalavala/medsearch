import { SearchHistoryItem, ConversationMetadata } from '../types/search-history';

const SEARCH_HISTORY_KEY = 'medsearch_search_history';
const CONVERSATIONS_KEY = 'medsearch_conversations';
const MAX_HISTORY_ITEMS = 50;

/**
 * Get search history from localStorage
 */
export function getSearchHistory(): SearchHistoryItem[] {
  try {
    const stored = localStorage.getItem(SEARCH_HISTORY_KEY);
    if (!stored) return [];

    const items = JSON.parse(stored) as SearchHistoryItem[];
    // Convert timestamp strings back to Date objects
    return items.map((item) => ({
      ...item,
      timestamp: new Date(item.timestamp),
    }));
  } catch (error) {
    console.error('Failed to load search history:', error);
    return [];
  }
}

/**
 * Save search history item to localStorage
 */
export function saveSearchHistoryItem(item: SearchHistoryItem): void {
  try {
    const history = getSearchHistory();
    
    // Add new item at the beginning
    history.unshift(item);
    
    // Keep only the most recent items
    const trimmed = history.slice(0, MAX_HISTORY_ITEMS);
    
    localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(trimmed));
  } catch (error) {
    console.error('Failed to save search history:', error);
  }
}

/**
 * Toggle saved status of a search history item
 */
export function toggleSavedSearch(searchId: string): void {
  try {
    const history = getSearchHistory();
    const updated = history.map((item) =>
      item.id === searchId ? { ...item, isSaved: !item.isSaved } : item
    );
    localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(updated));
  } catch (error) {
    console.error('Failed to toggle saved search:', error);
  }
}

/**
 * Delete a search history item
 */
export function deleteSearchHistoryItem(searchId: string): void {
  try {
    const history = getSearchHistory();
    const filtered = history.filter((item) => item.id !== searchId);
    localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(filtered));
  } catch (error) {
    console.error('Failed to delete search history item:', error);
  }
}

/**
 * Clear all search history
 */
export function clearSearchHistory(): void {
  try {
    localStorage.removeItem(SEARCH_HISTORY_KEY);
  } catch (error) {
    console.error('Failed to clear search history:', error);
  }
}

/**
 * Get saved searches only
 */
export function getSavedSearches(): SearchHistoryItem[] {
  return getSearchHistory().filter((item) => item.isSaved);
}

/**
 * Get conversations metadata
 */
export function getConversations(): ConversationMetadata[] {
  try {
    const stored = localStorage.getItem(CONVERSATIONS_KEY);
    if (!stored) return [];

    const conversations = JSON.parse(stored) as ConversationMetadata[];
    return conversations.map((conv) => ({
      ...conv,
      createdAt: new Date(conv.createdAt),
      updatedAt: new Date(conv.updatedAt),
    }));
  } catch (error) {
    console.error('Failed to load conversations:', error);
    return [];
  }
}

/**
 * Save conversation metadata
 */
export function saveConversation(conversation: ConversationMetadata): void {
  try {
    const conversations = getConversations();
    const existingIndex = conversations.findIndex((c) => c.id === conversation.id);

    if (existingIndex >= 0) {
      conversations[existingIndex] = conversation;
    } else {
      conversations.unshift(conversation);
    }

    localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(conversations));
  } catch (error) {
    console.error('Failed to save conversation:', error);
  }
}

/**
 * Delete a conversation
 */
export function deleteConversation(conversationId: string): void {
  try {
    const conversations = getConversations();
    const filtered = conversations.filter((c) => c.id !== conversationId);
    localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(filtered));
  } catch (error) {
    console.error('Failed to delete conversation:', error);
  }
}

/**
 * Rename a conversation
 */
export function renameConversation(conversationId: string, newTitle: string): void {
  try {
    const conversations = getConversations();
    const updated = conversations.map((c) =>
      c.id === conversationId
        ? { ...c, title: newTitle, updatedAt: new Date() }
        : c
    );
    localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
  } catch (error) {
    console.error('Failed to rename conversation:', error);
  }
}

