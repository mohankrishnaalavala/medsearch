'use client';

import { Message } from '@/lib/types';
import { cn } from '@/lib/utils';
import { User, Bot } from 'lucide-react';

interface MessageBubbleProps {
  message: Message;
  onCitationClick?: (citationId: string) => void;
}

export function MessageBubble({ message, onCitationClick }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={cn(
        'flex gap-3 mb-4',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
          <Bot className="w-5 h-5 text-primary-foreground" />
        </div>
      )}

      <div
        className={cn(
          'max-w-[80%] rounded-lg px-4 py-3',
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted text-foreground'
        )}
      >
        <div className="prose prose-sm dark:prose-invert max-w-none">
          {message.isStreaming ? (
            <div className="flex items-center gap-2">
              <span>{message.content}</span>
              <span className="inline-block w-1 h-4 bg-current animate-pulse" />
            </div>
          ) : (
            <p className="whitespace-pre-wrap">{message.content}</p>
          )}
        </div>

        {message.citations && message.citations.length > 0 && (
          <div className="mt-3 pt-3 border-t border-border/50">
            <p className="text-xs font-medium mb-2 opacity-70">Citations:</p>
            <div className="flex flex-wrap gap-2">
              {message.citations.map((citation, index) => (
                <button
                  key={citation.citation_id || `citation-${index}`}
                  onClick={() => onCitationClick?.(citation.citation_id)}
                  className={cn(
                    'inline-flex items-center gap-1 px-2 py-1 rounded text-xs',
                    'bg-background/50 hover:bg-background/80 transition-colors',
                    'border border-border/50'
                  )}
                >
                  <span className="font-mono">[{index + 1}]</span>
                  <span className="truncate max-w-[150px]">
                    {citation.title}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="mt-2 text-xs opacity-50">
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
          <User className="w-5 h-5 text-secondary-foreground" />
        </div>
      )}
    </div>
  );
}

