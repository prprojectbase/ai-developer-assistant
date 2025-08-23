"""
Message types for agent communication
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class AgentMessage:
    """Message structure for agent communication"""
    sender: str
    receiver: str
    message_type: str
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None