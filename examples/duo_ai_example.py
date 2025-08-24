#!/usr/bin/env python3
"""
Example usage of the Duo AI System
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents.duo_ai_orchestrator import DuoAIOrchestrator
from src.agents.message_types import AgentMessage
from src.config.settings import get_settings


class DuoAIExample:
    """Example usage of the Duo AI System"""
    
    def __init__(self):
        self.settings = get_settings()
        self.orchestrator = None
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    async def run_example(self) -> None:
        """Run the Duo AI example"""
        print("Duo AI System Example")
        print("====================")
        print()
        
        # Initialize orchestrator
        self.orchestrator = DuoAIOrchestrator()
        await self.orchestrator.initialize()
        
        try:
            # Start orchestrator in background
            orchestrator_task = asyncio.create_task(self.orchestrator.start())
            
            # Let the system run for a while to demonstrate interactions
            print("Starting Duo AI System...")
            print("Watch the logs to see GuideAI and ImplementAI interacting!")
            print()
            
            # Run for 2 minutes to demonstrate the system
            await asyncio.sleep(120)
            
            # Print status
            await self._print_status()
            
            # Stop orchestrator
            await self.orchestrator.stop()
            await orchestrator_task
            
        except Exception as e:
            self.logger.error(f"Error in example: {e}")
            if self.orchestrator:
                await self.orchestrator.stop()
    
    async def _print_status(self) -> None:
        """Print current system status"""
        if not self.orchestrator:
            return
        
        try:
            summary = await self.orchestrator.get_orchestrator_summary()
            
            print("\nSystem Status:")
            print("-------------")
            print(f"Current Phase: {summary['current_phase']}")
            print(f"Total Conversations: {summary['total_conversations']}")
            print(f"Active Conversations: {summary['active_conversations']}")
            print(f"Achieved Milestones: {summary['achieved_milestones']}/{summary['total_milestones']}")
            
            project_health = summary.get('project_health', {})
            print(f"Project Health: {project_health.get('status', 'unknown')} "
                  f"({project_health.get('overall_score', 0):.1f}%)")
            
            implementation_summary = summary.get('implementation_summary', {})
            print(f"Implementation Success Rate: {implementation_summary.get('success_rate', 0):.1f}%")
            print(f"Total Tasks Completed: {implementation_summary.get('completed_tasks', 0)}")
            
            print("\nRecent Collaboration Insights:")
            insights = summary.get('collaboration_insights', [])
            for i, insight in enumerate(insights[-3:], 1):  # Show last 3 insights
                print(f"  {i}. {insight}")
            
        except Exception as e:
            self.logger.error(f"Error printing status: {e}")


async def main():
    """Main entry point"""
    example = DuoAIExample()
    await example.run_example()


if __name__ == "__main__":
    asyncio.run(main())