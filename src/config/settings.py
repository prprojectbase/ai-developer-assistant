import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings"""
    
    # OpenRouter API Configuration (stored securely via API key manager)
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
    
    # Security Settings
    encryption_key_file: str = Field(default="./logs/encryption.key", env="ENCRYPTION_KEY_FILE")
    api_key_storage_file: str = Field(default="./logs/api_keys.enc", env="API_KEY_STORAGE_FILE")
    max_api_key_age_days: int = Field(default=90, env="MAX_API_KEY_AGE_DAYS")
    auto_rotate_api_keys: bool = Field(default=True, env="AUTO_ROTATE_API_KEYS")
    
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


def get_openrouter_api_key() -> Optional[str]:
    """Get OpenRouter API key from secure storage"""
    try:
        from ..utils.api_key_manager import get_api_key_manager
        key_manager = get_api_key_manager()
        
        # Try to get the key from secure storage
        api_keys = key_manager.list_api_keys("openrouter")
        
        if api_keys:
            # Get the first active key
            for key_id, key_info in api_keys.items():
                if key_info["is_active"] and not key_info["is_expired"]:
                    return key_manager.retrieve_api_key(key_id)
        
        # If no key in secure storage, try environment variable for backward compatibility
        env_key = os.getenv("OPENROUTER_API_KEY")
        if env_key:
            # Store it securely for future use
            key_manager.store_api_key(
                service="openrouter",
                api_key=env_key,
                expires_in_days=settings.max_api_key_age_days,
                metadata={"source": "environment_variable"}
            )
            return env_key
        
        return None
        
    except Exception as e:
        # Log error but don't crash the application
        import logging
        logging.getLogger(__name__).error(f"Error getting OpenRouter API key: {e}")
        return None


def store_openrouter_api_key(api_key: str, password: Optional[str] = None) -> str:
    """Store OpenRouter API key securely"""
    try:
        from ..utils.api_key_manager import get_api_key_manager
        key_manager = get_api_key_manager()
        
        # Validate key format
        if not key_manager.validate_api_key_format(api_key, "openrouter"):
            raise ValueError("Invalid OpenRouter API key format")
        
        # Store the key
        key_id = key_manager.store_api_key(
            service="openrouter",
            api_key=api_key,
            password=password,
            expires_in_days=settings.max_api_key_age_days,
            metadata={"stored_by": "user", "auto_rotate": settings.auto_rotate_api_keys}
        )
        
        return key_id
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error storing OpenRouter API key: {e}")
        raise


def rotate_openrouter_api_key(new_api_key: str, password: Optional[str] = None) -> bool:
    """Rotate OpenRouter API key"""
    try:
        from ..utils.api_key_manager import get_api_key_manager
        key_manager = get_api_key_manager()
        
        # Find existing key
        api_keys = key_manager.list_api_keys("openrouter")
        existing_key_id = None
        
        for key_id, key_info in api_keys.items():
            if key_info["is_active"] and not key_info["is_expired"]:
                existing_key_id = key_id
                break
        
        if existing_key_id:
            # Rotate the key
            result = key_manager.rotate_api_key(existing_key_id, new_api_key, password)
            return result is not None
        else:
            # No existing key, store new one
            store_openrouter_api_key(new_api_key, password)
            return True
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error rotating OpenRouter API key: {e}")
        return False