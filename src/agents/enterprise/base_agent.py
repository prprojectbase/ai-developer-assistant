"""
Base Agent Class for Enterprise AI Agent System

This module provides the foundation for all enterprise AI agents,
including common functionality, communication protocols,
and hierarchy management.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
import uuid
from enum import Enum

from ..config.settings import get_settings
from ..agents.communication_agent import CommunicationAgent
from ..agents.message_types import AgentMessage
from ..utils.performance_monitor import PerformanceMonitor
from ..utils.cache import get_cache_instance
from ..utils.security import get_security_manager


class AgentStatus(Enum):
    """Agent status enumeration"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    STOPPED = "stopped"


class AuthorityLevel(Enum):
    """Authority level enumeration"""
    SUPPORT = 1      # Level 1: Support engineers and specialists
    SPECIALIST = 2   # Level 2: Senior specialists
    OPERATIONAL = 3  # Level 3: Team leads
    TACTICAL = 4     # Level 4: Managers
    STRATEGIC = 5    # Level 5: Directors
    EXECUTIVE = 6    # Level 6: CTO, COO, CIO
    SUPREME = 7      # Level 7: CEO


@dataclass
class AgentCapabilities:
    """Agent capabilities definition"""
    strategic_planning: bool = False
    resource_allocation: bool = False
    team_management: bool = False
    technical_implementation: bool = False
    quality_assurance: bool = False
    security_management: bool = False
    operations_management: bool = False
    integration_management: bool = False
    monitoring: bool = False
    recovery: bool = False
    innovation: bool = False
    communication: bool = False
    decision_making: bool = False
    crisis_management: bool = False


@dataclass
class AgentResources:
    """Agent resources allocation"""
    cpu_allocation: float = 0.0
    memory_allocation: float = 0.0
    storage_allocation: float = 0.0
    network_bandwidth: float = 0.0
    ai_model_tokens: int = 0
    concurrent_tasks: int = 1
    priority_level: int = 1


@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_response_time: float = 0.0
    resource_utilization: float = 0.0
    quality_score: float = 0.0
    security_score: float = 0.0
    innovation_score: float = 0.0
    collaboration_score: float = 0.0
    last_activity: datetime = field(default_factory=datetime.now)
    uptime_percentage: float = 0.0


class EnterpriseBaseAgent(ABC):
    """
    Base class for all enterprise AI agents
    
    This class provides common functionality for all agents in the
    enterprise hierarchy, including communication, resource management,
    performance monitoring, and hierarchy integration.
    """
    
    def __init__(self, 
                 agent_id: str,
                 agent_name: str,
                 authority_level: AuthorityLevel,
                 capabilities: AgentCapabilities,
                 resources: AgentResources,
                 supervisor_id: Optional[str] = None,
                 subordinate_ids: Optional[List[str]] = None):
        """
        Initialize the enterprise agent
        
        Args:
            agent_id: Unique identifier for the agent
            agent_name: Human-readable name for the agent
            authority_level: Authority level in the hierarchy
            capabilities: Agent capabilities
            resources: Allocated resources
            supervisor_id: ID of supervisor agent
            subordinate_ids: IDs of subordinate agents
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.authority_level = authority_level
        self.capabilities = capabilities
        self.resources = resources
        self.supervisor_id = supervisor_id
        self.subordinate_ids = subordinate_ids or []
        
        # System components
        self.settings = get_settings()
        self.logger = self._setup_logging()
        self.communication_agent = CommunicationAgent()
        self.performance_monitor = PerformanceMonitor()
        self.cache = get_cache_instance()
        self.security_manager = get_security_manager()
        
        # Agent state
        self.status = AgentStatus.INITIALIZING
        self.metrics = AgentMetrics()
        self.message_queue = asyncio.Queue()
        self.task_queue = asyncio.Queue()
        self.active_tasks = {}
        self.context = {}
        
        # Communication
        self.message_handlers = {}
        self.event_handlers = {}
        
        # Performance tracking
        self.start_time = datetime.now()
        self.last_activity = datetime.now()
        
        # Security
        self.session_token = None
        self.permissions = set()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(f"EnterpriseAgent.{self.agent_id}")
        logger.setLevel(getattr(logging, self.settings.log_level))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    async def initialize(self) -> None:
        """Initialize the agent and all its components"""
        self.logger.info(f"Initializing {self.agent_name} ({self.agent_id})")
        
        try:
            # Initialize communication
            await self.communication_agent.initialize()
            
            # Initialize performance monitoring
            await self.performance_monitor.initialize()
            
            # Initialize security
            await self._initialize_security()
            
            # Register message handlers
            self._register_message_handlers()
            
            # Register event handlers
            self._register_event_handlers()
            
            # Set up performance monitoring
            self._setup_performance_monitoring()
            
            # Initialize context
            await self._initialize_context()
            
            # Update status
            self.status = AgentStatus.ACTIVE
            self.logger.info(f"{self.agent_name} initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.agent_name}: {e}")
            self.status = AgentStatus.ERROR
            raise
    
    async def _initialize_security(self) -> None:
        """Initialize security components"""
        try:
            # Generate session token
            self.session_token = str(uuid.uuid4())
            
            # Set up permissions based on authority level
            self.permissions = self._get_permissions_for_level()
            
            # Register with security manager
            await self.security_manager.register_agent(
                self.agent_id, 
                self.authority_level.value,
                self.permissions
            )
            
            self.logger.info(f"Security initialized for {self.agent_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize security: {e}")
            raise
    
    def _get_permissions_for_level(self) -> set:
        """Get permissions based on authority level"""
        permissions = set()
        
        # Base permissions for all agents
        permissions.update([
            'basic_communication',
            'task_execution',
            'status_reporting',
            'context_access'
        ])
        
        # Level-specific permissions
        if self.authority_level.value >= AuthorityLevel.SPECIALIST.value:
            permissions.update([
                'advanced_communication',
                'resource_request',
                'task_delegation'
            ])
        
        if self.authority_level.value >= AuthorityLevel.OPERATIONAL.value:
            permissions.update([
                'team_management',
                'resource_allocation',
                'quality_control'
            ])
        
        if self.authority_level.value >= AuthorityLevel.TACTICAL.value:
            permissions.update([
                'strategic_planning',
                'cross_functional_communication',
                'performance_monitoring'
            ])
        
        if self.authority_level.value >= AuthorityLevel.STRATEGIC.value:
            permissions.update([
                'resource_control',
                'policy_creation',
                'system_oversight'
            ])
        
        if self.authority_level.value >= AuthorityLevel.EXECUTIVE.value:
            permissions.update([
                'executive_decision',
                'crisis_management',
                'system_control'
            ])
        
        if self.authority_level.value >= AuthorityLevel.SUPREME.value:
            permissions.update([
                'ultimate_authority',
                'system_override',
                'resource_reallocation'
            ])
        
        return permissions
    
    def _register_message_handlers(self) -> None:
        """Register default message handlers"""
        self.message_handlers.update({
            'task_assignment': self._handle_task_assignment,
            'status_request': self._handle_status_request,
            'resource_request': self._handle_resource_request,
            'context_update': self._handle_context_update,
            'performance_query': self._handle_performance_query,
            'emergency_alert': self._handle_emergency_alert,
            'hierarchy_update': self._handle_hierarchy_update
        })
    
    def _register_event_handlers(self) -> None:
        """Register default event handlers"""
        self.event_handlers.update({
            'agent_status_change': self._handle_agent_status_change,
            'resource_allocation_change': self._handle_resource_change,
            'system_alert': self._handle_system_alert,
            'performance_threshold': self._handle_performance_threshold
        })
    
    def _setup_performance_monitoring(self) -> None:
        """Setup performance monitoring for the agent"""
        try:
            # Register agent with performance monitor
            self.performance_monitor.register_agent(
                self.agent_id,
                self.agent_name,
                self.authority_level.value
            )
            
            # Set up metrics collection
            self.performance_monitor.register_metrics_collector(
                self.agent_id,
                self._collect_performance_metrics
            )
            
            self.logger.info(f"Performance monitoring setup for {self.agent_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup performance monitoring: {e}")
    
    async def _initialize_context(self) -> None:
        """Initialize agent context"""
        try:
            # Load context from cache if available
            cached_context = await self.cache.get(f"agent_context_{self.agent_id}")
            if cached_context:
                self.context = json.loads(cached_context)
            else:
                # Initialize default context
                self.context = {
                    'agent_id': self.agent_id,
                    'agent_name': self.agent_name,
                    'authority_level': self.authority_level.value,
                    'capabilities': {
                        k: v for k, v in self.capabilities.__dict__.items()
                    },
                    'resources': {
                        k: v for k, v in self.resources.__dict__.items()
                    },
                    'hierarchy': {
                        'supervisor': self.supervisor_id,
                        'subordinates': self.subordinate_ids
                    },
                    'initialization_time': datetime.now().isoformat()
                }
                
                # Cache initial context
                await self.cache.set(
                    f"agent_context_{self.agent_id}",
                    json.dumps(self.context),
                    ttl=3600  # 1 hour TTL
                )
            
            self.logger.info(f"Context initialized for {self.agent_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize context: {e}")
            raise
    
    async def start(self) -> None:
        """Start the agent's main operation loop"""
        if self.status != AgentStatus.ACTIVE:
            raise RuntimeError(f"Agent {self.agent_name} is not active")
        
        self.logger.info(f"Starting {self.agent_name}")
        
        # Start background tasks
        self.background_tasks = [
            asyncio.create_task(self._process_messages()),
            asyncio.create_task(self._process_tasks()),
            asyncio.create_task(self._monitor_performance()),
            asyncio.create_task(self._monitor_context()),
            asyncio.create_task(self._handle_communication())
        ]
        
        self.logger.info(f"{self.agent_name} started successfully")
    
    async def stop(self) -> None:
        """Stop the agent's operation"""
        self.logger.info(f"Stopping {self.agent_name}")
        
        # Cancel background tasks
        for task in getattr(self, 'background_tasks', []):
            task.cancel()
        
        # Wait for tasks to complete
        if hasattr(self, 'background_tasks'):
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Update status
        self.status = AgentStatus.STOPPED
        
        # Save final context
        await self._save_context()
        
        # Cleanup
        await self.communication_agent.stop()
        await self.performance_monitor.stop_monitoring()
        
        self.logger.info(f"{self.agent_name} stopped successfully")
    
    async def _process_messages(self) -> None:
        """Process incoming messages"""
        while self.status in [AgentStatus.ACTIVE, AgentStatus.BUSY]:
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
    
    async def _process_tasks(self) -> None:
        """Process queued tasks"""
        while self.status in [AgentStatus.ACTIVE, AgentStatus.BUSY]:
            try:
                task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                await self._execute_task(task)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing task: {e}")
    
    async def _monitor_performance(self) -> None:
        """Monitor agent performance"""
        while self.status in [AgentStatus.ACTIVE, AgentStatus.BUSY]:
            try:
                # Collect performance metrics
                metrics = await self._collect_performance_metrics()
                
                # Update agent metrics
                self._update_metrics(metrics)
                
                # Check performance thresholds
                await self._check_performance_thresholds(metrics)
                
                # Sleep for monitoring interval
                await asyncio.sleep(30)  # 30 second interval
                
            except Exception as e:
                self.logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_context(self) -> None:
        """Monitor agent context health"""
        while self.status in [AgentStatus.ACTIVE, AgentStatus.BUSY]:
            try:
                # Validate context integrity
                await self._validate_context()
                
                # Update context if needed
                await self._update_context()
                
                # Save context periodically
                await self._save_context()
                
                # Sleep for context monitoring interval
                await asyncio.sleep(60)  # 1 minute interval
                
            except Exception as e:
                self.logger.error(f"Error in context monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _handle_communication(self) -> None:
        """Handle communication with other agents"""
        while self.status in [AgentStatus.ACTIVE, AgentStatus.BUSY]:
            try:
                # Receive messages from communication agent
                messages = await self.communication_agent.receive_messages()
                
                for message in messages:
                    await self.message_queue.put(message)
                
                # Sleep for communication interval
                await asyncio.sleep(0.1)  # 100ms interval
                
            except Exception as e:
                self.logger.error(f"Error in communication handling: {e}")
                await asyncio.sleep(1)
    
    async def _handle_message(self, message: AgentMessage) -> None:
        """Handle incoming message"""
        try:
            # Validate message
            if not await self._validate_message(message):
                self.logger.warning(f"Invalid message received: {message.message_id}")
                return
            
            # Update activity
            self.last_activity = datetime.now()
            
            # Route to appropriate handler
            handler = self.message_handlers.get(message.message_type)
            if handler:
                await handler(message)
            else:
                await self._handle_unknown_message(message)
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    async def _validate_message(self, message: AgentMessage) -> bool:
        """Validate incoming message"""
        try:
            # Check message structure
            if not all([
                message.message_id,
                message.sender,
                message.recipient,
                message.message_type,
                message.content
            ]):
                return False
            
            # Check security
            if not await self.security_manager.validate_message(message):
                return False
            
            # Check permissions
            if not await self._check_message_permissions(message):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating message: {e}")
            return False
    
    async def _check_message_permissions(self, message: AgentMessage) -> bool:
        """Check if agent has permissions to handle message"""
        # Basic permission check based on message type
        message_permissions = {
            'task_assignment': 'task_execution',
            'status_request': 'basic_communication',
            'resource_request': 'resource_request',
            'context_update': 'context_access',
            'performance_query': 'performance_monitoring',
            'emergency_alert': 'basic_communication',
            'hierarchy_update': 'basic_communication'
        }
        
        required_permission = message_permissions.get(message.message_type)
        if required_permission and required_permission not in self.permissions:
            self.logger.warning(f"Permission denied for message type: {message.message_type}")
            return False
        
        return True
    
    async def _handle_unknown_message(self, message: AgentMessage) -> None:
        """Handle unknown message types"""
        self.logger.warning(f"Unknown message type: {message.message_type}")
        
        # Send response indicating unknown message type
        response = AgentMessage(
            sender=self.agent_id,
            recipient=message.sender,
            message_type="error",
            content={
                "error": "Unknown message type",
                "message_type": message.message_type,
                "message_id": message.message_id
            },
            message_id=f"error_{message.message_id}"
        )
        
        await self.communication_agent.send_message(response)
    
    async def _handle_task_assignment(self, message: AgentMessage) -> None:
        """Handle task assignment"""
        try:
            task_data = message.content
            task_id = task_data.get('task_id', str(uuid.uuid4()))
            
            # Create task
            task = {
                'task_id': task_id,
                'task_type': task_data.get('task_type'),
                'priority': task_data.get('priority', 1),
                'deadline': task_data.get('deadline'),
                'requirements': task_data.get('requirements', {}),
                'assigned_by': message.sender,
                'assigned_at': datetime.now().isoformat()
            }
            
            # Add to task queue
            await self.task_queue.put(task)
            
            # Send acknowledgment
            response = AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type="task_acknowledgment",
                content={
                    "task_id": task_id,
                    "status": "queued",
                    "agent": self.agent_id,
                    "timestamp": datetime.now().isoformat()
                },
                message_id=f"ack_{message.message_id}"
            )
            
            await self.communication_agent.send_message(response)
            
        except Exception as e:
            self.logger.error(f"Error handling task assignment: {e}")
    
    async def _handle_status_request(self, message: AgentMessage) -> None:
        """Handle status request"""
        try:
            status_info = {
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "status": self.status.value,
                "authority_level": self.authority_level.value,
                "metrics": self.metrics.__dict__,
                "resources": self.resources.__dict__,
                "active_tasks": len(self.active_tasks),
                "queue_size": self.task_queue.qsize(),
                "last_activity": self.last_activity.isoformat()
            }
            
            response = AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type="status_response",
                content=status_info,
                message_id=f"status_{message.message_id}"
            )
            
            await self.communication_agent.send_message(response)
            
        except Exception as e:
            self.logger.error(f"Error handling status request: {e}")
    
    async def _handle_resource_request(self, message: AgentMessage) -> None:
        """Handle resource request"""
        try:
            # Check if agent has resource allocation permission
            if 'resource_allocation' not in self.permissions:
                response = AgentMessage(
                    sender=self.agent_id,
                    recipient=message.sender,
                    message_type="resource_denied",
                    content={
                        "reason": "Insufficient permissions",
                        "request_id": message.content.get('request_id')
                    },
                    message_id=f"deny_{message.message_id}"
                )
                await self.communication_agent.send_message(response)
                return
            
            # Process resource request
            request_data = message.content
            requested_resources = request_data.get('resources', {})
            
            # Forward to supervisor if needed
            if self.supervisor_id and self.authority_level.value < AuthorityLevel.EXECUTIVE.value:
                await self._forward_to_supervisor(message)
            else:
                # Handle resource allocation
                await self._handle_resource_allocation(request_data, message.sender)
                
        except Exception as e:
            self.logger.error(f"Error handling resource request: {e}")
    
    async def _handle_context_update(self, message: AgentMessage) -> None:
        """Handle context update"""
        try:
            context_update = message.content
            
            # Update agent context
            self.context.update(context_update)
            
            # Save updated context
            await self._save_context()
            
            # Send acknowledgment
            response = AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type="context_update_ack",
                content={
                    "status": "updated",
                    "timestamp": datetime.now().isoformat()
                },
                message_id=f"context_{message.message_id}"
            )
            
            await self.communication_agent.send_message(response)
            
        except Exception as e:
            self.logger.error(f"Error handling context update: {e}")
    
    async def _handle_performance_query(self, message: AgentMessage) -> None:
        """Handle performance query"""
        try:
            performance_data = await self._collect_performance_metrics()
            
            response = AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type="performance_response",
                content=performance_data,
                message_id=f"perf_{message.message_id}"
            )
            
            await self.communication_agent.send_message(response)
            
        except Exception as e:
            self.logger.error(f"Error handling performance query: {e}")
    
    async def _handle_emergency_alert(self, message: AgentMessage) -> None:
        """Handle emergency alert"""
        try:
            alert_data = message.content
            alert_level = alert_data.get('level', 'medium')
            
            self.logger.warning(f"Emergency alert received: {alert_level}")
            
            # Handle based on alert level and agent authority
            if alert_level == 'critical' and self.authority_level.value >= AuthorityLevel.EXECUTIVE.value:
                await self._handle_critical_alert(alert_data)
            else:
                # Forward to supervisor
                if self.supervisor_id:
                    await self._forward_to_supervisor(message)
                
        except Exception as e:
            self.logger.error(f"Error handling emergency alert: {e}")
    
    async def _handle_hierarchy_update(self, message: AgentMessage) -> None:
        """Handle hierarchy update"""
        try:
            update_data = message.content
            
            # Update hierarchy information
            if 'supervisor_id' in update_data:
                self.supervisor_id = update_data['supervisor_id']
            
            if 'subordinate_ids' in update_data:
                self.subordinate_ids = update_data['subordinate_ids']
            
            # Update context
            self.context['hierarchy'] = {
                'supervisor': self.supervisor_id,
                'subordinates': self.subordinate_ids
            }
            
            # Save context
            await self._save_context()
            
            # Send acknowledgment
            response = AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type="hierarchy_update_ack",
                content={
                    "status": "updated",
                    "timestamp": datetime.now().isoformat()
                },
                message_id=f"hierarchy_{message.message_id}"
            )
            
            await self.communication_agent.send_message(response)
            
        except Exception as e:
            self.logger.error(f"Error handling hierarchy update: {e}")
    
    async def _execute_task(self, task: Dict[str, Any]) -> None:
        """Execute a task"""
        try:
            task_id = task['task_id']
            task_type = task['task_type']
            
            # Update status
            self.status = AgentStatus.BUSY
            
            # Track task
            self.active_tasks[task_id] = {
                'task': task,
                'start_time': datetime.now(),
                'status': 'executing'
            }
            
            # Execute task based on type
            result = await self._execute_task_by_type(task)
            
            # Update task status
            self.active_tasks[task_id]['status'] = 'completed'
            self.active_tasks[task_id]['result'] = result
            self.active_tasks[task_id]['end_time'] = datetime.now()
            
            # Update metrics
            self.metrics.tasks_completed += 1
            
            # Send completion notification
            await self._send_task_completion_notification(task_id, result)
            
            # Remove from active tasks
            del self.active_tasks[task_id]
            
            # Update status
            self.status = AgentStatus.ACTIVE
            
        except Exception as e:
            self.logger.error(f"Error executing task {task_id}: {e}")
            
            # Update task status
            if task_id in self.active_tasks:
                self.active_tasks[task_id]['status'] = 'failed'
                self.active_tasks[task_id]['error'] = str(e)
                self.active_tasks[task_id]['end_time'] = datetime.now()
            
            # Update metrics
            self.metrics.tasks_failed += 1
            
            # Send failure notification
            await self._send_task_failure_notification(task_id, str(e))
            
            # Update status
            self.status = AgentStatus.ACTIVE
    
    @abstractmethod
    async def _execute_task_by_type(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task based on type - to be implemented by subclasses"""
        pass
    
    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics"""
        try:
            # Calculate uptime
            uptime = datetime.now() - self.start_time
            uptime_hours = uptime.total_seconds() / 3600
            
            # Calculate resource utilization
            resource_utilization = (
                self.resources.cpu_allocation +
                self.resources.memory_allocation +
                self.resources.storage_allocation
            ) / 3
            
            return {
                'agent_id': self.agent_id,
                'agent_name': self.agent_name,
                'status': self.status.value,
                'uptime_hours': uptime_hours,
                'tasks_completed': self.metrics.tasks_completed,
                'tasks_failed': self.metrics.tasks_failed,
                'active_tasks': len(self.active_tasks),
                'queue_size': self.task_queue.qsize(),
                'resource_utilization': resource_utilization,
                'last_activity': self.last_activity.isoformat(),
                'authority_level': self.authority_level.value,
                'capabilities': {
                    k: v for k, v in self.capabilities.__dict__.items()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting performance metrics: {e}")
            return {}
    
    def _update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update agent metrics"""
        try:
            # Update basic metrics
            self.metrics.average_response_time = metrics.get('average_response_time', 0.0)
            self.metrics.resource_utilization = metrics.get('resource_utilization', 0.0)
            self.metrics.quality_score = metrics.get('quality_score', 0.0)
            self.metrics.security_score = metrics.get('security_score', 0.0)
            self.metrics.innovation_score = metrics.get('innovation_score', 0.0)
            self.metrics.collaboration_score = metrics.get('collaboration_score', 0.0)
            
            # Calculate uptime percentage
            uptime = datetime.now() - self.start_time
            total_uptime = uptime.total_seconds()
            if total_uptime > 0:
                self.metrics.uptime_percentage = (total_uptime / total_uptime) * 100
            
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")
    
    async def _check_performance_thresholds(self, metrics: Dict[str, Any]) -> None:
        """Check performance thresholds and generate alerts"""
        try:
            # Define thresholds
            thresholds = {
                'resource_utilization': 90.0,
                'queue_size': 10,
                'active_tasks': 5,
                'error_rate': 0.1
            }
            
            alerts = []
            
            # Check resource utilization
            if metrics.get('resource_utilization', 0) > thresholds['resource_utilization']:
                alerts.append({
                    'type': 'resource_utilization_high',
                    'value': metrics['resource_utilization'],
                    'threshold': thresholds['resource_utilization']
                })
            
            # Check queue size
            if metrics.get('queue_size', 0) > thresholds['queue_size']:
                alerts.append({
                    'type': 'queue_size_high',
                    'value': metrics['queue_size'],
                    'threshold': thresholds['queue_size']
                })
            
            # Check active tasks
            if metrics.get('active_tasks', 0) > thresholds['active_tasks']:
                alerts.append({
                    'type': 'active_tasks_high',
                    'value': metrics['active_tasks'],
                    'threshold': thresholds['active_tasks']
                })
            
            # Check error rate
            total_tasks = self.metrics.tasks_completed + self.metrics.tasks_failed
            if total_tasks > 0:
                error_rate = self.metrics.tasks_failed / total_tasks
                if error_rate > thresholds['error_rate']:
                    alerts.append({
                        'type': 'error_rate_high',
                        'value': error_rate,
                        'threshold': thresholds['error_rate']
                    })
            
            # Send alerts if any
            for alert in alerts:
                await self._send_performance_alert(alert)
                
        except Exception as e:
            self.logger.error(f"Error checking performance thresholds: {e}")
    
    async def _send_performance_alert(self, alert: Dict[str, Any]) -> None:
        """Send performance alert"""
        try:
            alert_message = AgentMessage(
                sender=self.agent_id,
                recipient=self.supervisor_id or 'system',
                message_type="performance_alert",
                content={
                    'agent_id': self.agent_id,
                    'alert': alert,
                    'timestamp': datetime.now().isoformat()
                },
                message_id=f"alert_{uuid.uuid4()}"
            )
            
            await self.communication_agent.send_message(alert_message)
            
        except Exception as e:
            self.logger.error(f"Error sending performance alert: {e}")
    
    async def _validate_context(self) -> None:
        """Validate context integrity"""
        try:
            # Check required fields
            required_fields = ['agent_id', 'agent_name', 'authority_level']
            for field in required_fields:
                if field not in self.context:
                    raise ValueError(f"Missing required context field: {field}")
            
            # Check data types
            if not isinstance(self.context['authority_level'], int):
                raise ValueError("Authority level must be an integer")
            
            # Validate hierarchy information
            if 'hierarchy' in self.context:
                hierarchy = self.context['hierarchy']
                if not isinstance(hierarchy, dict):
                    raise ValueError("Hierarchy must be a dictionary")
            
        except Exception as e:
            self.logger.error(f"Context validation failed: {e}")
            raise
    
    async def _update_context(self) -> None:
        """Update context with current information"""
        try:
            # Update performance metrics
            self.context['performance'] = await self._collect_performance_metrics()
            
            # Update status
            self.context['status'] = self.status.value
            
            # Update last activity
            self.context['last_activity'] = self.last_activity.isoformat()
            
        except Exception as e:
            self.logger.error(f"Error updating context: {e}")
    
    async def _save_context(self) -> None:
        """Save context to cache"""
        try:
            await self.cache.set(
                f"agent_context_{self.agent_id}",
                json.dumps(self.context),
                ttl=3600  # 1 hour TTL
            )
        except Exception as e:
            self.logger.error(f"Error saving context: {e}")
    
    async def _forward_to_supervisor(self, message: AgentMessage) -> None:
        """Forward message to supervisor"""
        try:
            if self.supervisor_id:
                forwarded_message = AgentMessage(
                    sender=self.agent_id,
                    recipient=self.supervisor_id,
                    message_type=message.message_type,
                    content=message.content,
                    message_id=f"forward_{message.message_id}"
                )
                
                await self.communication_agent.send_message(forwarded_message)
            else:
                self.logger.warning("No supervisor to forward message to")
                
        except Exception as e:
            self.logger.error(f"Error forwarding to supervisor: {e}")
    
    async def _handle_resource_allocation(self, request_data: Dict[str, Any], requester_id: str) -> None:
        """Handle resource allocation"""
        try:
            # Process resource allocation logic
            # This is a placeholder - subclasses should implement specific logic
            
            response = AgentMessage(
                sender=self.agent_id,
                recipient=requester_id,
                message_type="resource_allocation_response",
                content={
                    "status": "processed",
                    "request_id": request_data.get('request_id'),
                    "allocated_resources": {},
                    "timestamp": datetime.now().isoformat()
                },
                message_id=f"resource_{uuid.uuid4()}"
            )
            
            await self.communication_agent.send_message(response)
            
        except Exception as e:
            self.logger.error(f"Error handling resource allocation: {e}")
    
    async def _handle_critical_alert(self, alert_data: Dict[str, Any]) -> None:
        """Handle critical alert"""
        try:
            self.logger.critical(f"Critical alert: {alert_data}")
            
            # Implement critical alert handling logic
            # This is a placeholder - subclasses should implement specific logic
            
        except Exception as e:
            self.logger.error(f"Error handling critical alert: {e}")
    
    async def _send_task_completion_notification(self, task_id: str, result: Dict[str, Any]) -> None:
        """Send task completion notification"""
        try:
            notification = AgentMessage(
                sender=self.agent_id,
                recipient=self.supervisor_id or 'system',
                message_type="task_completed",
                content={
                    "task_id": task_id,
                    "result": result,
                    "agent": self.agent_id,
                    "timestamp": datetime.now().isoformat()
                },
                message_id=f"complete_{task_id}"
            )
            
            await self.communication_agent.send_message(notification)
            
        except Exception as e:
            self.logger.error(f"Error sending task completion notification: {e}")
    
    async def _send_task_failure_notification(self, task_id: str, error: str) -> None:
        """Send task failure notification"""
        try:
            notification = AgentMessage(
                sender=self.agent_id,
                recipient=self.supervisor_id or 'system',
                message_type="task_failed",
                content={
                    "task_id": task_id,
                    "error": error,
                    "agent": self.agent_id,
                    "timestamp": datetime.now().isoformat()
                },
                message_id=f"failed_{task_id}"
            )
            
            await self.communication_agent.send_message(notification)
            
        except Exception as e:
            self.logger.error(f"Error sending task failure notification: {e}")
    
    async def _handle_agent_status_change(self, event_data: Dict[str, Any]) -> None:
        """Handle agent status change event"""
        try:
            agent_id = event_data.get('agent_id')
            new_status = event_data.get('status')
            
            self.logger.info(f"Agent {agent_id} status changed to {new_status}")
            
            # Update context if needed
            if agent_id in self.subordinate_ids:
                # Update subordinate status in context
                if 'subordinate_status' not in self.context:
                    self.context['subordinate_status'] = {}
                
                self.context['subordinate_status'][agent_id] = new_status
                await self._save_context()
                
        except Exception as e:
            self.logger.error(f"Error handling agent status change: {e}")
    
    async def _handle_resource_change(self, event_data: Dict[str, Any]) -> None:
        """Handle resource allocation change event"""
        try:
            agent_id = event_data.get('agent_id')
            new_resources = event_data.get('resources')
            
            self.logger.info(f"Resources changed for agent {agent_id}")
            
            # Update own resources if applicable
            if agent_id == self.agent_id:
                for key, value in new_resources.items():
                    if hasattr(self.resources, key):
                        setattr(self.resources, key, value)
                
                # Update context
                self.context['resources'] = {
                    k: v for k, v in self.resources.__dict__.items()
                }
                await self._save_context()
                
        except Exception as e:
            self.logger.error(f"Error handling resource change: {e}")
    
    async def _handle_system_alert(self, event_data: Dict[str, Any]) -> None:
        """Handle system alert event"""
        try:
            alert_type = event_data.get('type')
            alert_message = event_data.get('message')
            
            self.logger.warning(f"System alert: {alert_type} - {alert_message}")
            
            # Handle based on alert type and agent authority
            if alert_type == 'system_critical' and self.authority_level.value >= AuthorityLevel.EXECUTIVE.value:
                await self._handle_critical_alert(event_data)
                
        except Exception as e:
            self.logger.error(f"Error handling system alert: {e}")
    
    async def _handle_performance_threshold(self, event_data: Dict[str, Any]) -> None:
        """Handle performance threshold event"""
        try:
            threshold_type = event_data.get('type')
            threshold_value = event_data.get('value')
            threshold_limit = event_data.get('limit')
            
            self.logger.warning(f"Performance threshold exceeded: {threshold_type} = {threshold_value} > {threshold_limit}")
            
            # Take appropriate action based on threshold type
            if threshold_type == 'resource_utilization_high':
                # Request additional resources
                await self._request_additional_resources()
            elif threshold_type == 'queue_size_high':
                # Request task redistribution
                await self._request_task_redistribution()
                
        except Exception as e:
            self.logger.error(f"Error handling performance threshold: {e}")
    
    async def _request_additional_resources(self) -> None:
        """Request additional resources"""
        try:
            if self.supervisor_id:
                request = AgentMessage(
                    sender=self.agent_id,
                    recipient=self.supervisor_id,
                    message_type="resource_request",
                    content={
                        "request_id": str(uuid.uuid4()),
                        "reason": "High resource utilization",
                        "requested_resources": {
                            "cpu_allocation": self.resources.cpu_allocation + 0.1,
                            "memory_allocation": self.resources.memory_allocation + 0.1,
                            "concurrent_tasks": self.resources.concurrent_tasks + 1
                        }
                    },
                    message_id=f"resource_request_{uuid.uuid4()}"
                )
                
                await self.communication_agent.send_message(request)
                
        except Exception as e:
            self.logger.error(f"Error requesting additional resources: {e}")
    
    async def _request_task_redistribution(self) -> None:
        """Request task redistribution"""
        try:
            if self.subordinate_ids:
                # Redistribute tasks to subordinates
                redistribution_request = AgentMessage(
                    sender=self.agent_id,
                    recipient="system",
                    message_type="task_redistribution_request",
                    content={
                        "agent_id": self.agent_id,
                        "queue_size": self.task_queue.qsize(),
                        "available_subordinates": self.subordinate_ids
                    },
                    message_id=f"redistribute_{uuid.uuid4()}"
                )
                
                await self.communication_agent.send_message(redistribution_request)
                
        except Exception as e:
            self.logger.error(f"Error requesting task redistribution: {e}")
    
    async def send_message_to_agent(self, recipient_id: str, message_type: str, content: Dict[str, Any]) -> str:
        """Send message to another agent"""
        try:
            message = AgentMessage(
                sender=self.agent_id,
                recipient=recipient_id,
                message_type=message_type,
                content=content,
                message_id=f"msg_{uuid.uuid4()}"
            )
            
            await self.communication_agent.send_message(message)
            return message.message_id
            
        except Exception as e:
            self.logger.error(f"Error sending message to {recipient_id}: {e}")
            raise
    
    async def send_message_to_subordinates(self, message_type: str, content: Dict[str, Any]) -> List[str]:
        """Send message to all subordinate agents"""
        message_ids = []
        
        for subordinate_id in self.subordinate_ids:
            try:
                message_id = await self.send_message_to_agent(subordinate_id, message_type, content)
                message_ids.append(message_id)
            except Exception as e:
                self.logger.error(f"Error sending message to subordinate {subordinate_id}: {e}")
        
        return message_ids
    
    async def send_message_to_supervisor(self, message_type: str, content: Dict[str, Any]) -> str:
        """Send message to supervisor agent"""
        if not self.supervisor_id:
            raise ValueError("No supervisor assigned")
        
        return await self.send_message_to_agent(self.supervisor_id, message_type, content)
    
    async def broadcast_message(self, message_type: str, content: Dict[str, Any]) -> List[str]:
        """Broadcast message to all agents"""
        try:
            broadcast_message = AgentMessage(
                sender=self.agent_id,
                recipient="broadcast",
                message_type=message_type,
                content=content,
                message_id=f"broadcast_{uuid.uuid4()}"
            )
            
            await self.communication_agent.send_message(broadcast_message)
            return [broadcast_message.message_id]
            
        except Exception as e:
            self.logger.error(f"Error broadcasting message: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "authority_level": self.authority_level.value,
            "supervisor_id": self.supervisor_id,
            "subordinate_ids": self.subordinate_ids,
            "metrics": self.metrics.__dict__,
            "resources": self.resources.__dict__,
            "active_tasks": len(self.active_tasks),
            "queue_size": self.task_queue.qsize(),
            "last_activity": self.last_activity.isoformat(),
            "uptime": str(datetime.now() - self.start_time)
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "authority_level": self.authority_level.value,
            "capabilities": {
                k: v for k, v in self.capabilities.__dict__.items()
            }
        }
    
    def get_context(self) -> Dict[str, Any]:
        """Get agent context"""
        return self.context.copy()
    
    async def update_context(self, context_update: Dict[str, Any]) -> None:
        """Update agent context"""
        try:
            self.context.update(context_update)
            await self._save_context()
        except Exception as e:
            self.logger.error(f"Error updating context: {e}")
            raise