"""
WebSocket Connection Manager.

This module provides a centralized manager for handling WebSocket connections
across the application. It tracks active connections and provides utilities for
sending messages to individual clients or broadcasting to multiple clients.
"""

from typing import Dict, Set
from fastapi import WebSocket
from app.logging_config import logger


class WebSocketManager:
    """
    Manages WebSocket connections for the AIRA application.

    Provides connection lifecycle management and message routing for WebSocket clients.
    Tracks all active connections and supports both unicast and broadcast messaging.

    Attributes:
        active_connections: Dictionary mapping client IDs to their WebSocket instances
    """

    def __init__(self):
        """Initialize the WebSocket manager with an empty connections dictionary."""
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to accept
            client_id: Unique identifier for the client
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket connected: {client_id}")
        logger.info(f"Total active connections: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        """
        Remove a WebSocket connection.

        Args:
            client_id: Unique identifier for the client to disconnect
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket disconnected: {client_id}")
            logger.info(f"Total active connections: {len(self.active_connections)}")

    async def send_text(self, client_id: str, message: str):
        """
        Send text message to a specific client.

        Args:
            client_id: Unique identifier for the target client
            message: Text message to send
        """
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def send_bytes(self, client_id: str, data: bytes):
        """
        Send binary data to a specific client.

        Args:
            client_id: Unique identifier for the target client
            data: Binary data to send
        """
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_bytes(data)

    async def broadcast_text(self, message: str, exclude: Set[str] = None):
        """
        Broadcast text message to all connected clients.

        Args:
            message: Text message to broadcast
            exclude: Optional set of client IDs to exclude from broadcast
        """
        exclude = exclude or set()
        for client_id, connection in self.active_connections.items():
            if client_id not in exclude:
                await connection.send_text(message)

    async def broadcast_bytes(self, data: bytes, exclude: Set[str] = None):
        """
        Broadcast binary data to all connected clients.

        Args:
            data: Binary data to broadcast
            exclude: Optional set of client IDs to exclude from broadcast
        """
        exclude = exclude or set()
        for client_id, connection in self.active_connections.items():
            if client_id not in exclude:
                await connection.send_bytes(data)

    def get_connection_count(self) -> int:
        """
        Get the number of active connections.

        Returns:
            int: Current number of active WebSocket connections
        """
        return len(self.active_connections)


# Global WebSocket manager instance
ws_manager = WebSocketManager()
