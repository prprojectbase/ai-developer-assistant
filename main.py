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
from src.agents.guide_ai import GuideAI
from src.agents.implement_ai import ImplementAI
from src.agents.duo_ai_orchestrator import DuoAIOrchestrator

# New modules for comprehensive end-to-end development
from src.modules.version_control_integration import VersionControlIntegration
from src.modules.database_management import DatabaseManagement
from src.modules.api_development import APIDevelopment
from src.modules.devops_cicd import DevOpsCICD
from src.modules.security_testing import SecurityTesting
from src.modules.containerization_orchestration import ContainerizationOrchestration
from src.modules.cloud_infrastructure import CloudInfrastructure
from src.modules.package_management import PackageManagement


class AIDeveloperAssistantCLI:
    """Command-line interface for the AI Developer Assistant"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.assistant: Optional[AIDeveloperAssistant] = None
        self.guide_ai: Optional[GuideAI] = None
        self.implement_ai: Optional[ImplementAI] = None
        self.duo_ai_orchestrator: Optional[DuoAIOrchestrator] = None
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        if self.assistant:
            asyncio.create_task(self.assistant.stop())
        if self.duo_ai_orchestrator:
            asyncio.create_task(self.duo_ai_orchestrator.stop())
        sys.exit(0)
    
    async def run(self) -> None:
        """Run the AI Developer Assistant"""
        try:
            print("🤖 AI Developer Assistant Starting...")
            print("=" * 50)
            
            # Initialize and start the assistant
            self.assistant = AIDeveloperAssistant()
            await self.assistant.initialize()
            
            # Initialize AI agents
            self.guide_ai = GuideAI()
            self.implement_ai = ImplementAI()
            
            # Register agents with the communication system
            await self.assistant.communication_agent.register_agent("guide_ai", self.guide_ai)
            await self.assistant.communication_agent.register_agent("implement_ai", self.implement_ai)
            
            # Initialize the AI agents
            await self.guide_ai.initialize()
            await self.implement_ai.initialize()
            
            # Create and initialize Duo AI Orchestrator
            self.duo_ai_orchestrator = DuoAIOrchestrator(self.assistant.communication_agent)
            await self.duo_ai_orchestrator.initialize()
            
            # Register agents with main assistant
            await self.assistant.register_agent("guide_ai", self.guide_ai)
            await self.assistant.register_agent("implement_ai", self.implement_ai)
            await self.assistant.register_agent("duo_ai_orchestrator", self.duo_ai_orchestrator)
            
            # Set up additional integrations
            await self._setup_integrations()
            
            print("✅ AI Developer Assistant is ready!")
            print(f"📁 Workspace: {self.settings.workspace_dir}")
            print(f"🌐 Agent Communication: ws://{self.settings.agent_host}:{self.settings.agent_port}")
            print(f"💻 VS Code Integration: {'Available' if self.settings.vscode_port else 'Disabled'}")
            print(f"🧠 OpenRouter API: {'Configured' if self.settings.openrouter_api_key else 'Not Configured'}")
            print("🤖 AI Agents: GuideAI, ImplementAI registered and ready")
            print("🎭 Duo AI Orchestrator: Active and coordinating agents")
            print("=" * 50)
            print("Press Ctrl+C to stop the assistant")
            print()
            
            # Start the assistant
            assistant_task = asyncio.create_task(self.assistant.start())
            orchestrator_task = asyncio.create_task(self.duo_ai_orchestrator.start())
            
            await asyncio.gather(assistant_task, orchestrator_task)
            
        except KeyboardInterrupt:
            print("\n👋 Shutting down AI Developer Assistant...")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            print(f"❌ Fatal error: {e}")
        finally:
            if self.duo_ai_orchestrator:
                await self.duo_ai_orchestrator.stop()
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
            
            # Initialize Version Control Integration
            version_control = VersionControlIntegration()
            await version_control.initialize()
            await self.assistant.register_agent("version_control", version_control)
            
            # Register version control operations as task handlers
            await self.assistant.task_manager.register_task_handler(
                "version_control_operation",
                version_control.execute_operation
            )
            
            print("🔄 Version Control integration enabled")
            
            # Initialize Database Management
            database_mgmt = DatabaseManagement()
            await database_mgmt.initialize()
            await self.assistant.register_agent("database", database_mgmt)
            
            # Register database operations as task handlers
            await self.assistant.task_manager.register_task_handler(
                "database_operation",
                database_mgmt.execute_operation
            )
            
            print("🗄️ Database Management integration enabled")
            
            # Initialize API Development
            api_dev = APIDevelopment()
            await api_dev.initialize()
            await self.assistant.register_agent("api_development", api_dev)
            
            # Register API development operations as task handlers
            await self.assistant.task_manager.register_task_handler(
                "api_development_operation",
                api_dev.execute_operation
            )
            
            print("🌐 API Development integration enabled")
            
            # Initialize DevOps & CI/CD
            devops_cicd = DevOpsCICD()
            await devops_cicd.initialize()
            await self.assistant.register_agent("devops_cicd", devops_cicd)
            
            # Register DevOps operations as task handlers
            await self.assistant.task_manager.register_task_handler(
                "devops_cicd_operation",
                devops_cicd.execute_operation
            )
            
            print("🚀 DevOps & CI/CD integration enabled")
            
            # Initialize Security Testing
            security_testing = SecurityTesting()
            await security_testing.initialize()
            await self.assistant.register_agent("security_testing", security_testing)
            
            # Register security testing operations as task handlers
            await self.assistant.task_manager.register_task_handler(
                "security_testing_operation",
                security_testing.execute_operation
            )
            
            print("🔒 Security Testing integration enabled")
            
            # Initialize Containerization & Orchestration
            containerization = ContainerizationOrchestration()
            await containerization.initialize()
            await self.assistant.register_agent("containerization", containerization)
            
            # Register containerization operations as task handlers
            await self.assistant.task_manager.register_task_handler(
                "containerization_operation",
                containerization.execute_operation
            )
            
            print("📦 Containerization & Orchestration integration enabled")
            
            # Initialize Cloud Infrastructure
            cloud_infra = CloudInfrastructure()
            await cloud_infra.initialize()
            await self.assistant.register_agent("cloud_infrastructure", cloud_infra)
            
            # Register cloud infrastructure operations as task handlers
            await self.assistant.task_manager.register_task_handler(
                "cloud_infrastructure_operation",
                cloud_infra.execute_operation
            )
            
            print("☁️ Cloud Infrastructure integration enabled")
            
            # Initialize Package Management
            package_mgmt = PackageManagement()
            await package_mgmt.initialize()
            await self.assistant.register_agent("package_management", package_mgmt)
            
            # Register package management operations as task handlers
            await self.assistant.task_manager.register_task_handler(
                "package_management_operation",
                package_mgmt.execute_operation
            )
            
            print("📦 Package Management integration enabled")
            
            # Register existing module operations as task handlers
            await self.assistant.task_manager.register_task_handler(
                "playwright_action",
                self.assistant.playwright.execute_action
            )
            
            await self.assistant.task_manager.register_task_handler(
                "file_operation",
                self.assistant.file_ops.execute_operation
            )
            
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