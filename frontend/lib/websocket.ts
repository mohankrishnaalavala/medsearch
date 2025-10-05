/**
 * WebSocket client for real-time search updates
 */

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export type MessageType = 
  | 'agent_start'
  | 'agent_progress'
  | 'agent_complete'
  | 'search_result'
  | 'citation_found'
  | 'error';

export interface WebSocketMessage {
  type: MessageType;
  data: any;
  timestamp: string;
}

export interface AgentStartMessage {
  agent_name: string;
  task: string;
}

export interface AgentProgressMessage {
  agent_name: string;
  progress: number;
  message: string;
}

export interface AgentCompleteMessage {
  agent_name: string;
  result: string;
  execution_time: number;
}

export interface SearchResultMessage {
  search_id: string;
  final_response: string;
  confidence_score: number;
  execution_time: number;
}

export interface CitationFoundMessage {
  citation_id: string;
  source_type: string;
  title: string;
  snippet: string;
  relevance_score: number;
}

export interface ErrorMessage {
  error: string;
  details?: string;
}

export type MessageHandler = (message: WebSocketMessage) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private searchId: string;
  private handlers: Map<MessageType, MessageHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private shouldReconnect = true;

  constructor(searchId: string) {
    this.searchId = searchId;
  }

  /**
   * Connect to WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const url = `${WS_BASE_URL}/ws/${this.searchId}`;
        console.debug('Connecting to WebSocket:', url);
        
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          console.debug('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            console.debug('WebSocket message received:', message);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.debug('WebSocket closed');
          this.handleReconnect();
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    this.shouldReconnect = false; // Prevent reconnection
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Register a message handler
   */
  on(type: MessageType, handler: MessageHandler): void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, []);
    }
    this.handlers.get(type)!.push(handler);
  }

  /**
   * Unregister a message handler
   */
  off(type: MessageType, handler: MessageHandler): void {
    const handlers = this.handlers.get(type);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Handle incoming message
   */
  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.handlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => handler(message));
    }

    // Also call handlers registered for all message types
    const allHandlers = this.handlers.get('*' as MessageType);
    if (allHandlers) {
      allHandlers.forEach(handler => handler(message));
    }
  }

  /**
   * Handle reconnection
   */
  private handleReconnect(): void {
    if (!this.shouldReconnect) {
      console.debug('Reconnection disabled, not reconnecting');
      return;
    }

    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

      console.debug(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

      setTimeout(() => {
        this.connect().catch(error => {
          console.error('Reconnection failed:', error);
        });
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

/**
 * Create a WebSocket client for a search
 */
export function createWebSocketClient(searchId: string): WebSocketClient {
  return new WebSocketClient(searchId);
}

