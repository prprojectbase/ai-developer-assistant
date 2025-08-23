import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

from ..config.settings import get_settings
from ..modules.file_operations import FileOperations
from ..modules.terminal_operations import TerminalOperations
from ..modules.task_manager import TaskManager
from ..modules.playwright_integration import PlaywrightIntegration
from ..agents.communication_agent import CommunicationAgent


@dataclass
class AgentMessage:
    """Message structure for agent communication"""
    sender: str
    recipient: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: Optional[str] = None


class AIDeveloperAssistant:
    """Main AI Developer Assistant orchestrator"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = self._setup_logging()
        
        # Initialize modules
        self.file_ops = FileOperations()
        self.terminal_ops = TerminalOperations()
        self.task_manager = TaskManager(max_concurrent_tasks=self.settings.max_concurrent_tasks)
        self.playwright = PlaywrightIntegration()
        
        # Initialize communication agent
        self.communication_agent = CommunicationAgent()
        
        # Agent registry
        self.agents: Dict[str, Any] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        
        # Running state
        self.is_running = False
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.settings.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.settings.log_file),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    async def initialize(self) -> None:
        """Initialize the assistant and all modules"""
        self.logger.info("Initializing AI Developer Assistant...")
        
        # Create workspace directory if it doesn't exist
        import os
        os.makedirs(self.settings.workspace_dir, exist_ok=True)
        
        # Initialize modules
        await self.file_ops.initialize()
        await self.terminal_ops.initialize()
        await self.task_manager.initialize()
        await self.playwright.initialize()
        
        # Initialize communication agent
        await self.communication_agent.initialize()
        
        # Register self as an agent
        self.agents["main"] = self
        
        self.logger.info("AI Developer Assistant initialized successfully")
    
    async def start(self) -> None:
        """Start the assistant"""
        if self.is_running:
            self.logger.warning("Assistant is already running")
            return
            
        self.logger.info("Starting AI Developer Assistant...")
        self.is_running = True
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._process_messages()),
            asyncio.create_task(self._monitor_tasks()),
            asyncio.create_task(self._handle_agent_communication())
        ]
        
        self.logger.info("AI Developer Assistant started successfully")
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            self.logger.info("Shutting down assistant...")
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the assistant"""
        self.logger.info("Stopping AI Developer Assistant...")
        self.is_running = False
        
        # Stop all modules
        await self.file_ops.stop()
        await self.terminal_ops.stop()
        await self.task_manager.stop()
        await self.playwright.stop()
        await self.communication_agent.stop()
        
        self.logger.info("AI Developer Assistant stopped")
    
    async def _process_messages(self) -> None:
        """Process messages from the queue"""
        while self.is_running:
            try:
                message = await asyncio.wait_for(
                    self.message_queue.get(), 
                    timeout=1.0
                )
                await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
    
    async def _handle_message(self, message: AgentMessage) -> None:
        """Handle incoming messages"""
        self.logger.info(f"Received message from {message.sender}: {message.message_type}")
        
        try:
            if message.message_type == "file_operation":
                result = await self.file_ops.execute_operation(message.content)
                await self._send_response(message, result)
            
            elif message.message_type == "terminal_command":
                result = await self.terminal_ops.execute_command(message.content)
                await self._send_response(message, result)
            
            elif message.message_type == "task_create":
                result = await self.task_manager.create_task(message.content)
                await self._send_response(message, result)
            
            elif message.message_type == "playwright_action":
                result = await self.playwright.execute_action(message.content)
                await self._send_response(message, result)
            
            else:
                self.logger.warning(f"Unknown message type: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            await self._send_response(message, {"error": str(e)})
    
    async def _send_response(self, original_message: AgentMessage, response: Dict[str, Any]) -> None:
        """Send response back to message sender"""
        response_message = AgentMessage(
            sender="main",
            recipient=original_message.sender,
            message_type="response",
            content=response,
            message_id=f"resp_{original_message.message_id}"
        )
        
        await self.communication_agent.send_message(response_message)
    
    async def _monitor_tasks(self) -> None:
        """Monitor task execution"""
        while self.is_running:
            try:
                task_status = await self.task_manager.get_task_status()
                if task_status:
                    self.logger.debug(f"Task status: {task_status}")
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"Error monitoring tasks: {e}")
    
    async def _handle_agent_communication(self) -> None:
        """Handle multi-agent communication"""
        while self.is_running:
            try:
                messages = await self.communication_agent.receive_messages()
                for message in messages:
                    await self.message_queue.put(message)
            except Exception as e:
                self.logger.error(f"Error in agent communication: {e}")
                await asyncio.sleep(1)
    
    async def register_agent(self, agent_id: str, agent: Any) -> None:
        """Register a new agent"""
        self.agents[agent_id] = agent
        self.logger.info(f"Registered agent: {agent_id}")
    
    async def send_message_to_agent(self, agent_id: str, message: AgentMessage) -> None:
        """Send message to a specific agent"""
        if agent_id in self.agents:
            await self.agents[agent_id].handle_message(message)
        else:
            self.logger.warning(f"Agent not found: {agent_id}")
    
    async def broadcast_message(self, message: AgentMessage) -> None:
        """Broadcast message to all agents"""
        for agent_id, agent in self.agents.items():
            if agent_id != message.sender:
                await agent.handle_message(message)