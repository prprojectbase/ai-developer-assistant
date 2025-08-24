"""
Enterprise AI Agent System

This package contains the enterprise-level AI agent system implementation,
including the base agent class and all specialized enterprise agents.
"""

from .base_agent import (
    EnterpriseBaseAgent,
    AgentStatus,
    AuthorityLevel,
    AgentCapabilities,
    AgentResources
)

from .executive.chief_executive_agent import (
    EnterpriseChiefExecutiveAgent,
    StrategicGoal,
    CrisisPlan
)

__all__ = [
    # Base classes and enums
    'EnterpriseBaseAgent',
    'AgentStatus',
    'AuthorityLevel',
    'AgentCapabilities',
    'AgentResources',
    
    # Executive agents
    'EnterpriseChiefExecutiveAgent',
    'StrategicGoal',
    'CrisisPlan'
]

__version__ = "1.0.0"
__author__ = "Enterprise AI Agent System Team"