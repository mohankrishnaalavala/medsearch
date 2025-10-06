'use client';

import { useState, useRef, useEffect } from 'react';
import { Message, Citation, AgentStatus as AgentStatusType } from '@/lib/types';
import { MessageBubble } from './message-bubble';
import { AgentStatus } from './agent-status';
import { CitationCard } from './citation-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Loader2, Trash2 } from 'lucide-react';
import { createSearch } from '@/lib/api';
import { createWebSocketClient, WebSocketClient } from '@/lib/websocket';
import type { WebSocketMessage } from '@/lib/websocket';

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


export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [agents, setAgents] = useState<AgentStatusType[]>([]);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [selectedCitation, setSelectedCitation] = useState<string | null>(null);
  const [wsClient, setWsClient] = useState<WebSocketClient | null>(null);

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
    setAgents([]);
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
        setAgents((prev) => [
          ...prev,
          {
            name: payload.agent_name,
            status: 'running',
            progress: 0,
            message: payload.task,
          },
        ]);
      });

      // Handle search progress
      client.on('search_progress', (message) => {
        const payload = extractPayload(message);
        if (!isSearchProgressPayload(payload)) return;
        if (payload.search_id !== response.search_id) return; // ignore other sessions
        console.debug('Search progress:', payload);
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
    <div className="flex h-screen bg-background">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {/* Header with Clear History button */}
        {messages.length > 0 && (
          <div className="border-b border-border p-4">
            <div className="max-w-4xl mx-auto flex justify-between items-center">
              <h2 className="text-lg font-semibold">Conversation History</h2>
              <Button
                variant="outline"
                size="sm"
                onClick={handleClearHistory}
                className="gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Clear History
              </Button>
            </div>
          </div>
        )}

        {/* Messages */}
        <ScrollArea className="flex-1 p-4" ref={scrollRef}>
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <h2 className="text-2xl font-bold mb-2">Welcome to MedSearch AI</h2>
                <p className="text-muted-foreground">
                  Ask me anything about medical research, clinical trials, or drug information.
                </p>
              </div>
            )}

            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onCitationClick={setSelectedCitation}
              />
            ))}

            {agents.length > 0 && <AgentStatus agents={agents} />}
          </div>
        </ScrollArea>

        {/* Input */}
        <div className="border-t border-border p-4">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="flex gap-2">
              <Input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about medical research..."
                disabled={isLoading}
                className="flex-1"
              />
              <Button type="submit" disabled={isLoading || !input.trim()}>
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>

      {/* Citations sidebar */}
      {citations.length > 0 && (
        <div className="w-80 border-l border-border p-4 overflow-y-auto">
          <h3 className="text-lg font-semibold mb-4">Citations ({citations.length})</h3>
          <div className="space-y-3">
            {citations.map((citation, index) => (
              <CitationCard
                key={citation.citation_id}
                citation={citation}
                index={index + 1}
                expanded={selectedCitation === citation.citation_id}
                onToggle={() =>
                  setSelectedCitation(
                    selectedCitation === citation.citation_id ? null : citation.citation_id
                  )
                }
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

