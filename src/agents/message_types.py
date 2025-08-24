"""
Message types for agent communication
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List


@dataclass
class AgentMessage:
    """Message structure for agent communication"""
    sender: str
    recipient: str
    message_type: str
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProjectPhaseMessage:
    """Message for project phase transitions"""
    phase: str
    previous_phase: Optional[str] = None
    guidance: Optional[Dict[str, Any]] = None
    success_criteria: Optional[List[str]] = None
    key_activities: Optional[List[str]] = None


@dataclass
class ImplementationStatusMessage:
    """Message for implementation status updates"""
    progress: float
    status: str
    active_tasks: int
    completed_tasks: int
    challenges: List[str] = None
    artifacts: List[str] = None


@dataclass
class TaskAssignmentMessage:
    """Message for task assignments"""
    task_id: str
    task_name: str
    task_type: str
    priority: str
    description: str
    dependencies: List[str] = None
    estimated_duration: str = "1 hour"
    metadata: Dict[str, Any] = None


@dataclass
class GuidanceRequestMessage:
    """Message for requesting guidance"""
    request_type: str
    context: Dict[str, Any]
    urgency: str = "normal"
    details: Dict[str, Any] = None


@dataclass
class ImplementationResultMessage:
    """Message for implementation results"""
    task_id: str
    success: bool
    result: Any
    execution_time: float
    error_message: Optional[str] = None
    artifacts: List[str] = None


@dataclass
class ConversationMessage:
    """Message for AI agent conversations"""
    conversation_id: str
    message: str
    context: Dict[str, Any]
    response_expected: bool = True
    timestamp: datetime = field(default_factory=datetime.now)