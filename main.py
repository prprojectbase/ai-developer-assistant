#!/usr/bin/env python3
"""
AI Developer Assistant - Main Entry Point

A comprehensive AI-powered development assistant with file operations,
terminal commands, multi-agent communication, task management,
Playwright integration, OpenRouter API, and VS Code integration.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents.main_agent import AIDeveloperAssistant
from src.config.settings import get_settings
from src.modules.openrouter_integration import OpenRouterAPI, OpenRouterAgent
from src.modules.vscode_integration import VSCodeIntegration


class AIDeveloperAssistantCLI:
    """Command-line interface for the AI Developer Assistant"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.assistant: Optional[AIDeveloperAssistant] = None
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        if self.assistant:
            asyncio.create_task(self.assistant.stop())
        sys.exit(0)
    
    async def run(self) -> None:
        """Run the AI Developer Assistant"""
        try:
            print("🤖 AI Developer Assistant Starting...")
            print("=" * 50)
            
            # Initialize and start the assistant
            self.assistant = AIDeveloperAssistant()
            await self.assistant.initialize()
            
            # Set up additional integrations
            await self._setup_integrations()
            
            print("✅ AI Developer Assistant is ready!")
            print(f"📁 Workspace: {self.settings.workspace_dir}")
            print(f"🌐 Agent Communication: ws://{self.settings.agent_host}:{self.settings.agent_port}")
            print(f"💻 VS Code Integration: {'Available' if self.settings.vscode_port else 'Disabled'}")
            print(f"🧠 OpenRouter API: {'Configured' if self.settings.openrouter_api_key else 'Not Configured'}")
            print("=" * 50)
            print("Press Ctrl+C to stop the assistant")
            print()
            
            # Start the assistant
            await self.assistant.start()
            
        except KeyboardInterrupt:
            print("\n👋 Shutting down AI Developer Assistant...")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            print(f"❌ Fatal error: {e}")
        finally:
            if self.assistant:
                await self.assistant.stop()
    
    async def _setup_integrations(self) -> None:
        """Set up additional integrations"""
        try:
            # Initialize OpenRouter API
            if self.settings.openrouter_api_key:
                openrouter_api = OpenRouterAPI()
                await openrouter_api.initialize()
                
                # Create OpenRouter agent
                openrouter_agent = OpenRouterAgent(openrouter_api)
                await self.assistant.register_agent("openrouter", openrouter_agent)
                
                # Register task handlers for AI-powered tasks
                await self.assistant.task_manager.register_task_handler(
                    "generate_code", 
                    openrouter_agent.generate_code
                )
                await self.assistant.task_manager.register_task_handler(
                    "analyze_code", 
                    openrouter_agent.analyze_code
                )
                await self.assistant.task_manager.register_task_handler(
                    "debug_code", 
                    openrouter_agent.debug_code
                )
                await self.assistant.task_manager.register_task_handler(
                    "explain_concept", 
                    openrouter_agent.explain_concept
                )
                
                print("🧠 OpenRouter API integration enabled")
            
            # Initialize VS Code integration
            vscode_integration = VSCodeIntegration()
            await vscode_integration.initialize()
            await self.assistant.register_agent("vscode", vscode_integration)
            
            # Register VS Code operations as task handlers
            await self.assistant.task_manager.register_task_handler(
                "vscode_operation",
                vscode_integration.execute_operation
            )
            
            if vscode_integration.vscode_path:
                print("💻 VS Code integration enabled")
            
            # Register Playwright operations as task handlers
            await self.assistant.task_manager.register_task_handler(
                "playwright_action",
                self.assistant.playwright.execute_action
            )
            
            # Register file operations as task handlers
            await self.assistant.task_manager.register_task_handler(
                "file_operation",
                self.assistant.file_ops.execute_operation
            )
            
            # Register terminal operations as task handlers
            await self.assistant.task_manager.register_task_handler(
                "terminal_command",
                self.assistant.terminal_ops.execute_command
            )
            
        except Exception as e:
            self.logger.error(f"Error setting up integrations: {e}")
            print(f"⚠️  Some integrations failed to initialize: {e}")


async def main():
    """Main entry point"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("assistant.log"),
            logging.StreamHandler()
        ]
    )
    
    # Create and run CLI
    cli = AIDeveloperAssistantCLI()
    await cli.run()


if __name__ == "__main__":
    asyncio.run(main())