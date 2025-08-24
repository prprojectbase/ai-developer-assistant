"""
Duo AI Orchestrator - Manages the interaction between GuideAI and ImplementAI agents
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import uuid

from ..config.settings import get_settings
from ..agents.message_types import (
    AgentMessage, ProjectPhaseMessage, ImplementationStatusMessage,
    TaskAssignmentMessage, GuidanceRequestMessage, ImplementationResultMessage,
    ConversationMessage
)
from ..agents.guide_ai import GuideAI
from ..agents.implement_ai import ImplementAI
from ..agents.communication_agent import CommunicationAgent
from ..utils.performance_monitor import PerformanceMonitor


@dataclass
class ConversationSession:
    """Represents a conversation session between GuideAI and ImplementAI"""
    session_id: str
    topic: str
    phase: str
    messages: List[ConversationMessage] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)
    outcomes: List[str] = field(default_factory=list)


@dataclass
class ProjectMilestone:
    """Represents a project milestone"""
    id: str
    name: str
    description: str
    phase: str
    criteria: List[str]
    status: str = "pending"
    achieved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DuoAIOrchestrator:
    """Orchestrates the interaction between GuideAI and ImplementAI agents"""
    
    def __init__(self, communication_agent: CommunicationAgent = None):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Use provided communication agent or create new one
        self.communication_agent = communication_agent
        
        # Initialize AI agents
        self.guide_ai = GuideAI()
        self.implement_ai = ImplementAI()
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()
        
        # Conversation management
        self.active_conversations: Dict[str, ConversationSession] = {}
        self.conversation_history: List[ConversationSession] = []
        
        # Project management
        self.current_phase = "planning"
        self.project_milestones: List[ProjectMilestone] = []
        self.project_context = {
            "start_time": datetime.now().isoformat(),
            "total_conversations": 0,
            "decisions_made": [],
            "lessons_learned": []
        }
        
        # Communication queues
        self.guide_to_implement_queue = asyncio.Queue()
        self.implement_to_guide_queue = asyncio.Queue()
        
        # Orchestrator state
        self.is_running = False
        self.session_id_counter = 0
        
        # Initialize project milestones
        self._initialize_project_milestones()
        
    def _initialize_project_milestones(self) -> None:
        """Initialize project milestones for each phase"""
        milestones = [
            ProjectMilestone(
                id="planning_complete",
                name="Planning Complete",
                description="All planning activities finished and approved",
                phase="planning",
                criteria=[
                    "Requirements documented and approved",
                    "Architecture designed and reviewed",
                    "Technology stack selected",
                    "Project timeline finalized",
                    "Resources allocated"
                ]
            ),
            ProjectMilestone(
                id="development_complete",
                name="Development Complete",
                description="Core development activities finished",
                phase="development",
                criteria=[
                    "All core features implemented",
                    "Unit tests passing",
                    "Code review standards met",
                    "Integration tests successful",
                    "Documentation complete"
                ]
            ),
            ProjectMilestone(
                id="testing_complete",
                name="Testing Complete",
                description="All testing activities finished",
                phase="testing",
                criteria=[
                    "All test cases passing",
                    "Performance benchmarks met",
                    "Security vulnerabilities resolved",
                    "User acceptance achieved",
                    "Test reports complete"
                ]
            ),
            ProjectMilestone(
                id="deployment_complete",
                name="Deployment Complete",
                description="Production deployment successful",
                phase="deployment",
                criteria=[
                    "Successful deployment to production",
                    "Systems operational and stable",
                    "Monitoring active and alerting",
                    "Performance within SLA",
                    "Deployment documentation complete"
                ]
            ),
            ProjectMilestone(
                id="maintenance_ready",
                name="Maintenance Ready",
                description="Project ready for maintenance phase",
                phase="maintenance",
                criteria=[
                    "Maintenance procedures documented",
                    "Monitoring systems in place",
                    "Support team trained",
                    "Backup and recovery procedures tested",
                    "Knowledge transfer complete"
                ]
            )
        ]
        
        self.project_milestones = milestones
    
    async def initialize(self) -> None:
        """Initialize the Duo AI Orchestrator"""
        self.logger.info("Initializing Duo AI Orchestrator...")
        
        # Initialize performance monitor
        await self.performance_monitor.initialize()
        
        # Register agents with communication agent if available
        if self.communication_agent:
            await self.communication_agent.register_agent("guide_ai", self.guide_ai)
            await self.communication_agent.register_agent("implement_ai", self.implement_ai)
        
        # Initialize AI agents
        await self.guide_ai.initialize()
        await self.implement_ai.initialize()
        
        # Set up communication channels
        await self._setup_communication_channels()
        
        self.logger.info("Duo AI Orchestrator initialized successfully")
    
    async def start(self) -> None:
        """Start the Duo AI Orchestrator"""
        if self.is_running:
            self.logger.warning("Duo AI Orchestrator is already running")
            return
            
        self.logger.info("Starting Duo AI Orchestrator...")
        self.is_running = True
        
        # Start AI agents
        guide_task = asyncio.create_task(self.guide_ai.start())
        implement_task = asyncio.create_task(self.implement_ai.start())
        
        # Start orchestrator tasks
        orchestrator_tasks = [
            asyncio.create_task(self._manage_conversations()),
            asyncio.create_task(self._facilitate_communication()),
            asyncio.create_task(self._monitor_project_progress()),
            asyncio.create_task(self._handle_milestones()),
            asyncio.create_task(self._optimize_collaboration()),
            asyncio.create_task(self._generate_insights())
        ]
        
        self.logger.info("Duo AI Orchestrator started successfully")
        
        try:
            await asyncio.gather(guide_task, implement_task, *orchestrator_tasks)
        except KeyboardInterrupt:
            self.logger.info("Shutting down Duo AI Orchestrator...")
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the Duo AI Orchestrator"""
        self.logger.info("Stopping Duo AI Orchestrator...")
        self.is_running = False
        
        # Stop AI agents
        await self.guide_ai.stop()
        await self.implement_ai.stop()
        
        # Stop performance monitor
        await self.performance_monitor.stop_monitoring()
        
        # Save conversation history
        await self._save_conversation_history()
        
        # Save project context
        await self._save_project_context()
        
        self.logger.info("Duo AI Orchestrator stopped")
    
    async def _setup_communication_channels(self) -> None:
        """Set up communication channels between agents"""
        self.logger.info("Setting up communication channels...")
        
        if self.communication_agent:
            # Use the existing communication agent
            self.logger.info("Using existing CommunicationAgent for agent communication")
        else:
            # Set up direct message passing as fallback
            self.logger.info("No CommunicationAgent provided, using direct message passing")
        
        self.logger.info("Communication channels established")
    
    async def _manage_conversations(self) -> None:
        """Manage conversations between GuideAI and ImplementAI"""
        while self.is_running:
            try:
                # Check if new conversation is needed
                if await self._should_start_conversation():
                    await self._start_conversation()
                
                # Manage active conversations
                await self._process_active_conversations()
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error managing conversations: {e}")
                await asyncio.sleep(5)
    
    async def _should_start_conversation(self) -> bool:
        """Determine if a new conversation should be started"""
        # Check if there are active conversations
        if len(self.active_conversations) >= 3:  # Limit concurrent conversations
            return False
        
        # Check if it's time for a scheduled conversation
        current_time = datetime.now()
        last_conversation_time = self._get_last_conversation_time()
        
        if last_conversation_time:
            time_since_last = (current_time - last_conversation_time).total_seconds()
            if time_since_last < 300:  # 5 minutes between conversations
                return False
        
        # Check if there are topics that need discussion
        urgent_topics = await self._get_urgent_conversation_topics()
        if urgent_topics:
            return True
        
        # Check if project phase transition is needed
        if await self._should_transition_phase():
            return True
        
        return False
    
    async def _start_conversation(self) -> None:
        """Start a new conversation between agents"""
        self.session_id_counter += 1
        session_id = f"session_{self.session_id_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Determine conversation topic
        topic = await self._determine_conversation_topic()
        
        # Create conversation session
        session = ConversationSession(
            session_id=session_id,
            topic=topic,
            phase=self.current_phase,
            context={
                "project_phase": self.current_phase,
                "project_context": self.project_context,
                "active_milestones": [m for m in self.project_milestones if m.status == "pending"]
            }
        )
        
        self.active_conversations[session_id] = session
        
        # Start conversation with initial message
        await self._send_conversation_message(
            session_id,
            "guide_ai",
            f"Let's discuss {topic} in the {self.current_phase} phase. What's your current status and challenges?",
            {"topic": topic, "phase": self.current_phase}
        )
        
        self.logger.info(f"Started conversation session: {session_id} - {topic}")
        
        # Update project context
        self.project_context["total_conversations"] += 1
    
    async def _determine_conversation_topic(self) -> str:
        """Determine the topic for the next conversation"""
        urgent_topics = await self._get_urgent_conversation_topics()
        
        if urgent_topics:
            return urgent_topics[0]
        
        # Regular topics based on project phase
        phase_topics = {
            "planning": ["requirements analysis", "architecture design", "technology selection"],
            "development": ["implementation progress", "code quality", "testing strategy"],
            "testing": ["test results", "bug fixes", "performance optimization"],
            "deployment": ["deployment strategy", "infrastructure setup", "monitoring"],
            "maintenance": ["system stability", "user feedback", "optimization opportunities"]
        }
        
        topics = phase_topics.get(self.current_phase, ["general project discussion"])
        return topics[0]  # Return first topic for simplicity
    
    async def _get_urgent_conversation_topics(self) -> List[str]:
        """Get urgent topics that need immediate discussion"""
        urgent_topics = []
        
        # Check for failed tasks
        implement_summary = await self.implement_ai.get_implementation_summary()
        if implement_summary.get("success_rate", 100) < 80:
            urgent_topics.append("implementation challenges and solutions")
        
        # Check for project health issues
        guide_summary = await self.guide_ai.get_project_summary()
        project_health = guide_summary.get("project_health", {})
        if project_health.get("status") == "critical":
            urgent_topics.append("project health and risk mitigation")
        
        # Check for milestone issues
        for milestone in self.project_milestones:
            if milestone.phase == self.current_phase and milestone.status == "pending":
                # Check if milestone is at risk
                if await self._is_milestone_at_risk(milestone):
                    urgent_topics.append(f"milestone at risk: {milestone.name}")
        
        return urgent_topics
    
    async def _is_milestone_at_risk(self, milestone: ProjectMilestone) -> bool:
        """Check if a milestone is at risk"""
        # Simple risk assessment based on phase progress
        if self.current_phase == milestone.phase:
            # Check phase progress
            phase_status = await self.implement_ai._get_phase_status()
            phase_progress = phase_status.get("phase_progress", 0)
            
            # If progress is less than 50% and we're in the second half of the phase
            # (this is a simplified heuristic)
            return phase_progress < 50
        
        return False
    
    async def _process_active_conversations(self) -> None:
        """Process active conversations and facilitate dialogue"""
        completed_sessions = []
        
        for session_id, session in self.active_conversations.items():
            try:
                # Check if conversation should continue
                if await self._should_continue_conversation(session):
                    await self._facilitate_conversation_turn(session)
                else:
                    # End conversation
                    await self._end_conversation(session)
                    completed_sessions.append(session_id)
                
            except Exception as e:
                self.logger.error(f"Error processing conversation {session_id}: {e}")
                await self._end_conversation(session)
                completed_sessions.append(session_id)
        
        # Move completed conversations to history
        for session_id in completed_sessions:
            session = self.active_conversations.pop(session_id)
            self.conversation_history.append(session)
    
    async def _should_continue_conversation(self, session: ConversationSession) -> bool:
        """Determine if a conversation should continue"""
        # Check conversation duration
        duration = (datetime.now() - session.started_at).total_seconds()
        if duration > 600:  # 10 minutes max per conversation
            return False
        
        # Check if conversation has reached a natural conclusion
        if len(session.messages) >= 10:  # Max 10 messages per conversation
            return False
        
        # Check if outcomes have been achieved
        if session.outcomes:
            return False
        
        return True
    
    async def _facilitate_conversation_turn(self, session: ConversationSession) -> None:
        """Facilitate a turn in the conversation"""
        if not session.messages:
            return
        
        last_message = session.messages[-1]
        
        # Determine who should speak next
        if last_message.message.startswith("GuideAI:") or "guide_ai" in last_message.message.lower():
            next_speaker = "implement_ai"
            prompt = f"ImplementAI, please respond to GuideAI about {session.topic}: "
        else:
            next_speaker = "guide_ai"
            prompt = f"GuideAI, please provide guidance on {session.topic} based on ImplementAI's input: "
        
        # Generate response (this would use AI models in practice)
        response = await self._generate_agent_response(next_speaker, prompt, session.context)
        
        # Add response to conversation
        response_message = ConversationMessage(
            conversation_id=session.session_id,
            message=f"{next_speaker.title()}: {response}",
            context=session.context,
            response_expected=False
        )
        
        session.messages.append(response_message)
        
        # Process response for potential actions
        await self._process_conversation_response(session, next_speaker, response)
        
        self.logger.debug(f"Conversation {session.session_id}: {next_speaker} responded")
    
    async def _generate_agent_response(self, agent_type: str, prompt: str, context: Dict[str, Any]) -> str:
        """Generate a response from an AI agent"""
        # This is a simplified response generation
        # In practice, this would use AI models or the actual agents
        
        if agent_type == "guide_ai":
            responses = [
                "Based on the current project status, I recommend focusing on code quality and testing.",
                "I suggest we review the architecture to ensure it meets scalability requirements.",
                "Let's analyze the risks and create a mitigation strategy.",
                "I recommend prioritizing the most critical features first.",
                "Based on best practices, we should implement proper error handling and logging."
            ]
        else:
            responses = [
                "I've implemented the core features and they're working as expected.",
                "I'm encountering some challenges with the database performance.",
                "The tests are passing and the code is ready for review.",
                "I've optimized the algorithms and improved performance significantly.",
                "I need guidance on the best approach for handling edge cases."
            ]
        
        import random
        return random.choice(responses)
    
    async def _process_conversation_response(self, session: ConversationSession, agent_type: str, response: str) -> None:
        """Process a conversation response for potential actions"""
        # Extract action items from response
        action_items = await self._extract_action_items(response)
        
        for action in action_items:
            if agent_type == "guide_ai":
                # GuideAI is providing guidance, create tasks for ImplementAI
                await self._create_implementation_tasks(action)
            else:
                # ImplementAI is providing status, update project context
                await self._update_project_context(action)
        
        # Check for decisions made
        decisions = await self._extract_decisions(response)
        for decision in decisions:
            session.outcomes.append(decision)
            self.project_context["decisions_made"].append({
                "decision": decision,
                "timestamp": datetime.now().isoformat(),
                "session_id": session.session_id
            })
    
    async def _extract_action_items(self, response: str) -> List[str]:
        """Extract action items from a response"""
        # Simple keyword-based extraction
        action_keywords = ["implement", "create", "develop", "test", "deploy", "optimize", "fix", "review"]
        action_items = []
        
        sentences = response.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in action_keywords):
                action_items.append(sentence.strip())
        
        return action_items
    
    async def _extract_decisions(self, response: str) -> List[str]:
        """Extract decisions from a response"""
        # Simple keyword-based extraction
        decision_keywords = ["decide", "determine", "choose", "select", "agree", "confirm"]
        decisions = []
        
        sentences = response.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in decision_keywords):
                decisions.append(sentence.strip())
        
        return decisions
    
    async def _create_implementation_tasks(self, action: str) -> None:
        """Create implementation tasks based on conversation outcomes"""
        # Create a task for ImplementAI
        task_id = f"conv_task_{uuid.uuid4().hex[:8]}"
        
        task_message = TaskAssignmentMessage(
            task_id=task_id,
            task_name=f"Conversation Action: {action[:50]}...",
            task_type="conversation_action",
            priority="medium",
            description=f"Task created from conversation: {action}",
            metadata={"source": "conversation", "action": action}
        )
        
        # Send task to ImplementAI (this would go through the communication system)
        self.logger.info(f"Created implementation task from conversation: {task_id}")
    
    async def _update_project_context(self, action: str) -> None:
        """Update project context based on conversation outcomes"""
        # Extract status information and update context
        if "progress" in action.lower():
            # Update progress information
            self.project_context["last_progress_update"] = datetime.now().isoformat()
        
        if "challenge" in action.lower():
            # Add to challenges list
            self.project_context["challenges"] = self.project_context.get("challenges", [])
            self.project_context["challenges"].append({
                "challenge": action,
                "timestamp": datetime.now().isoformat()
            })
        
        self.logger.info(f"Updated project context from conversation")
    
    async def _end_conversation(self, session: ConversationSession) -> None:
        """End a conversation session"""
        session.ended_at = datetime.now()
        
        # Summarize conversation outcomes
        summary = await self._summarize_conversation(session)
        session.outcomes.append(summary)
        
        self.logger.info(f"Ended conversation session: {session.session_id}")
        self.logger.info(f"Conversation summary: {summary}")
    
    async def _summarize_conversation(self, session: ConversationSession) -> str:
        """Summarize a conversation session"""
        # Simple summary based on messages and outcomes
        message_count = len(session.messages)
        outcome_count = len(session.outcomes)
        
        summary = f"Conversation about {session.topic} with {message_count} messages"
        if outcome_count > 0:
            summary += f" and {outcome_count} outcomes"
        
        return summary
    
    async def _facilitate_communication(self) -> None:
        """Facilitate communication between GuideAI and ImplementAI"""
        while self.is_running:
            try:
                # Process messages from GuideAI to ImplementAI
                while not self.guide_to_implement_queue.empty():
                    message = await self.guide_to_implement_queue.get()
                    await self._route_message_to_implement_ai(message)
                
                # Process messages from ImplementAI to GuideAI
                while not self.implement_to_guide_queue.empty():
                    message = await self.implement_to_guide_queue.get()
                    await self._route_message_to_guide_ai(message)
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Error facilitating communication: {e}")
                await asyncio.sleep(5)
    
    async def _route_message_to_implement_ai(self, message: AgentMessage) -> None:
        """Route a message from GuideAI to ImplementAI"""
        # Convert to appropriate message type and send to ImplementAI
        if message.message_type == "phase_guidance":
            await self.implement_ai.handle_message(message)
        elif message.message_type == "task_assignment":
            await self.implement_ai.handle_message(message)
        else:
            self.logger.warning(f"Unknown message type for ImplementAI: {message.message_type}")
    
    async def _route_message_to_guide_ai(self, message: AgentMessage) -> None:
        """Route a message from ImplementAI to GuideAI"""
        # Convert to appropriate message type and send to GuideAI
        if message.message_type == "implementation_status":
            await self.guide_ai.handle_message(message)
        elif message.message_type == "guidance_request":
            await self.guide_ai.handle_message(message)
        else:
            self.logger.warning(f"Unknown message type for GuideAI: {message.message_type}")
    
    async def _send_conversation_message(self, session_id: str, sender: str, message: str, context: Dict[str, Any]) -> None:
        """Send a message in a conversation"""
        if session_id not in self.active_conversations:
            self.logger.error(f"Session not found: {session_id}")
            return
        
        session = self.active_conversations[session_id]
        
        conversation_message = ConversationMessage(
            conversation_id=session_id,
            message=f"{sender.title()}: {message}",
            context=context,
            response_expected=True
        )
        
        session.messages.append(conversation_message)
        
        # Send message through communication agent if available
        if self.communication_agent:
            # Determine recipient based on sender
            recipient = "implement_ai" if sender == "guide_ai" else "guide_ai"
            
            agent_message = AgentMessage(
                sender=sender,
                recipient=recipient,
                message_type="conversation_message",
                content={
                    "conversation_id": session_id,
                    "message": message,
                    "context": context
                }
            )
            
            await self.communication_agent.send_message(agent_message)
        else:
            # Fallback to direct message passing
            self.logger.debug(f"Would send message directly to {recipient}")
    
    async def _monitor_project_progress(self) -> None:
        """Monitor overall project progress and facilitate coordination"""
        while self.is_running:
            try:
                # Get status from both agents
                guide_summary = await self.guide_ai.get_project_summary()
                implement_summary = await self.implement_ai.get_implementation_summary()
                
                # Check for phase transition
                if await self._should_transition_phase():
                    await self._transition_phase()
                
                # Check for milestone achievements
                await self._check_milestone_achievements()
                
                # Log progress
                self.logger.info(f"Project progress - Phase: {self.current_phase}, "
                               f"Guide sessions: {guide_summary.get('total_guidance_sessions', 0)}, "
                               f"Implement tasks: {implement_summary.get('completed_tasks', 0)}")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error monitoring project progress: {e}")
                await asyncio.sleep(60)
    
    async def _should_transition_phase(self) -> bool:
        """Determine if project should transition to next phase"""
        # Check if current phase milestones are achieved
        current_milestones = [m for m in self.project_milestones if m.phase == self.current_phase]
        
        for milestone in current_milestones:
            if milestone.status != "achieved":
                return False
        
        # Check if there's a next phase
        phases = ["planning", "development", "testing", "deployment", "maintenance"]
        current_index = phases.index(self.current_phase)
        
        return current_index < len(phases) - 1
    
    async def _transition_phase(self) -> None:
        """Transition project to next phase"""
        phases = ["planning", "development", "testing", "deployment", "maintenance"]
        current_index = phases.index(self.current_phase)
        
        if current_index < len(phases) - 1:
            old_phase = self.current_phase
            new_phase = phases[current_index + 1]
            
            self.current_phase = new_phase
            
            # Update project context
            self.project_context["phase_transitions"] = self.project_context.get("phase_transitions", [])
            self.project_context["phase_transitions"].append({
                "from_phase": old_phase,
                "to_phase": new_phase,
                "timestamp": datetime.now().isoformat()
            })
            
            # Notify agents
            await self._notify_phase_transition(old_phase, new_phase)
            
            self.logger.info(f"Phase transition: {old_phase} -> {new_phase}")
    
    async def _notify_phase_transition(self, old_phase: str, new_phase: str) -> None:
        """Notify agents about phase transition"""
        # Send phase transition message to GuideAI
        phase_message = AgentMessage(
            sender="orchestrator",
            recipient="guide_ai",
            message_type="phase_update",
            content={"phase": new_phase, "previous_phase": old_phase}
        )
        
        await self.guide_ai.handle_message(phase_message)
        
        # Send phase transition message to ImplementAI
        await self.implement_ai.handle_message(phase_message)
        
        # Start a conversation about the phase transition
        await self._start_conversation()
    
    async def _handle_milestones(self) -> None:
        """Handle project milestone management"""
        while self.is_running:
            try:
                # Check milestone progress
                for milestone in self.project_milestones:
                    if milestone.status == "pending":
                        progress = await self._calculate_milestone_progress(milestone)
                        
                        if progress >= 100:
                            await self._achieve_milestone(milestone)
                        elif progress >= 75 and milestone.status == "pending":
                            # Mark as in progress
                            milestone.status = "in_progress"
                
                await asyncio.sleep(180)  # Check every 3 minutes
                
            except Exception as e:
                self.logger.error(f"Error handling milestones: {e}")
                await asyncio.sleep(60)
    
    async def _calculate_milestone_progress(self, milestone: ProjectMilestone) -> float:
        """Calculate progress towards a milestone"""
        # This would be more sophisticated in practice
        # For now, use a simple heuristic based on phase progress
        
        if milestone.phase != self.current_phase:
            return 0.0
        
        # Get phase progress from ImplementAI
        phase_status = await self.implement_ai._get_phase_status()
        phase_progress = phase_status.get("phase_progress", 0)
        
        return phase_progress
    
    async def _achieve_milestone(self, milestone: ProjectMilestone) -> None:
        """Mark a milestone as achieved"""
        milestone.status = "achieved"
        milestone.achieved_at = datetime.now()
        
        # Update project context
        self.project_context["achieved_milestones"] = self.project_context.get("achieved_milestones", [])
        self.project_context["achieved_milestones"].append({
            "milestone_id": milestone.id,
            "milestone_name": milestone.name,
            "achieved_at": milestone.achieved_at.isoformat()
        })
        
        # Notify agents
        await self._notify_milestone_achievement(milestone)
        
        self.logger.info(f"Milestone achieved: {milestone.name}")
    
    async def _notify_milestone_achievement(self, milestone: ProjectMilestone) -> None:
        """Notify agents about milestone achievement"""
        # Send notification to both agents
        notification = AgentMessage(
            sender="orchestrator",
            recipient="all",
            message_type="milestone_achieved",
            content={
                "milestone_id": milestone.id,
                "milestone_name": milestone.name,
                "achieved_at": milestone.achieved_at.isoformat()
            }
        )
        
        await self.guide_ai.handle_message(notification)
        await self.implement_ai.handle_message(notification)
        
        # Start a celebration conversation
        await self._start_milestone_conversation(milestone)
    
    async def _start_milestone_conversation(self, milestone: ProjectMilestone) -> None:
        """Start a conversation to celebrate milestone achievement"""
        self.session_id_counter += 1
        session_id = f"milestone_{self.session_id_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = ConversationSession(
            session_id=session_id,
            topic=f"Milestone Achieved: {milestone.name}",
            phase=self.current_phase,
            context={
                "milestone": milestone.__dict__,
                "celebration": True
            }
        )
        
        self.active_conversations[session_id] = session
        
        # Start celebration conversation
        await self._send_conversation_message(
            session_id,
            "guide_ai",
            f"Congratulations! We've achieved the milestone: {milestone.name}. Let's discuss what went well and what we can improve.",
            {"milestone": milestone.name, "achievement": True}
        )
        
        self.logger.info(f"Started milestone celebration conversation: {session_id}")
    
    async def _check_milestone_achievements(self) -> None:
        """Check for milestone achievements"""
        for milestone in self.project_milestones:
            if milestone.status == "pending":
                progress = await self._calculate_milestone_progress(milestone)
                
                if progress >= 100:
                    await self._achieve_milestone(milestone)
    
    async def _optimize_collaboration(self) -> None:
        """Optimize collaboration between agents"""
        while self.is_running:
            try:
                # Analyze collaboration patterns
                collaboration_metrics = await self._analyze_collaboration_patterns()
                
                # Adjust collaboration strategies based on metrics
                if collaboration_metrics.get("conversation_efficiency", 0) < 0.7:
                    # Improve conversation efficiency
                    await self._improve_conversation_efficiency()
                
                if collaboration_metrics.get("task_alignment", 0) < 0.8:
                    # Improve task alignment
                    await self._improve_task_alignment()
                
                await asyncio.sleep(600)  # Optimize every 10 minutes
                
            except Exception as e:
                self.logger.error(f"Error optimizing collaboration: {e}")
                await asyncio.sleep(120)
    
    async def _analyze_collaboration_patterns(self) -> Dict[str, Any]:
        """Analyze collaboration patterns between agents"""
        # Calculate conversation metrics
        total_conversations = len(self.conversation_history) + len(self.active_conversations)
        avg_messages_per_conversation = 0
        
        if self.conversation_history:
            total_messages = sum(len(session.messages) for session in self.conversation_history)
            avg_messages_per_conversation = total_messages / len(self.conversation_history)
        
        # Calculate task completion metrics
        implement_summary = await self.implement_ai.get_implementation_summary()
        task_success_rate = implement_summary.get("success_rate", 0)
        
        return {
            "total_conversations": total_conversations,
            "avg_messages_per_conversation": avg_messages_per_conversation,
            "task_success_rate": task_success_rate,
            "conversation_efficiency": 0.8,  # Placeholder
            "task_alignment": 0.85  # Placeholder
        }
    
    async def _improve_conversation_efficiency(self) -> None:
        """Improve conversation efficiency"""
        self.logger.info("Improving conversation efficiency...")
        
        # Analyze conversation history for patterns
        if self.conversation_history:
            # Find conversations that took too long or had too many messages
            inefficient_sessions = [
                session for session in self.conversation_history
                if len(session.messages) > 8 or 
                (session.ended_at and session.started_at and 
                 (session.ended_at - session.started_at).total_seconds() > 480)
            ]
            
            if inefficient_sessions:
                self.logger.info(f"Found {len(inefficient_sessions)} inefficient conversations")
                # Adjust conversation strategies
    
    async def _improve_task_alignment(self) -> None:
        """Improve task alignment between agents"""
        self.logger.info("Improving task alignment...")
        
        # Analyze task success patterns
        implement_summary = await self.implement_ai.get_implementation_summary()
        
        if implement_summary.get("success_rate", 100) < 80:
            # Focus on improving task quality and alignment
            self.logger.info("Task success rate below threshold, improving alignment")
    
    async def _generate_insights(self) -> None:
        """Generate insights from the collaboration"""
        while self.is_running:
            try:
                # Generate collaboration insights
                insights = await self._generate_collaboration_insights()
                
                # Store insights in project context
                self.project_context["collaboration_insights"] = self.project_context.get("collaboration_insights", [])
                self.project_context["collaboration_insights"].extend(insights)
                
                # Log key insights
                for insight in insights:
                    self.logger.info(f"Collaboration insight: {insight}")
                
                await asyncio.sleep(900)  # Generate insights every 15 minutes
                
            except Exception as e:
                self.logger.error(f"Error generating insights: {e}")
                await asyncio.sleep(180)
    
    async def _generate_collaboration_insights(self) -> List[str]:
        """Generate insights from agent collaboration"""
        insights = []
        
        # Analyze conversation patterns
        if self.conversation_history:
            # Most discussed topics
            topic_counts = {}
            for session in self.conversation_history:
                topic = session.topic
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            if topic_counts:
                most_discussed = max(topic_counts, key=topic_counts.get)
                insights.append(f"Most discussed topic: {most_discussed}")
        
        # Analyze project progress
        guide_summary = await self.guide_ai.get_project_summary()
        project_health = guide_summary.get("project_health", {})
        
        if project_health.get("status") == "healthy":
            insights.append("Project collaboration is effective and healthy")
        elif project_health.get("status") == "warning":
            insights.append("Project collaboration needs attention")
        else:
            insights.append("Project collaboration requires immediate intervention")
        
        # Analyze task completion
        implement_summary = await self.implement_ai.get_implementation_summary()
        success_rate = implement_summary.get("success_rate", 0)
        
        if success_rate > 90:
            insights.append("Implementation success rate is excellent")
        elif success_rate > 80:
            insights.append("Implementation success rate is good")
        else:
            insights.append("Implementation success rate needs improvement")
        
        return insights
    
    def _get_last_conversation_time(self) -> Optional[datetime]:
        """Get the time of the last conversation"""
        if self.conversation_history:
            return self.conversation_history[-1].started_at
        
        if self.active_conversations:
            return min(session.started_at for session in self.active_conversations.values())
        
        return None
    
    async def _save_conversation_history(self) -> None:
        """Save conversation history to file"""
        try:
            filename = f"conversation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            history_data = {
                "active_conversations": [
                    {
                        "session_id": session.session_id,
                        "topic": session.topic,
                        "phase": session.phase,
                        "started_at": session.started_at.isoformat(),
                        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                        "message_count": len(session.messages),
                        "outcomes": session.outcomes,
                        "context": session.context
                    }
                    for session in self.active_conversations.values()
                ],
                "conversation_history": [
                    {
                        "session_id": session.session_id,
                        "topic": session.topic,
                        "phase": session.phase,
                        "started_at": session.started_at.isoformat(),
                        "ended_at": session.ended_at.isoformat(),
                        "message_count": len(session.messages),
                        "outcomes": session.outcomes,
                        "context": session.context
                    }
                    for session in self.conversation_history
                ],
                "project_context": self.project_context,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(filename, 'w') as f:
                json.dump(history_data, f, indent=2)
            
            self.logger.info(f"Conversation history saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving conversation history: {e}")
    
    async def _save_project_context(self) -> None:
        """Save project context to file"""
        try:
            filename = f"project_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            context_data = {
                "project_context": self.project_context,
                "current_phase": self.current_phase,
                "project_milestones": [
                    {
                        "id": milestone.id,
                        "name": milestone.name,
                        "phase": milestone.phase,
                        "status": milestone.status,
                        "achieved_at": milestone.achieved_at.isoformat() if milestone.achieved_at else None
                    }
                    for milestone in self.project_milestones
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            with open(filename, 'w') as f:
                json.dump(context_data, f, indent=2)
            
            self.logger.info(f"Project context saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving project context: {e}")
    
    async def get_orchestrator_summary(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator summary"""
        total_conversations = len(self.conversation_history) + len(self.active_conversations)
        achieved_milestones = [m for m in self.project_milestones if m.status == "achieved"]
        
        # Get agent summaries
        guide_summary = await self.guide_ai.get_project_summary()
        implement_summary = await self.implement_ai.get_implementation_summary()
        
        return {
            "current_phase": self.current_phase,
            "total_conversations": total_conversations,
            "active_conversations": len(self.active_conversations),
            "achieved_milestones": len(achieved_milestones),
            "total_milestones": len(self.project_milestones),
            "project_health": guide_summary.get("project_health", {}),
            "implementation_summary": implement_summary,
            "collaboration_insights": self.project_context.get("collaboration_insights", []),
            "total_decisions_made": len(self.project_context.get("decisions_made", [])),
            "timestamp": datetime.now().isoformat()
        }