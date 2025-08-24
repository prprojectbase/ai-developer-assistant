"""
Agent Client for WebSocket communication with CommunicationAgent
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import websockets
from websockets.client import WebSocketClientProtocol

from ..config.settings import get_settings
from ..agents.message_types import AgentMessage
from ..utils.auth import auth_manager


class AgentClient:
    """Client for agents to communicate with the CommunicationAgent via WebSocket"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.settings = get_settings()
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # WebSocket connection
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        # Message handling
        self.message_handlers: Dict[str, Callable] = {}
        self.message_queue = asyncio.Queue()
        
        # Authentication
        self.auth_token = None
        
        # Communication state
        self.is_running = False
        
    async def connect(self) -> bool:
        """Connect to the CommunicationAgent WebSocket server"""
        try:
            self.logger.info(f"Connecting to CommunicationAgent as {self.agent_id}...")
            
            # Get authentication token
            self.auth_token = await self._get_auth_token()
            if not self.auth_token:
                self.logger.error("Failed to get authentication token")
                return False
            
            # Connect to WebSocket server
            websocket_url = f"ws://{self.settings.agent_host}:{self.settings.agent_port}"
            self.websocket = await websockets.connect(websocket_url)
            
            # Authenticate the connection
            auth_success = await self._authenticate_connection()
            if not auth_success:
                self.logger.error("Authentication failed")
                await self.websocket.close()
                return False
            
            self.is_connected = True
            self.reconnect_attempts = 0
            self.logger.info(f"Successfully connected to CommunicationAgent as {self.agent_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to CommunicationAgent: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from the CommunicationAgent"""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                self.logger.error(f"Error disconnecting: {e}")
        
        self.is_connected = False
        self.logger.info("Disconnected from CommunicationAgent")
    
    async def _get_auth_token(self) -> Optional[str]:
        """Get authentication token for this agent"""
        try:
            # Check if token already exists
            tokens = auth_manager.list_agent_tokens(self.agent_id)
            if tokens:
                return tokens[-1]["token_id"]
            
            # Create new token
            token = auth_manager.create_token(self.agent_id)
            return token
            
        except Exception as e:
            self.logger.error(f"Failed to get authentication token: {e}")
            return None
    
    async def _authenticate_connection(self) -> bool:
        """Authenticate the WebSocket connection"""
        try:
            # Send authentication message
            auth_message = {
                "type": "auth",
                "agent_id": self.agent_id,
                "token": self.auth_token
            }
            
            await self.websocket.send(json.dumps(auth_message))
            
            # Wait for authentication response
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            response_data = json.loads(response)
            
            if response_data.get("type") == "auth_response" and response_data.get("success"):
                self.logger.info("Authentication successful")
                return True
            else:
                self.logger.error(f"Authentication failed: {response_data.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False
    
    async def send_message(self, message: AgentMessage) -> Optional[str]:
        """Send a message to the CommunicationAgent"""
        if not self.is_connected or not self.websocket:
            self.logger.warning("Not connected to CommunicationAgent")
            return None
        
        try:
            # Ensure message has ID
            if not message.message_id:
                message.message_id = str(uuid.uuid4())
            
            # Create message envelope
            message_envelope = {
                "sender": message.sender,
                "recipient": message.recipient,
                "message_type": message.message_type,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "message_id": message.message_id
            }
            
            # Sign the message
            signed_message = auth_manager.sign_message(message_envelope, self.auth_token)
            
            # Send the message
            await self.websocket.send(json.dumps(signed_message))
            
            self.logger.debug(f"Sent message: {message.message_type} from {message.sender} to {message.recipient}")
            return message.message_id
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return None
    
    async def start_message_listener(self) -> None:
        """Start listening for incoming messages"""
        if not self.is_connected:
            self.logger.warning("Cannot start message listener - not connected")
            return
        
        self.is_running = True
        self.logger.info("Starting message listener...")
        
        try:
            while self.is_running and self.is_connected:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)
                    
                    # Process the message
                    await self._handle_incoming_message(message)
                    
                except asyncio.TimeoutError:
                    # Timeout is normal - just check if we should continue
                    continue
                except websockets.exceptions.ConnectionClosed:
                    self.logger.warning("WebSocket connection closed")
                    break
                except Exception as e:
                    self.logger.error(f"Error receiving message: {e}")
                    break
            
        except Exception as e:
            self.logger.error(f"Error in message listener: {e}")
        
        self.is_running = False
        self.logger.info("Message listener stopped")
    
    async def _handle_incoming_message(self, raw_message: str) -> None:
        """Handle incoming message from CommunicationAgent"""
        try:
            # Parse and verify the message
            message_data = json.loads(raw_message)
            is_valid, auth_token, verified_data = auth_manager.unwrap_message(message_data)
            
            if not is_valid:
                self.logger.warning("Received message with invalid signature")
                return
            
            # Create AgentMessage from verified data
            agent_message = AgentMessage(
                sender=verified_data.get("sender", "unknown"),
                recipient=verified_data.get("recipient", self.agent_id),
                message_type=verified_data.get("message_type", "unknown"),
                content=verified_data.get("content", {}),
                timestamp=datetime.fromisoformat(verified_data.get("timestamp", datetime.now().isoformat())),
                message_id=verified_data.get("message_id")
            )
            
            self.logger.debug(f"Received message: {agent_message.message_type} from {agent_message.sender}")
            
            # Handle the message
            await self._process_message(agent_message)
            
        except json.JSONDecodeError:
            self.logger.error("Received invalid JSON message")
        except Exception as e:
            self.logger.error(f"Error handling incoming message: {e}")
    
    async def _process_message(self, message: AgentMessage) -> None:
        """Process a received message"""
        try:
            # Check if there's a specific handler for this message type
            if message.message_type in self.message_handlers:
                await self.message_handlers[message.message_type](message)
            else:
                # Put message in queue for general processing
                await self.message_queue.put(message)
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    async def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """Register a handler for a specific message type"""
        self.message_handlers[message_type] = handler
        self.logger.info(f"Registered message handler for type: {message_type}")
    
    async def unregister_message_handler(self, message_type: str) -> None:
        """Unregister a message handler"""
        if message_type in self.message_handlers:
            del self.message_handlers[message_type]
            self.logger.info(f"Unregistered message handler for type: {message_type}")
    
    async def get_message(self, timeout: float = 1.0) -> Optional[AgentMessage]:
        """Get a message from the queue"""
        try:
            return await asyncio.wait_for(self.message_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
    
    async def stop(self) -> None:
        """Stop the agent client"""
        self.is_running = False
        await self.disconnect()
        self.logger.info("Agent client stopped")
    
    async def reconnect(self) -> bool:
        """Attempt to reconnect to the CommunicationAgent"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.logger.error("Max reconnection attempts reached")
            return False
        
        self.reconnect_attempts += 1
        self.logger.info(f"Attempting to reconnect (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})...")
        
        # Wait before reconnecting
        await asyncio.sleep(min(2 ** self.reconnect_attempts, 30))  # Exponential backoff
        
        return await self.connect()
    
    async def ensure_connection(self) -> bool:
        """Ensure the client is connected, reconnect if necessary"""
        if not self.is_connected:
            return await self.reconnect()
        return True