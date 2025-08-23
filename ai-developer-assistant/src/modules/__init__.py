"""Core modules for AI Developer Assistant"""

from .file_operations import FileOperations
from .terminal_operations import TerminalOperations
from .task_manager import TaskManager, Task, TaskStatus, TaskPriority
from .playwright_integration import PlaywrightIntegration
from .openrouter_integration import OpenRouterAPI, OpenRouterAgent, ChatMessage, ChatCompletionRequest, ChatCompletionResponse
from .vscode_integration import VSCodeIntegration

__all__ = [
    "FileOperations",
    "TerminalOperations", 
    "TaskManager",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "PlaywrightIntegration",
    "OpenRouterAPI",
    "OpenRouterAgent",
    "ChatMessage",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "VSCodeIntegration"
]