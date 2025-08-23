"""
AI Developer Assistant - A comprehensive AI-powered development assistant
"""

__version__ = "1.0.0"
__author__ = "AI Developer Assistant Team"
__email__ = "assistant@ai-developer.local"

from .agents.main_agent import AIDeveloperAssistant
from .config.settings import get_settings

__all__ = ["AIDeveloperAssistant", "get_settings"]