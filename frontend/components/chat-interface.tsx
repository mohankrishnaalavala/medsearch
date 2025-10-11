'use client';

import { useState, useRef, useEffect } from 'react';
import { Message, Citation, AgentStatus as AgentStatusType } from '@/lib/types';
import { MessageBubble } from './message-bubble';
import { AgentStatus } from './agent-status';
import { CitationCard } from './citation-card';
import { CitationDrawer } from './citation-drawer';
import { ConversationsSidebar } from './conversations-sidebar';
import { CitationExport } from './citation-export';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Loader2, Trash2, Paperclip, Mic } from 'lucide-react';
import { createSearch } from '@/lib/api';
import { createWebSocketClient, WebSocketClient } from '@/lib/websocket';
import type { WebSocketMessage } from '@/lib/websocket';
import { saveSearchHistoryItem } from '@/lib/utils/search-history';
import { SearchHistoryItem } from '@/lib/types/search-history';

// WS payload types and guards
type SearchProgressPayload = { search_id: string; current_step?: string; progress?: number };
type SearchCompletePayload = { search_id: string; final_response: string; citations?: Citation[] };
type SearchErrorPayload = { search_id: string; error?: string };
type AgentStartPayload = { agent_name: string; task: string };

type UnknownObject = Record<string, unknown>;
const extractPayload = (message: WebSocketMessage): unknown => (
  typeof message.payload !== 'undefined' ? message.payload : message.data
);
const hasProp = (obj: unknown, prop: string): boolean => !!obj && typeof obj === 'object' && prop in (obj as UnknownObject);
const isAgentStartPayload = (p: unknown): p is AgentStartPayload => hasProp(p, 'agent_name') && hasProp(p, 'task');
const isSearchProgressPayload = (p: unknown): p is SearchProgressPayload => hasProp(p, 'search_id');
const isSearchCompletePayload = (p: unknown): p is SearchCompletePayload => hasProp(p, 'search_id') && hasProp(p, 'final_response');
const isSearchErrorPayload = (p: unknown): p is SearchErrorPayload => hasProp(p, 'search_id') && hasProp(p, 'error');


// Known agents shown in the status panel
const KNOWN_AGENTS: AgentStatusType[] = [
  { name: 'Query Analyzer', status: 'idle', progress: 0, message: 'Waiting' },
  { name: 'Research Agent', status: 'idle', progress: 0, message: 'Waiting' },
  { name: 'Clinical Trials Agent', status: 'idle', progress: 0, message: 'Waiting' },
  { name: 'Drug Agent', status: 'idle', progress: 0, message: 'Waiting' },
  { name: 'Synthesis Agent', status: 'idle', progress: 0, message: 'Waiting' },
];

// Helper function to calculate average confidence from citations
const calculateAvgConfidence = (citations: Citation[]): number => {
  if (citations.length === 0) return 0;
  // For now, return a default confidence score
  // In the future, this could be calculated from actual citation metadata
  return 85;
};

// Helper function to extract unique sources from citations
const extractSources = (citations: Citation[]): string[] => {
  const sources = new Set<string>();
  citations.forEach((citation) => {
    // Map source_type to display name
    const sourceMap: Record<string, string> = {
      pubmed: 'PubMed',
      clinical_trial: 'Clinical Trials',
      drug_info: 'FDA',
    };
    const sourceName = sourceMap[citation.source_type] || citation.source_type;
    sources.add(sourceName);
  });
  return Array.from(sources);
};

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [agents, setAgents] = useState<AgentStatusType[]>([]);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [selectedCitation, setSelectedCitation] = useState<string | null>(null);
  const [isCitationOpen, setIsCitationOpen] = useState<boolean>(false);
  const [wsClient, setWsClient] = useState<WebSocketClient | null>(null);

  const [currentStep, setCurrentStep] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load conversation history from localStorage on mount
  useEffect(() => {
    const savedMessages = localStorage.getItem('medsearch_conversation');
    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages);
        // Limit to last 20 messages
        const recentMessages = parsed.slice(-20);
        setMessages(recentMessages);
      } catch (error) {
        console.error('Failed to load conversation history:', error);
      }
    }
  }, []);

  // Save conversation history to localStorage when messages change
  useEffect(() => {
    if (messages.length > 0) {
      // Limit to last 20 messages to avoid localStorage quota
      const recentMessages = messages.slice(-20);
      localStorage.setItem('medsearch_conversation', JSON.stringify(recentMessages));
    }
  }, [messages]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsClient) {
        wsClient.disconnect();
      }
    };
  }, [wsClient]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || isLoading) {
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setAgents(KNOWN_AGENTS);
    setCitations([]);

    try {
      // Prepare conversation history (last 5 messages for context)
      const conversationHistory = messages.slice(-10).map(msg => ({
        role: msg.role,
        content: msg.content,
      }));

      // Create search request
      const response = await createSearch({
        query: userMessage.content,
        max_results: 10,
        messages: conversationHistory,
      });

      // Create assistant message placeholder
      const assistantMessage: Message = {
        id: response.search_id,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Connect to WebSocket for real-time updates
      const client = createWebSocketClient(response.search_id);
      setWsClient(client);

      // Handle agent start
      client.on('agent_start', (message) => {
        const payload = extractPayload(message);
        if (!isAgentStartPayload(payload)) return;
        setAgents((prev) => {
          const exists = prev.some(a => a.name === payload.agent_name);
          const updated = prev.map(a => (
            a.name === payload.agent_name
              ? ({ ...a, status: 'running' as const, message: payload.task, progress: 0 })
              : a
          ));
          return exists
            ? updated
            : [...prev, { name: payload.agent_name, status: 'running' as const, progress: 0, message: payload.task }];
        });
      });

      // Handle search progress
      client.on('search_progress', (message) => {
        const payload = extractPayload(message);
        if (!isSearchProgressPayload(payload)) return;
        if (payload.search_id !== response.search_id) return; // ignore other sessions
        console.debug('Search progress:', payload);
        // Update step label
        if (payload.current_step) setCurrentStep(payload.current_step);
        // Update agent status based on current step
        if (payload.current_step) {
          setAgents((prev) =>
            prev.map((agent) => {
              if (payload.current_step && payload.current_step.includes(agent.name.toLowerCase())) {
                return { ...agent, status: 'running', progress: payload.progress ?? 0 };
              }
              return agent;
            })
          );
        }
      });

      // Handle search complete
      client.on('search_complete', (message) => {
        const payload = extractPayload(message);
        if (!isSearchCompletePayload(payload)) return;
        if (payload.search_id !== response.search_id) return; // ignore other sessions
        console.debug('Search complete:', payload);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === response.search_id
              ? {
                  ...msg,
                  content: payload.final_response,
                  citations: payload.citations || [],
                  isStreaming: false,
                }
              : msg
          )
        );
        // Sync citations sidebar for quick access
        setCitations(payload.citations || []);

        // Save to search history
        const searchHistoryItem: SearchHistoryItem = {
          id: response.search_id,
          query: userMessage.content,
          timestamp: new Date(),
          resultsCount: payload.citations?.length || 0,
          avgConfidence: calculateAvgConfidence(payload.citations || []),
          sources: extractSources(payload.citations || []),
          citations: payload.citations || [],
          isSaved: false,
        };
        saveSearchHistoryItem(searchHistoryItem);

        // Mark progress complete
        setCurrentStep('complete');
        setIsLoading(false);
        client.disconnect();
      });

      // Handle errors
      client.on('search_error', (message) => {
        const payload = extractPayload(message);
        if (!isSearchErrorPayload(payload)) return;
        if (payload.search_id !== response.search_id) return; // ignore other sessions
        console.error('WebSocket error:', payload);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === response.search_id
              ? {
                  ...msg,
                  content: `Error: ${payload.error || 'An error occurred during search'}`,
                  isStreaming: false,
                }
              : msg
          )
        );
        setIsLoading(false);
        client.disconnect();
      });

      // Connect to WebSocket
      await client.connect();
    } catch (error) {
      console.error('Error creating search:', error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: 'assistant',
          content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
          timestamp: new Date(),
        },
      ]);
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    if (confirm('Are you sure you want to clear the conversation history?')) {
      setMessages([]);
      setCitations([]);
      setAgents([]);
      localStorage.removeItem('medsearch_conversation');
    }
  };

  return (
    <div className="flex h-[calc(100vh-3.5rem)] bg-background">
      {/* Left conversations sidebar */}
      <ConversationsSidebar />

      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {/* Header with Clear History button - only show when messages exist */}
        {messages.length > 0 && (
          <div className="border-b border-border px-6 py-3 bg-background">
            <div className="max-w-4xl mx-auto flex justify-between items-center">
              <h2 className="text-base font-semibold">Conversation</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearHistory}
                className="gap-2 text-muted-foreground hover:text-foreground"
              >
                <Trash2 className="w-4 h-4" />
                Clear History
              </Button>
            </div>
          </div>
        )}

        {/* Messages */}
        <ScrollArea className="flex-1 p-6" ref={scrollRef}>
          {messages.length === 0 && !isLoading ? (
            <div className="flex flex-col items-center justify-center h-full max-w-4xl mx-auto">
              <div className="text-center space-y-4 mb-8">
                <h2 className="text-3xl font-bold">Welcome to MedSearch AI</h2>
                <p className="text-muted-foreground text-lg">
                  Ask me anything about medical research, clinical trials, or drug information.
                </p>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  onCitationClick={(id) => { setSelectedCitation(id); setIsCitationOpen(true); }}
                />
              ))}

              {/* Loading state with agent status */}
              {isLoading && (
                <div className="flex gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-muted">
                    <Loader2 className="h-5 w-5 text-foreground animate-spin" />
                  </div>
                  <div className="flex-1 space-y-3">
                    <div className="rounded-2xl px-4 py-3 bg-card border border-border max-w-3xl">
                      <div className="flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin text-primary" />
                        <p className="text-sm text-muted-foreground">
                          {currentStep || 'Analyzing your query...'}
                        </p>
                      </div>
                    </div>
                    {agents.length > 0 && <AgentStatus agents={agents} />}
                  </div>
                </div>
              )}
            </div>
          )}
        </ScrollArea>

        {/* Input */}
        <div className="border-t border-border bg-background p-6">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto space-y-4">
            <div className="relative">
              <Input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about treatments, clinical trials, drug interactions..."
                disabled={isLoading}
                className="pr-28 h-12"
                aria-label="Query input"
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  aria-label="Attach file"
                  onClick={() => console.debug('attach_clicked')}
                  disabled={isLoading}
                >
                  <Paperclip className="w-4 h-4" />
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  aria-label="Voice input"
                  onClick={() => console.debug('mic_clicked')}
                  disabled={isLoading}
                >
                  <Mic className="w-4 h-4" />
                </Button>
                <Button
                  type="submit"
                  size="icon"
                  className="h-8 w-8"
                  disabled={isLoading || !input.trim()}
                  aria-label="Send"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>
            <p className="text-xs text-muted-foreground text-center">
              MedSearch AI provides research assistance. Always verify critical medical decisions with current clinical guidelines.
            </p>
          </form>
        </div>
      </div>

      {/* Right citations sidebar */}
      <div className="hidden lg:block w-80 border-l border-border p-4 overflow-y-auto">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold">Active Citations</h3>
          <div className="flex items-center gap-2">
            {citations.length > 0 && <CitationExport citations={citations} size="sm" />}
            <span className="text-xs text-muted-foreground">{citations.length} sources</span>
          </div>
        </div>
        <div className="space-y-3">
          {citations.map((citation, index) => (
            <CitationCard
              key={citation.citation_id}
              citation={citation}
              index={index + 1}
              expanded={selectedCitation === citation.citation_id}
              onToggle={() => {
                const newId = selectedCitation === citation.citation_id ? null : citation.citation_id;
                setSelectedCitation(newId);
                setIsCitationOpen(!!newId);
              }}
            />
          ))}
        </div>
      </div>

      {/* Citation Drawer */}
      <CitationDrawer
        open={isCitationOpen}
        citation={selectedCitation ? citations.find(c => c.citation_id === selectedCitation) ?? null : null}
        onClose={() => setIsCitationOpen(false)}
      />
    </div>
  );
}

