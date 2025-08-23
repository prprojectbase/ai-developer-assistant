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
from ..modules.openrouter_integration import OpenRouterAPI
from ..agents.communication_agent import CommunicationAgent
from ..utils.performance_monitor import PerformanceMonitor


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
        self.openrouter_api = OpenRouterAPI()
        
        # Initialize communication agent
        self.communication_agent = CommunicationAgent()
        
        # Initialize performance monitor
        self.performance_monitor = PerformanceMonitor()
        
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
        
        # Initialize performance monitor first
        await self.performance_monitor.initialize()
        
        # Initialize modules
        await self.file_ops.initialize()
        await self.terminal_ops.initialize()
        await self.task_manager.initialize()
        await self.playwright.initialize()
        await self.openrouter_api.initialize()
        
        # Initialize communication agent
        await self.communication_agent.initialize()
        
        # Register module statistics collectors with performance monitor
        self._register_performance_collectors()
        
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
        
        # Start performance monitoring
        await self.performance_monitor.start_monitoring()
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._process_messages()),
            asyncio.create_task(self._monitor_tasks()),
            asyncio.create_task(self._handle_agent_communication()),
            asyncio.create_task(self._monitor_performance())
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
        
        # Stop performance monitoring
        await self.performance_monitor.stop_monitoring()
        
        # Stop all modules
        await self.file_ops.stop()
        await self.terminal_ops.stop()
        await self.task_manager.stop()
        await self.playwright.stop()
        await self.openrouter_api.stop()
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
            
            elif message.message_type == "performance_get_summary":
                result = await self._handle_performance_summary()
                await self._send_response(message, result)
            
            elif message.message_type == "performance_get_metrics":
                result = await self._handle_performance_get_metrics(message.content)
                await self._send_response(message, result)
            
            elif message.message_type == "performance_get_alerts":
                result = await self._handle_performance_get_alerts(message.content)
                await self._send_response(message, result)
            
            elif message.message_type == "performance_export_metrics":
                result = await self._handle_performance_export_metrics(message.content)
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
    
    def _register_performance_collectors(self) -> None:
        """Register module statistics collectors with performance monitor"""
        # Register task manager statistics
        self.performance_monitor.register_module_collector(
            "task_manager", 
            self.task_manager.get_statistics
        )
        
        # Register OpenRouter API statistics
        self.performance_monitor.register_module_collector(
            "openrouter_api", 
            self.openrouter_api.get_statistics
        )
        
        # Register cache statistics
        from ..utils.cache import get_cache_instance
        cache = get_cache_instance()
        self.performance_monitor.register_module_collector(
            "cache", 
            cache.get_stats
        )
        
        # Register security statistics
        from ..utils.security import get_security_manager
        security = get_security_manager()
        self.performance_monitor.register_module_collector(
            "security", 
            security.get_command_statistics
        )
        
        self.logger.info("Registered performance collectors for all modules")
    
    async def _monitor_performance(self) -> None:
        """Monitor system performance and handle alerts"""
        while self.is_running:
            try:
                # Get current performance summary
                summary = await self.performance_monitor.get_performance_summary()
                
                # Log performance warnings
                if summary["health_score"] < 80:
                    self.logger.warning(f"System health score low: {summary['health_score']}")
                
                if summary["active_alerts"] > 0:
                    self.logger.warning(f"Active performance alerts: {summary['active_alerts']}")
                
                # Check for critical alerts
                critical_alerts = await self.performance_monitor.get_alerts(resolved=False)
                critical_count = len([a for a in critical_alerts if a["severity"] == "critical"])
                if critical_count > 0:
                    self.logger.error(f"Critical performance alerts detected: {critical_count}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _handle_performance_summary(self) -> Dict[str, Any]:
        """Handle performance summary request"""
        try:
            return await self.performance_monitor.get_performance_summary()
        except Exception as e:
            self.logger.error(f"Error getting performance summary: {e}")
            return {"error": str(e)}
    
    async def _handle_performance_get_metrics(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get performance metrics request"""
        try:
            metric_name = content.get("metric_name")
            limit = content.get("limit", 100)
            return await self.performance_monitor.get_metrics(metric_name, limit)
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}
    
    async def _handle_performance_get_alerts(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get performance alerts request"""
        try:
            resolved = content.get("resolved")
            limit = content.get("limit", 50)
            alerts = await self.performance_monitor.get_alerts(resolved, limit)
            return {"alerts": alerts}
        except Exception as e:
            self.logger.error(f"Error getting performance alerts: {e}")
            return {"error": str(e)}
    
    async def _handle_performance_export_metrics(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle export performance metrics request"""
        try:
            format_type = content.get("format", "json")
            exported_data = await self.performance_monitor.export_metrics(format_type)
            return {
                "format": format_type,
                "data": exported_data,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error exporting performance metrics: {e}")
            return {"error": str(e)}
    
    async def get_system_performance(self) -> Dict[str, Any]:
        """Get comprehensive system performance report"""
        try:
            # Get performance summary
            summary = await self.performance_monitor.get_performance_summary()
            
            # Get current metrics
            current_metrics = await self.performance_monitor.get_current_metrics()
            
            # Get system info
            system_info = await self.performance_monitor.get_system_info()
            
            # Get active alerts
            active_alerts = await self.performance_monitor.get_alerts(resolved=False)
            
            return {
                "summary": summary,
                "current_metrics": current_metrics,
                "system_info": system_info,
                "active_alerts": active_alerts,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting system performance: {e}")
            return {"error": str(e)}
    
    async def resolve_performance_alert(self, alert_id: str) -> Dict[str, Any]:
        """Resolve a performance alert"""
        try:
            success = await self.performance_monitor.resolve_alert(alert_id)
            return {
                "success": success,
                "alert_id": alert_id,
                "message": f"Alert {alert_id} resolved" if success else f"Alert {alert_id} not found"
            }
        except Exception as e:
            self.logger.error(f"Error resolving performance alert: {e}")
            return {"error": str(e)}
    
    async def set_performance_threshold(self, metric_name: str, warning: Optional[float] = None, 
                                     critical: Optional[float] = None) -> Dict[str, Any]:
        """Set performance alert thresholds"""
        try:
            self.performance_monitor.set_threshold(metric_name, warning, critical)
            return {
                "success": True,
                "metric_name": metric_name,
                "warning_threshold": warning,
                "critical_threshold": critical,
                "message": f"Thresholds updated for {metric_name}"
            }
        except Exception as e:
            self.logger.error(f"Error setting performance threshold: {e}")
            return {"error": str(e)}