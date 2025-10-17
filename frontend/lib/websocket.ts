/**
 * WebSocket client for real-time search updates
 */

// Use relative WebSocket URL in production (works through nginx proxy)
// Use localhost in development
const getWsBaseUrl = () => {
  if (typeof window === 'undefined') return 'ws://localhost:8000';

  if (window.location.hostname === 'localhost') {
    return process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
  }

  // Production: use same host with wss protocol
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}`;
};

const WS_BASE_URL = getWsBaseUrl();

export type MessageType =
  | '*'
  | 'agent_start'
  | 'agent_progress'
  | 'agent_complete'
  | 'search_result'
  | 'citation_found'
  | 'search_progress'
  | 'search_complete'
  | 'search_error'
  | 'error';

export interface WebSocketMessage {
  type: string; // backend may send additional types
  payload?: unknown; // backend sends 'payload'
  data?: unknown;    // legacy shape
  timestamp?: string;
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


// Utility types and helpers to avoid `any`
type UnknownObject = Record<string, unknown>;

function extractPayload(msg: WebSocketMessage): unknown {
  return typeof msg.payload !== 'undefined' ? msg.payload : msg.data;
}

function getSearchIdFromPayload(payload: unknown): string | undefined {
  if (payload && typeof payload === 'object' && 'search_id' in payload) {
    const sid = (payload as UnknownObject).search_id;
    return typeof sid === 'string' ? sid : undefined;
  }
  return undefined;
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
    try {
      // Filter by search_id if present to avoid cross-talk across searches
      const payload = extractPayload(message);
      const targetSearchId = getSearchIdFromPayload(payload);
      if (targetSearchId && targetSearchId !== this.searchId) {
        console.debug('Ignoring WS message for different search_id', { targetSearchId, current: this.searchId, type: message.type });
        return;
      }

      const handlers = this.handlers.get(message.type as MessageType);
      if (handlers) {
        handlers.forEach(handler => handler(message));
      }

      // Also call handlers registered for all message types
      const allHandlers = this.handlers.get('*');
      if (allHandlers) {
        allHandlers.forEach(handler => handler(message));
      }
    } catch (err) {
      console.error('Failed to handle WS message', { err });
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

