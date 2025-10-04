"""WebSocket connection manager for real-time updates."""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self) -> None:
        """Initialize connection manager."""
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_sessions: Dict[str, str] = {}  # websocket_id -> user_id

    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """
        Accept WebSocket connection.

        Args:
            websocket: WebSocket connection
            user_id: User identifier

        Returns:
            Connection ID
        """
        await websocket.accept()

        # Generate connection ID
        connection_id = id(websocket)
        websocket_id = str(connection_id)

        # Store connection
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)
        self.user_sessions[websocket_id] = user_id

        logger.info(f"WebSocket connected: user={user_id}, connection={websocket_id}")
        return websocket_id

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Disconnect WebSocket.

        Args:
            websocket: WebSocket connection to disconnect
        """
        websocket_id = str(id(websocket))

        if websocket_id in self.user_sessions:
            user_id = self.user_sessions[websocket_id]

            # Remove from active connections
            if user_id in self.active_connections:
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)

                # Clean up empty user lists
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

            # Remove from user sessions
            del self.user_sessions[websocket_id]

            logger.info(f"WebSocket disconnected: user={user_id}, connection={websocket_id}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        """
        Send message to specific WebSocket.

        Args:
            message: Message to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def send_to_user(self, message: Dict[str, Any], user_id: str) -> None:
        """
        Send message to all connections of a user.

        Args:
            message: Message to send
            user_id: Target user ID
        """
        if user_id in self.active_connections:
            disconnected = []

            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    disconnected.append(connection)

            # Clean up disconnected connections
            for connection in disconnected:
                self.disconnect(connection)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast message to all connections.

        Args:
            message: Message to broadcast
        """
        disconnected = []

        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
                    disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def send_search_progress(
        self,
        user_id: str,
        search_id: str,
        status: str,
        message: str,
        progress: int,
        current_step: Optional[str] = None,
    ) -> None:
        """
        Send search progress update.

        Args:
            user_id: User ID
            search_id: Search session ID
            status: Current status
            message: Progress message
            progress: Progress percentage (0-100)
            current_step: Current step description
        """
        payload = {
            "type": "search_progress",
            "payload": {
                "search_id": search_id,
                "status": status,
                "message": message,
                "progress": progress,
                "current_step": current_step,
            },
        }

        await self.send_to_user(payload, user_id)

    async def send_search_result(
        self,
        user_id: str,
        search_id: str,
        result: Dict[str, Any],
    ) -> None:
        """
        Send search result.

        Args:
            user_id: User ID
            search_id: Search session ID
            result: Search result data
        """
        payload = {
            "type": "search_result",
            "payload": {
                "search_id": search_id,
                "result": result,
            },
        }

        await self.send_to_user(payload, user_id)

    async def send_search_error(
        self,
        user_id: str,
        search_id: str,
        error_code: str,
        error_message: str,
    ) -> None:
        """
        Send search error.

        Args:
            user_id: User ID
            search_id: Search session ID
            error_code: Error code
            error_message: Error message
        """
        payload = {
            "type": "search_error",
            "payload": {
                "search_id": search_id,
                "error": {
                    "code": error_code,
                    "message": error_message,
                },
            },
        }

        await self.send_to_user(payload, user_id)

    async def send_search_complete(
        self,
        user_id: str,
        search_id: str,
        final_response: str,
        citations: List[Dict[str, Any]],
        confidence_score: float,
        execution_time: float,
    ) -> None:
        """
        Send search completion.

        Args:
            user_id: User ID
            search_id: Search session ID
            final_response: Final synthesized response
            citations: List of citations
            confidence_score: Overall confidence score
            execution_time: Total execution time
        """
        payload = {
            "type": "search_complete",
            "payload": {
                "search_id": search_id,
                "final_response": final_response,
                "citations": citations,
                "confidence_score": confidence_score,
                "execution_time": execution_time,
            },
        }

        await self.send_to_user(payload, user_id)

    def get_active_connections_count(self) -> int:
        """Get total number of active connections."""
        return sum(len(connections) for connections in self.active_connections.values())

    def get_active_users_count(self) -> int:
        """Get number of users with active connections."""
        return len(self.active_connections)


# Global connection manager instance
connection_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Get global connection manager instance."""
    return connection_manager

