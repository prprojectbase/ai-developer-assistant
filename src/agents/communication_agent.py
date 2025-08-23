import asyncio
import json
import logging
import uuid
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol
import aiofiles
import os

from ..config.settings import get_settings
from ..agents.main_agent import AgentMessage
from ..utils.auth import auth_manager, WebSocketAuthMiddleware


class CommunicationAgent:
    """Multi-agent communication system for the AI Developer Assistant"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Communication channels
        self.websocket_server = None
        self.connected_clients: Dict[str, WebSocketServerProtocol] = {}
        self.authenticated_clients: Dict[str, Any] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.message_history: List[AgentMessage] = []
        
        # Agent registry
        self.registered_agents: Dict[str, Any] = {}
        
        # Authentication
        self.auth_middleware = WebSocketAuthMiddleware(auth_manager)
        
        # Event loop for async operations
        self.event_loop = None
        
    async def initialize(self) -> None:
        """Initialize the communication agent"""
        self.logger.info("Initializing Communication Agent...")
        
        # Get the current event loop
        self.event_loop = asyncio.get_event_loop()
        
        # Create authentication tokens for registered agents
        for agent_id in self.registered_agents:
            auth_manager.create_token(agent_id)
        
        # Start WebSocket server
        self.websocket_server = await websockets.serve(
            self._handle_websocket_connection,
            self.settings.agent_host,
            self.settings.agent_port
        )
        
        self.logger.info(f"Communication Agent started on ws://{self.settings.agent_host}:{self.settings.agent_port}")
    
    async def stop(self) -> None:
        """Stop the communication agent"""
        self.logger.info("Stopping Communication Agent...")
        
        # Close all client connections
        for client_id, client in self.connected_clients.items():
            try:
                await client.close()
            except Exception as e:
                self.logger.error(f"Error closing client {client_id}: {e}")
        
        self.connected_clients.clear()
        self.authenticated_clients.clear()
        
        # Clean up expired tokens
        auth_manager.cleanup_expired_tokens()
        
        # Stop WebSocket server
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
        
        self.logger.info("Communication Agent stopped")
    
    async def register_agent(self, agent_id: str, agent: Any) -> None:
        """Register an agent for communication"""
        self.registered_agents[agent_id] = agent
        
        # Create authentication token for the agent
        auth_manager.create_token(agent_id)
        
        self.logger.info(f"Registered agent: {agent_id}")
    
    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent"""
        if agent_id in self.registered_agents:
            del self.registered_agents[agent_id]
            
            # Revoke all tokens for this agent
            auth_manager.revoke_agent_tokens(agent_id)
            
            self.logger.info(f"Unregistered agent: {agent_id}")
    
    async def get_agent_token(self, agent_id: str) -> Optional[str]:
        """Get authentication token for an agent"""
        tokens = auth_manager.list_agent_tokens(agent_id)
        if tokens:
            # Return the most recent token
            return tokens[-1]["token_id"]
        return None
    
    async def send_message(self, message: AgentMessage) -> str:
        """Send a message to another agent"""
        if not message.message_id:
            message.message_id = str(uuid.uuid4())
        
        # Add to message history
        self.message_history.append(message)
        
        # Log the message
        self.logger.info(f"Sending message from {message.sender} to {message.recipient}")
        
        # Send to WebSocket clients
        await self._broadcast_to_clients(message)
        
        # Send to registered agent if exists
        if message.recipient in self.registered_agents:
            try:
                await self.registered_agents[message.recipient].handle_message(message)
            except Exception as e:
                self.logger.error(f"Error sending message to agent {message.recipient}: {e}")
        
        return message.message_id
    
    async def receive_messages(self) -> List[AgentMessage]:
        """Receive messages from other agents"""
        # This method would typically be called by agents to get their messages
        # For now, we'll return an empty list as messages are handled via callbacks
        return []
    
    async def broadcast_message(self, message: AgentMessage, exclude_sender: bool = True) -> None:
        """Broadcast a message to all agents"""
        if not message.message_id:
            message.message_id = str(uuid.uuid4())
        
        # Add to message history
        self.message_history.append(message)
        
        # Broadcast to all registered agents
        for agent_id, agent in self.registered_agents.items():
            if exclude_sender and agent_id == message.sender:
                continue
            
            try:
                await agent.handle_message(message)
            except Exception as e:
                self.logger.error(f"Error broadcasting message to agent {agent_id}: {e}")
        
        # Broadcast to WebSocket clients
        await self._broadcast_to_clients(message)
    
    async def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """Register a message handler for a specific message type"""
        self.message_handlers[message_type] = handler
        self.logger.info(f"Registered message handler for type: {message_type}")
    
    async def unregister_message_handler(self, message_type: str) -> None:
        """Unregister a message handler"""
        if message_type in self.message_handlers:
            del self.message_handlers[message_type]
            self.logger.info(f"Unregistered message handler for type: {message_type}")
    
    async def get_message_history(self, limit: Optional[int] = None) -> List[AgentMessage]:
        """Get message history"""
        if limit:
            return self.message_history[-limit:]
        return self.message_history.copy()
    
    async def get_connected_agents(self) -> List[str]:
        """Get list of connected agents"""
        return list(self.registered_agents.keys())
    
    async def _handle_websocket_connection(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle incoming WebSocket connections"""
        client_id = f"client_{len(self.connected_clients)}_{id(websocket)}"
        self.connected_clients[client_id] = websocket
        
        self.logger.info(f"Client connected: {client_id}")
        
        try:
            # Authenticate the connection
            is_authenticated, auth_token = await self.auth_middleware.authenticate_connection(websocket, path)
            
            if not is_authenticated:
                await self.auth_middleware.send_auth_response(websocket, False)
                await websocket.close()
                return
            
            # Send successful authentication response
            await self.auth_middleware.send_auth_response(websocket, True, auth_token)
            
            # Store authenticated client
            self.authenticated_clients[client_id] = {
                "websocket": websocket,
                "token": auth_token,
                "agent_id": auth_token.agent_id
            }
            
            self.logger.info(f"Client authenticated: {client_id} (Agent: {auth_token.agent_id})")
            
            # Send welcome message
            welcome_message = AgentMessage(
                sender="system",
                recipient=client_id,
                message_type="welcome",
                content={
                    "message": "Connected to AI Developer Assistant",
                    "client_id": client_id,
                    "agent_id": auth_token.agent_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            await self._send_to_client(websocket, welcome_message)
            
            # Handle incoming messages
            async for message in websocket:
                try:
                    await self._handle_client_message(client_id, message)
                except Exception as e:
                    self.logger.error(f"Error handling message from client {client_id}: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            self.logger.error(f"Error with client {client_id}: {e}")
        finally:
            # Clean up client connection
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
            if client_id in self.authenticated_clients:
                del self.authenticated_clients[client_id]
            self.logger.info(f"Client connection cleaned up: {client_id}")
    
    async def _handle_client_message(self, client_id: str, message: str) -> None:
        """Handle message from WebSocket client"""
        try:
            # Check if client is authenticated
            if client_id not in self.authenticated_clients:
                self.logger.warning(f"Unauthenticated client {client_id} attempted to send message")
                return
            
            # Parse and verify signed message
            message_data = json.loads(message)
            is_valid, auth_token, verified_data = self.auth_middleware.unwrap_message(message_data)
            
            if not is_valid:
                self.logger.warning(f"Invalid signature from client {client_id}")
                error_response = AgentMessage(
                    sender="system",
                    recipient=client_id,
                    message_type="error",
                    content={"error": "Invalid message signature"}
                )
                await self._send_to_client(self.connected_clients[client_id], error_response)
                return
            
            # Create AgentMessage from verified data
            agent_message = AgentMessage(
                sender=verified_data.get("sender", client_id),
                recipient=verified_data.get("recipient", "system"),
                message_type=verified_data.get("message_type", "unknown"),
                content=verified_data.get("content", {}),
                timestamp=datetime.fromisoformat(verified_data.get("timestamp", datetime.now().isoformat())),
                message_id=verified_data.get("message_id")
            )
            
            self.logger.info(f"Received message from client {client_id}: {agent_message.message_type}")
            
            # Add to message history
            self.message_history.append(agent_message)
            
            # Handle message based on type
            if agent_message.message_type in self.message_handlers:
                await self.message_handlers[agent_message.message_type](agent_message)
            else:
                # Forward to registered agent
                if agent_message.recipient in self.registered_agents:
                    await self.registered_agents[agent_message.recipient].handle_message(agent_message)
                else:
                    # Send error response
                    error_response = AgentMessage(
                        sender="system",
                        recipient=client_id,
                        message_type="error",
                        content={
                            "error": f"No handler for message type: {agent_message.message_type}",
                            "original_message_id": agent_message.message_id
                        }
                    )
                    await self._send_to_client(self.connected_clients[client_id], error_response)
                    
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON message from client {client_id}")
            error_response = AgentMessage(
                sender="system",
                recipient=client_id,
                message_type="error",
                content={"error": "Invalid JSON message"}
            )
            await self._send_to_client(self.connected_clients[client_id], error_response)
        except Exception as e:
            self.logger.error(f"Error handling client message: {e}")
            error_response = AgentMessage(
                sender="system",
                recipient=client_id,
                message_type="error",
                content={"error": f"Error processing message: {str(e)}"}
            )
            await self._send_to_client(self.connected_clients[client_id], error_response)
    
    async def _send_to_client(self, websocket: WebSocketServerProtocol, message: AgentMessage) -> None:
        """Send a message to a specific WebSocket client"""
        try:
            message_dict = {
                "sender": message.sender,
                "recipient": message.recipient,
                "message_type": message.message_type,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "message_id": message.message_id
            }
            
            await websocket.send(json.dumps(message_dict))
            
        except Exception as e:
            self.logger.error(f"Error sending message to client: {e}")
    
    async def _broadcast_to_clients(self, message: AgentMessage) -> None:
        """Broadcast a message to all connected WebSocket clients"""
        if not self.connected_clients:
            return
        
        message_dict = {
            "sender": message.sender,
            "recipient": message.recipient,
            "message_type": message.message_type,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "message_id": message.message_id
        }
        
        # Send to all connected clients
        disconnected_clients = []
        for client_id, websocket in self.connected_clients.items():
            try:
                await websocket.send(json.dumps(message_dict))
            except Exception as e:
                self.logger.error(f"Error broadcasting to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
    
    async def save_message_history(self, filename: str) -> None:
        """Save message history to a file"""
        try:
            history_data = []
            for message in self.message_history:
                history_data.append({
                    "sender": message.sender,
                    "recipient": message.recipient,
                    "message_type": message.message_type,
                    "content": message.content,
                    "timestamp": message.timestamp.isoformat(),
                    "message_id": message.message_id
                })
            
            async with aiofiles.open(filename, 'w') as f:
                await f.write(json.dumps(history_data, indent=2))
            
            self.logger.info(f"Message history saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving message history: {e}")
    
    async def load_message_history(self, filename: str) -> None:
        """Load message history from a file"""
        try:
            if not os.path.exists(filename):
                self.logger.warning(f"Message history file not found: {filename}")
                return
            
            async with aiofiles.open(filename, 'r') as f:
                content = await f.read()
            
            history_data = json.loads(content)
            
            self.message_history.clear()
            for msg_data in history_data:
                message = AgentMessage(
                    sender=msg_data["sender"],
                    recipient=msg_data["recipient"],
                    message_type=msg_data["message_type"],
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                    message_id=msg_data["message_id"]
                )
                self.message_history.append(message)
            
            self.logger.info(f"Message history loaded from {filename}")
            
        except Exception as e:
            self.logger.error(f"Error loading message history: {e}")


class AgentClient:
    """Client for connecting to the communication system"""
    
    def __init__(self, agent_id: str, host: str = "localhost", port: int = 8081):
        self.agent_id = agent_id
        self.host = host
        self.port = port
        self.websocket = None
        self.auth_token = None
        self.message_handlers: Dict[str, Callable] = {}
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> None:
        """Connect to the communication server"""
        uri = f"ws://{self.host}:{self.port}"
        self.websocket = await websockets.connect(uri)
        self.logger.info(f"Connected to communication server: {uri}")
        
        # Authenticate with the server
        await self._authenticate()
        
        # Start listening for messages
        asyncio.create_task(self._listen_for_messages())
    
    async def _authenticate(self) -> None:
        """Authenticate with the communication server"""
        if not self.auth_token:
            # Generate a new token (in a real scenario, this would be provided by the server)
            from ..utils.auth import auth_manager
            token = auth_manager.create_token(self.agent_id)
            self.auth_token = token.token_id
        
        # Send authentication message
        auth_message = {
            "type": "auth",
            "token_id": self.auth_token,
            "timestamp": int(time.time())
        }
        
        # Sign the authentication message
        from ..utils.auth import auth_manager
        signed_auth = auth_manager.create_signed_message(self.auth_token, auth_message)
        
        await self.websocket.send(json.dumps(signed_auth))
        
        # Wait for authentication response
        response = await self.websocket.recv()
        response_data = json.loads(response)
        
        if response_data.get("type") == "auth_response" and response_data.get("success"):
            self.logger.info("Authentication successful")
        else:
            raise RuntimeError("Authentication failed")
    
    async def disconnect(self) -> None:
        """Disconnect from the communication server"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.logger.info("Disconnected from communication server")
    
    async def send_message(self, message: AgentMessage) -> None:
        """Send a message to the communication server"""
        if not self.websocket:
            raise RuntimeError("Not connected to communication server")
        
        if not self.auth_token:
            raise RuntimeError("Not authenticated")
        
        # Create message data
        message_data = {
            "sender": message.sender or self.agent_id,
            "recipient": message.recipient,
            "message_type": message.message_type,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "message_id": message.message_id
        }
        
        # Sign the message
        from ..utils.auth import auth_manager
        signed_message = auth_manager.create_signed_message(self.auth_token, message_data)
        
        await self.websocket.send(json.dumps(signed_message))
    
    async def _listen_for_messages(self) -> None:
        """Listen for incoming messages"""
        try:
            async for message in self.websocket:
                try:
                    message_data = json.loads(message)
                    
                    agent_message = AgentMessage(
                        sender=message_data["sender"],
                        recipient=message_data["recipient"],
                        message_type=message_data["message_type"],
                        content=message_data["content"],
                        timestamp=datetime.fromisoformat(message_data["timestamp"]),
                        message_id=message_data["message_id"]
                    )
                    
                    # Handle message
                    if agent_message.message_type in self.message_handlers:
                        await self.message_handlers[agent_message.message_type](agent_message)
                    else:
                        self.logger.warning(f"No handler for message type: {agent_message.message_type}")
                        
                except Exception as e:
                    self.logger.error(f"Error handling incoming message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.info("Connection to communication server closed")
        except Exception as e:
            self.logger.error(f"Error listening for messages: {e}")
    
    def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """Register a message handler"""
        self.message_handlers[message_type] = handler
        self.logger.info(f"Registered message handler for type: {message_type}")
    
    def unregister_message_handler(self, message_type: str) -> None:
        """Unregister a message handler"""
        if message_type in self.message_handlers:
            del self.message_handlers[message_type]
            self.logger.info(f"Unregistered message handler for type: {message_type}")