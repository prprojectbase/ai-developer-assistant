import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings"""
    
    # OpenRouter API Configuration
    openrouter_api_key: str = Field(..., env="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL")
    openrouter_model: str = Field(default="anthropic/claude-3-sonnet", env="OPENROUTER_MODEL")
    
    # VS Code Integration
    vscode_port: int = Field(default=8080, env="VSCODE_PORT")
    vscode_host: str = Field(default="localhost", env="VSCODE_HOST")
    
    # Multi-Agent Communication
    agent_port: int = Field(default=8081, env="AGENT_PORT")
    agent_host: str = Field(default="localhost", env="AGENT_HOST")
    
    # Playwright Configuration
    playwright_headless: bool = Field(default=False, env="PLAYWRIGHT_HEADLESS")
    playwright_timeout: int = Field(default=30000, env="PLAYWRIGHT_TIMEOUT")
    
    # File Operations
    workspace_dir: str = Field(default="./workspace", env="WORKSPACE_DIR")
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    
    # Task Manager
    max_concurrent_tasks: int = Field(default=5, env="MAX_CONCURRENT_TASKS")
    task_timeout: int = Field(default=300000, env="TASK_TIMEOUT")  # 5 minutes
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="./logs/assistant.log", env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings


def update_settings(**kwargs) -> None:
    """Update settings dynamically"""
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)