#!/usr/bin/env python3
"""
Duo AI System Demo - Demonstrates the interaction between GuideAI and ImplementAI agents
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents.duo_ai_orchestrator import DuoAIOrchestrator
from src.config.settings import get_settings


class DuoAIDemo:
    """Demo application for the Duo AI System"""
    
    def __init__(self):
        self.settings = get_settings()
        self.orchestrator = None
        self.logger = self._setup_logging()
        self.running = False
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.settings.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.settings.log_file),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    async def start(self) -> None:
        """Start the Duo AI demo"""
        self.logger.info("Starting Duo AI Demo...")
        
        # Initialize orchestrator
        self.orchestrator = DuoAIOrchestrator()
        await self.orchestrator.initialize()
        
        # Set up signal handlers
        self._setup_signal_handlers()
        
        self.running = True
        self.logger.info("Duo AI Demo started successfully")
        
        try:
            # Start orchestrator
            await self.orchestrator.start()
            
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        except Exception as e:
            self.logger.error(f"Error in Duo AI demo: {e}")
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the Duo AI demo"""
        if not self.running:
            return
            
        self.logger.info("Stopping Duo AI Demo...")
        self.running = False
        
        if self.orchestrator:
            await self.orchestrator.stop()
        
        # Print final summary
        await self._print_final_summary()
        
        self.logger.info("Duo AI Demo stopped")
    
    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _print_final_summary(self) -> None:
        """Print final summary of the demo"""
        if not self.orchestrator:
            return
        
        try:
            summary = await self.orchestrator.get_orchestrator_summary()
            
            print("\n" + "="*60)
            print("DUO AI DEMO - FINAL SUMMARY")
            print("="*60)
            print(f"Current Phase: {summary['current_phase']}")
            print(f"Total Conversations: {summary['total_conversations']}")
            print(f"Active Conversations: {summary['active_conversations']}")
            print(f"Achieved Milestones: {summary['achieved_milestones']}/{summary['total_milestones']}")
            print(f"Total Decisions Made: {summary['total_decisions_made']}")
            
            project_health = summary.get('project_health', {})
            print(f"Project Health: {project_health.get('status', 'unknown')} "
                  f"({project_health.get('overall_score', 0):.1f}%)")
            
            implementation_summary = summary.get('implementation_summary', {})
            print(f"Implementation Success Rate: {implementation_summary.get('success_rate', 0):.1f}%")
            print(f"Total Tasks Completed: {implementation_summary.get('completed_tasks', 0)}")
            
            print("\nCollaboration Insights:")
            insights = summary.get('collaboration_insights', [])
            for i, insight in enumerate(insights[-5:], 1):  # Show last 5 insights
                print(f"  {i}. {insight}")
            
            print("="*60)
            
        except Exception as e:
            self.logger.error(f"Error printing final summary: {e}")
    
    async def run_demo_scenario(self) -> None:
        """Run a specific demo scenario"""
        self.logger.info("Running demo scenario...")
        
        # This would contain specific demo scenarios
        # For now, we'll let the orchestrator run naturally
        
        # Example scenarios could include:
        # 1. Project planning phase
        # 2. Development phase with challenges
        # 3. Testing phase with bug fixes
        # 4. Deployment phase
        # 5. Maintenance phase with optimization
        
        self.logger.info("Demo scenario completed")


async def main():
    """Main entry point"""
    print("Duo AI System Demo")
    print("==================")
    print("This demo showcases the interaction between GuideAI and ImplementAI agents")
    print("as they collaborate on a software development project from planning to deployment.")
    print()
    print("Features demonstrated:")
    print("- Agent-to-agent conversations")
    print("- Project phase management")
    print("- Task assignment and execution")
    print("- Progress monitoring and reporting")
    print("- Milestone tracking")
    print("- Collaborative decision making")
    print()
    print("Press Ctrl+C to stop the demo")
    print()
    
    # Create and run demo
    demo = DuoAIDemo()
    await demo.start()


if __name__ == "__main__":
    asyncio.run(main())