'use client';

import { useState, useRef, useEffect } from 'react';
import { Message, Citation, AgentStatus as AgentStatusType } from '@/lib/types';
import { MessageBubble } from './message-bubble';
import { AgentStatus } from './agent-status';
import { CitationCard } from './citation-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Loader2 } from 'lucide-react';
import { createSearch } from '@/lib/api';
import { createWebSocketClient, WebSocketClient } from '@/lib/websocket';

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
      // Create search request
      const response = await createSearch({
        query: userMessage.content,
        max_results: 10,
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
        const data = message.data;
        setAgents((prev) => [
          ...prev,
          {
            name: data.agent_name,
            status: 'running',
            progress: 0,
            message: data.task,
          },
        ]);
      });

      // Handle agent progress
      client.on('agent_progress', (message) => {
        const data = message.data;
        setAgents((prev) =>
          prev.map((agent) =>
            agent.name === data.agent_name
              ? { ...agent, progress: data.progress, message: data.message }
              : agent
          )
        );
      });

      // Handle agent complete
      client.on('agent_complete', (message) => {
        const data = message.data;
        setAgents((prev) =>
          prev.map((agent) =>
            agent.name === data.agent_name
              ? {
                  ...agent,
                  status: 'complete',
                  progress: 100,
                  execution_time: data.execution_time,
                }
              : agent
          )
        );
      });

      // Handle citation found
      client.on('citation_found', (message) => {
        const citation: Citation = message.data;
        setCitations((prev) => [...prev, citation]);
      });

      // Handle search result
      client.on('search_result', (message) => {
        const data = message.data;
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === response.search_id
              ? {
                  ...msg,
                  content: data.final_response,
                  citations: citations,
                  isStreaming: false,
                }
              : msg
          )
        );
        setIsLoading(false);
        client.disconnect();
      });

      // Handle errors
      client.on('error', (message) => {
        const data = message.data;
        console.error('WebSocket error:', data);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === response.search_id
              ? {
                  ...msg,
                  content: `Error: ${data.error}`,
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

  return (
    <div className="flex h-screen bg-background">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
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

