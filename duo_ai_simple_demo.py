#!/usr/bin/env python3
"""
Simple Duo AI System Demo - Demonstrates the concept without complex dependencies
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ProjectPhase(Enum):
    """Project phases"""
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"


@dataclass
class AgentMessage:
    """Message structure for agent communication"""
    sender: str
    recipient: str
    message_type: str
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: Optional[str] = None


@dataclass
class ConversationMessage:
    """Message for AI agent conversations"""
    conversation_id: str
    message: str
    context: Dict[str, Any]
    response_expected: bool = True
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProjectMilestone:
    """Represents a project milestone"""
    id: str
    name: str
    description: str
    phase: ProjectPhase
    criteria: List[str]
    status: str = "pending"
    achieved_at: Optional[datetime] = None


class SimpleGuideAI:
    """Simplified GuideAI Agent"""
    
    def __init__(self):
        self.logger = logging.getLogger("GuideAI")
        self.current_phase = ProjectPhase.PLANNING
        self.project_context = {}
        self.guidance_history = []
        self.message_queue = asyncio.Queue()
        self.is_running = False
        
        # Strategic knowledge
        self.strategic_patterns = {
            "web_application": {
                "architecture": "Microservices or Monolithic based on scale",
                "key_focus": ["User experience", "Performance", "Security"],
                "recommended_tools": ["React/Vue", "Node.js", "Docker", "Kubernetes"]
            },
            "api_service": {
                "architecture": "RESTful or GraphQL API",
                "key_focus": ["Performance", "Scalability", "Documentation"],
                "recommended_tools": ["FastAPI", "Django REST", "PostgreSQL", "Redis"]
            }
        }
        
        self.best_practices = {
            "code_quality": [
                "Write clean, readable code",
                "Follow consistent naming conventions",
                "Implement proper error handling"
            ],
            "testing": [
                "Write unit tests for all critical functions",
                "Implement integration tests",
                "Maintain high test coverage"
            ]
        }
    
    async def initialize(self):
        """Initialize GuideAI"""
        self.logger.info("Initializing GuideAI...")
        self.project_context = {
            "start_time": datetime.now().isoformat(),
            "current_phase": self.current_phase.value,
            "total_guidance_sessions": 0
        }
        self.logger.info("GuideAI initialized")
    
    async def start(self):
        """Start GuideAI"""
        self.logger.info("Starting GuideAI...")
        self.is_running = True
        
        try:
            await self._process_messages()
        except KeyboardInterrupt:
            self.logger.info("Shutting down GuideAI...")
            await self.stop()
    
    async def stop(self):
        """Stop GuideAI"""
        self.logger.info("Stopping GuideAI...")
        self.is_running = False
    
    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages"""
        self.logger.info(f"GuideAI received: {message.message_type} from {message.sender}")
        await self.message_queue.put(message)
    
    async def _process_messages(self):
        """Process messages"""
        while self.is_running:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self._handle_message_content(message)
            except asyncio.TimeoutError:
                continue
    
    async def _handle_message_content(self, message: AgentMessage):
        """Handle specific message content"""
        if message.message_type == "phase_update":
            await self._handle_phase_update(message.content)
        elif message.message_type == "implementation_status":
            await self._handle_implementation_status(message.content)
        elif message.message_type == "strategic_query":
            await self._handle_strategic_query(message.content)
    
    async def _handle_phase_update(self, content: Dict[str, Any]):
        """Handle phase update"""
        new_phase = content.get("phase")
        old_phase = self.current_phase
        
        self.current_phase = ProjectPhase(new_phase)
        self.project_context["current_phase"] = new_phase
        
        self.logger.info(f"Phase transition: {old_phase.value} -> {new_phase}")
        
        # Provide guidance
        guidance = await self._generate_phase_guidance(new_phase)
        self.logger.info(f"Guidance provided for {new_phase} phase")
    
    async def _handle_implementation_status(self, content: Dict[str, Any]):
        """Handle implementation status"""
        progress = content.get("progress", 0)
        challenges = content.get("challenges", [])
        
        self.logger.info(f"Implementation status: {progress}% complete, {len(challenges)} challenges")
        
        if challenges:
            guidance = await self._analyze_challenges(challenges)
            self.logger.info(f"Provided guidance for {len(challenges)} challenges")
    
    async def _handle_strategic_query(self, content: Dict[str, Any]):
        """Handle strategic query"""
        query_type = content.get("query_type")
        self.logger.info(f"Strategic query handled: {query_type}")
    
    async def _generate_phase_guidance(self, phase: str) -> Dict[str, Any]:
        """Generate phase guidance"""
        guidance = {
            "phase_overview": f"Guidance for {phase} phase",
            "key_focus": ["Focus on quality", "Follow best practices"],
            "success_criteria": ["Meet requirements", "Pass tests"],
            "recommendations": ["Plan carefully", "Execute diligently"]
        }
        return guidance
    
    async def _analyze_challenges(self, challenges: List[str]) -> Dict[str, Any]:
        """Analyze challenges and provide guidance"""
        return {
            "total_challenges": len(challenges),
            "recommendations": ["Address challenges systematically", "Learn from experience"]
        }
    
    async def get_project_summary(self) -> Dict[str, Any]:
        """Get project summary"""
        return {
            "current_phase": self.current_phase.value,
            "project_context": self.project_context,
            "total_guidance_sessions": len(self.guidance_history)
        }


class SimpleImplementAI:
    """Simplified ImplementAI Agent"""
    
    def __init__(self):
        self.logger = logging.getLogger("ImplementAI")
        self.message_queue = asyncio.Queue()
        self.is_running = False
        
        # Task management
        self.pending_tasks = []
        self.completed_tasks = []
        
        # Capabilities
        self.capabilities = {
            "file_operations": ["create", "read", "update", "delete"],
            "code_generation": ["python", "javascript", "java"],
            "testing": ["unit", "integration", "functional"],
            "deployment": ["build", "deploy", "monitor"]
        }
    
    async def initialize(self):
        """Initialize ImplementAI"""
        self.logger.info("Initializing ImplementAI...")
        self.logger.info("ImplementAI initialized")
    
    async def start(self):
        """Start ImplementAI"""
        self.logger.info("Starting ImplementAI...")
        self.is_running = True
        
        try:
            await self._process_messages()
        except KeyboardInterrupt:
            self.logger.info("Shutting down ImplementAI...")
            await self.stop()
    
    async def stop(self):
        """Stop ImplementAI"""
        self.logger.info("Stopping ImplementAI...")
        self.is_running = False
    
    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages"""
        self.logger.info(f"ImplementAI received: {message.message_type} from {message.sender}")
        await self.message_queue.put(message)
    
    async def _process_messages(self):
        """Process messages"""
        while self.is_running:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self._handle_message_content(message)
            except asyncio.TimeoutError:
                continue
    
    async def _handle_message_content(self, message: AgentMessage):
        """Handle specific message content"""
        if message.message_type == "task_assignment":
            await self._handle_task_assignment(message.content)
        elif message.message_type == "phase_guidance":
            await self._handle_phase_guidance(message.content)
        elif message.message_type == "execution_command":
            await self._handle_execution_command(message.content)
    
    async def _handle_task_assignment(self, content: Dict[str, Any]):
        """Handle task assignment"""
        task_id = content.get("task_id", f"task_{len(self.pending_tasks)}")
        task_name = content.get("task_name", "Unknown Task")
        
        task = {
            "id": task_id,
            "name": task_name,
            "status": "pending",
            "created_at": datetime.now()
        }
        
        self.pending_tasks.append(task)
        self.logger.info(f"Task assigned: {task_name}")
        
        # Simulate task execution
        await asyncio.sleep(2)  # Simulate work
        
        # Complete task
        task["status"] = "completed"
        task["completed_at"] = datetime.now()
        self.completed_tasks.append(task)
        self.pending_tasks.remove(task)
        
        self.logger.info(f"Task completed: {task_name}")
        
        # Report status
        await self._report_status()
    
    async def _handle_phase_guidance(self, content: Dict[str, Any]):
        """Handle phase guidance"""
        phase = content.get("phase")
        guidance = content.get("guidance", {})
        
        self.logger.info(f"Phase guidance received for {phase}")
        self.logger.info(f"Guidance: {guidance.get('phase_overview', 'No overview')}")
    
    async def _handle_execution_command(self, content: Dict[str, Any]):
        """Handle execution command"""
        command = content.get("command", "echo 'Hello World'")
        
        self.logger.info(f"Executing command: {command}")
        
        # Simulate command execution
        await asyncio.sleep(1)
        
        self.logger.info(f"Command executed successfully")
    
    async def _report_status(self):
        """Report implementation status"""
        progress = len(self.completed_tasks) / max(1, len(self.completed_tasks) + len(self.pending_tasks)) * 100
        challenges = ["Integration complexity", "Performance optimization"] if len(self.pending_tasks) > 3 else []
        
        status_message = {
            "progress": progress,
            "status": "active",
            "completed_tasks": len(self.completed_tasks),
            "pending_tasks": len(self.pending_tasks),
            "challenges": challenges
        }
        
        self.logger.info(f"Status reported: {progress:.1f}% complete")
        
        # This would be sent to GuideAI in the full system
        return status_message
    
    async def get_implementation_summary(self) -> Dict[str, Any]:
        """Get implementation summary"""
        return {
            "total_tasks": len(self.completed_tasks) + len(self.pending_tasks),
            "completed_tasks": len(self.completed_tasks),
            "pending_tasks": len(self.pending_tasks),
            "success_rate": 100.0,  # Simplified
            "capabilities": list(self.capabilities.keys())
        }


class SimpleDuoAIOrchestrator:
    """Simplified Duo AI Orchestrator"""
    
    def __init__(self):
        self.logger = logging.getLogger("DuoAIOrchestrator")
        self.guide_ai = SimpleGuideAI()
        self.implement_ai = SimpleImplementAI()
        self.is_running = False
        
        # Conversation management
        self.conversation_history = []
        self.current_phase = ProjectPhase.PLANNING
        
        # Project milestones
        self.milestones = [
            ProjectMilestone(
                id="planning_complete",
                name="Planning Complete",
                description="All planning activities finished",
                phase=ProjectPhase.PLANNING,
                criteria=["Requirements documented", "Architecture designed"]
            ),
            ProjectMilestone(
                id="development_complete",
                name="Development Complete",
                description="Core development finished",
                phase=ProjectPhase.DEVELOPMENT,
                criteria=["Features implemented", "Tests passing"]
            )
        ]
    
    async def initialize(self):
        """Initialize orchestrator"""
        self.logger.info("Initializing Duo AI Orchestrator...")
        
        await self.guide_ai.initialize()
        await self.implement_ai.initialize()
        
        self.logger.info("Duo AI Orchestrator initialized")
    
    async def start(self):
        """Start orchestrator"""
        self.logger.info("Starting Duo AI Orchestrator...")
        self.is_running = True
        
        # Start agents
        guide_task = asyncio.create_task(self.guide_ai.start())
        implement_task = asyncio.create_task(self.implement_ai.start())
        
        # Start orchestrator tasks
        orchestrator_tasks = [
            asyncio.create_task(self._manage_conversations()),
            asyncio.create_task(self._simulate_project_progress()),
            asyncio.create_task(self._monitor_and_coordinate())
        ]
        
        try:
            await asyncio.gather(guide_task, implement_task, *orchestrator_tasks)
        except KeyboardInterrupt:
            self.logger.info("Shutting down Duo AI Orchestrator...")
            await self.stop()
    
    async def stop(self):
        """Stop orchestrator"""
        self.logger.info("Stopping Duo AI Orchestrator...")
        self.is_running = False
        
        await self.guide_ai.stop()
        await self.implement_ai.stop()
        
        await self._print_final_summary()
    
    async def _manage_conversations(self):
        """Manage conversations between agents"""
        while self.is_running:
            try:
                # Start a conversation every 30 seconds
                await asyncio.sleep(30)
                
                if self.is_running:
                    await self._start_conversation()
                
            except Exception as e:
                self.logger.error(f"Error managing conversations: {e}")
    
    async def _start_conversation(self):
        """Start a conversation between agents"""
        conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
        
        # Determine conversation topic based on current phase
        topics = {
            ProjectPhase.PLANNING: ["requirements", "architecture", "technology"],
            ProjectPhase.DEVELOPMENT: ["implementation", "testing", "code quality"],
            ProjectPhase.TESTING: ["test results", "bug fixes", "performance"],
            ProjectPhase.DEPLOYMENT: ["deployment strategy", "monitoring", "rollout"],
            ProjectPhase.MAINTENANCE: ["optimization", "user feedback", "stability"]
        }
        
        topic = topics[self.current_phase][0]
        
        self.logger.info(f"Starting conversation: {topic}")
        
        # Simulate conversation
        await self._simulate_conversation(conversation_id, topic)
    
    async def _simulate_conversation(self, conversation_id: str, topic: str):
        """Simulate a conversation between agents"""
        # GuideAI starts
        guide_message = f"GuideAI: Let's discuss {topic} in the {self.current_phase.value} phase. What's your current status?"
        self.logger.info(f"Conversation {conversation_id}: {guide_message}")
        
        await asyncio.sleep(1)
        
        # ImplementAI responds
        implement_message = f"ImplementAI: I'm making good progress on {topic}. Current status shows 75% completion with some integration challenges."
        self.logger.info(f"Conversation {conversation_id}: {implement_message}")
        
        await asyncio.sleep(1)
        
        # GuideAI provides guidance
        guide_response = f"GuideAI: Based on your progress, I recommend focusing on the integration challenges and ensuring all requirements are met before proceeding."
        self.logger.info(f"Conversation {conversation_id}: {guide_response}")
        
        # Store conversation
        conversation = {
            "id": conversation_id,
            "topic": topic,
            "phase": self.current_phase.value,
            "messages": [guide_message, implement_message, guide_response],
            "timestamp": datetime.now().isoformat()
        }
        
        self.conversation_history.append(conversation)
        
        self.logger.info(f"Conversation {conversation_id} completed")
    
    async def _simulate_project_progress(self):
        """Simulate project progress"""
        while self.is_running:
            try:
                # Simulate progress every 45 seconds
                await asyncio.sleep(45)
                
                if self.is_running:
                    await self._advance_project()
                
            except Exception as e:
                self.logger.error(f"Error simulating progress: {e}")
    
    async def _advance_project(self):
        """Advance project progress"""
        # Assign tasks to ImplementAI
        task_message = AgentMessage(
            sender="orchestrator",
            recipient="implement_ai",
            message_type="task_assignment",
            content={
                "task_id": f"task_{len(self.implement_ai.completed_tasks) + 1}",
                "task_name": f"Development task in {self.current_phase.value}",
                "task_type": "development"
            }
        )
        
        await self.implement_ai.handle_message(task_message)
        
        # Check for phase transition
        if len(self.implement_ai.completed_tasks) % 3 == 0:  # Every 3 tasks
            await self._transition_phase()
    
    async def _transition_phase(self):
        """Transition to next phase"""
        phases = list(ProjectPhase)
        current_index = phases.index(self.current_phase)
        
        if current_index < len(phases) - 1:
            old_phase = self.current_phase
            new_phase = phases[current_index + 1]
            
            self.current_phase = new_phase
            
            # Notify agents
            phase_message = AgentMessage(
                sender="orchestrator",
                recipient="all",
                message_type="phase_update",
                content={"phase": new_phase.value, "previous_phase": old_phase.value}
            )
            
            await self.guide_ai.handle_message(phase_message)
            await self.implement_ai.handle_message(phase_message)
            
            self.logger.info(f"Phase transition: {old_phase.value} -> {new_phase.value}")
    
    async def _monitor_and_coordinate(self):
        """Monitor and coordinate agent activities"""
        while self.is_running:
            try:
                # Monitor every 60 seconds
                await asyncio.sleep(60)
                
                if self.is_running:
                    # Get status from both agents
                    guide_summary = await self.guide_ai.get_project_summary()
                    implement_summary = await self.implement_ai.get_implementation_summary()
                    
                    self.logger.info(f"Project Status - Phase: {guide_summary['current_phase']}, "
                                   f"Tasks: {implement_summary['completed_tasks']}/{implement_summary['total_tasks']}, "
                                   f"Conversations: {len(self.conversation_history)}")
                
            except Exception as e:
                self.logger.error(f"Error monitoring: {e}")
    
    async def _print_final_summary(self):
        """Print final summary"""
        print("\n" + "="*60)
        print("SIMPLE DUO AI SYSTEM - FINAL SUMMARY")
        print("="*60)
        
        guide_summary = await self.guide_ai.get_project_summary()
        implement_summary = await self.implement_ai.get_implementation_summary()
        
        print(f"Current Phase: {guide_summary['current_phase']}")
        print(f"Total Conversations: {len(self.conversation_history)}")
        print(f"Tasks Completed: {implement_summary['completed_tasks']}/{implement_summary['total_tasks']}")
        print(f"Success Rate: {implement_summary['success_rate']:.1f}%")
        
        print("\nRecent Conversations:")
        for conv in self.conversation_history[-3:]:
            print(f"  - {conv['topic']} ({conv['phase']} phase)")
        
        print("\nAgent Capabilities:")
        print(f"  GuideAI: Strategic guidance and project oversight")
        print(f"  ImplementAI: {', '.join(implement_summary['capabilities'])}")
        
        print("="*60)


async def main():
    """Main entry point"""
    print("Simple Duo AI System Demo")
    print("=" * 40)
    print("This demo shows the interaction between GuideAI and ImplementAI")
    print("agents as they collaborate on a software development project.")
    print()
    print("Features demonstrated:")
    print("- Agent-to-agent conversations")
    print("- Project phase management")
    print("- Task assignment and execution")
    print("- Progress monitoring")
    print("- Collaborative decision making")
    print()
    print("Press Ctrl+C to stop the demo")
    print()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run orchestrator
    orchestrator = SimpleDuoAIOrchestrator()
    await orchestrator.initialize()
    await orchestrator.start()


if __name__ == "__main__":
    asyncio.run(main())