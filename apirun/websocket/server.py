"""WebSocket Server for Real-time Push.

This module implements the WebSocket server for real-time test execution updates.
Following Google Python Style Guide.
"""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime
import json
import logging

import websockets
from websockets.server import WebSocketServerProtocol

from apirun.websocket.events import EventType, WebSocketEvent

logger = logging.getLogger(__name__)


class WebSocketServer:
    """WebSocket server for real-time test execution updates.

    This server:
    - Manages WebSocket client connections
    - Broadcasts events to all connected clients
    - Handles client connection/disconnection
    - Supports event filtering by type

    Attributes:
        host: Server host address
        port: Server port
        clients: Set of connected client connections
        server: WebSocket server instance
        event_callback: Optional callback for incoming client messages
    """

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 8765,
        event_callback: Callable[[dict], Awaitable[None]] | None = None,
    ):
        """Initialize WebSocket server.

        Args:
            host: Server host address
            port: Server port
            event_callback: Optional async callback for client messages
        """
        self.host = host
        self.port = port
        self.clients: set[WebSocketServerProtocol] = set()
        self.server: websockets.server.serve | None = None
        self.event_callback = event_callback
        self._running = False

    async def start(self):
        """Start the WebSocket server.

        This method starts the server in the background.
        """
        if self._running:
            logger.warning('WebSocket server is already running')
            return

        self.server = await websockets.serve(
            self._handle_client, self.host, self.port, ping_interval=20, ping_timeout=20
        )
        self._running = True
        logger.info(f'WebSocket server started at ws://{self.host}:{self.port}')

    async def stop(self):
        """Stop the WebSocket server.

        This method closes all client connections and stops the server.
        """
        if not self._running:
            return

        # Close all client connections
        for client in self.clients.copy():
            await client.close()

        self.clients.clear()

        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None

        self._running = False
        logger.info('WebSocket server stopped')

    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle a client connection.

        Args:
            websocket: WebSocket client connection
            path: WebSocket URL path
        """
        client_id = f'{websocket.remote_address[0]}:{websocket.remote_address[1]}'
        logger.info(f'Client connected: {client_id}')

        # Register client
        self.clients.add(websocket)

        try:
            # Send welcome message
            welcome_event = WebSocketEvent(
                type=EventType.LOG,
                data={
                    'level': 'info',
                    'message': f'Connected to Sisyphus WebSocket server at {datetime.now().isoformat()}',
                },
            )
            await self._send_to_client(websocket, welcome_event)

            # Listen for client messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.debug(f'Received message from {client_id}: {data}')

                    # Call event callback if provided
                    if self.event_callback:
                        await self.event_callback(data)

                except json.JSONDecodeError as e:
                    logger.error(f'Invalid JSON from {client_id}: {e}')
                except Exception as e:
                    logger.error(f'Error handling message from {client_id}: {e}')

        except websockets.exceptions.ConnectionClosed:
            logger.info(f'Client disconnected: {client_id}')
        except Exception as e:
            logger.error(f'Error handling client {client_id}: {e}')
        finally:
            # Unregister client
            self.clients.discard(websocket)
            logger.info(f'Client removed: {client_id}')

    async def broadcast(self, event: WebSocketEvent):
        """Broadcast an event to all connected clients.

        Args:
            event: Event to broadcast
        """
        if not self.clients:
            return

        message = json.dumps(event.to_dict())

        # Create a list of coroutines for all clients
        tasks = [self._send_to_client(client, event) for client in self.clients.copy()]

        # Execute all sends concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_to_client(
        self, client: WebSocketServerProtocol, event: WebSocketEvent
    ):
        """Send an event to a specific client.

        Args:
            client: WebSocket client connection
            event: Event to send
        """
        try:
            message = json.dumps(event.to_dict())
            await client.send(message)
        except (websockets.exceptions.ConnectionClosed, Exception) as e:
            logger.debug(f'Failed to send to client: {e}')
            self.clients.discard(client)

    def get_client_count(self) -> int:
        """Get the number of connected clients.

        Returns:
            Number of connected clients
        """
        return len(self.clients)

    @property
    def is_running(self) -> bool:
        """Check if the server is running.

        Returns:
            True if server is running, False otherwise
        """
        return self._running

    async def run_forever(self):
        """Run the server until interrupted.

        This is a convenience method that keeps the server running.
        """
        if not self._running:
            await self.start()

        try:
            # Keep the server running
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info('Server run cancelled')
        finally:
            await self.stop()
