"""
GuideAI Agent - Provides guidance and strategic direction throughout the project lifecycle
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from ..config.settings import get_settings
from ..agents.message_types import AgentMessage
from ..utils.performance_monitor import PerformanceMonitor
from ..agents.agent_client import AgentClient


@dataclass
class ProjectPhase:
    """Represents a phase in the project lifecycle"""
    name: str
    description: str
    key_activities: List[str]
    success_criteria: List[str]
    estimated_duration: str
    dependencies: List[str] = None


class GuideAI:
    """GuideAI Agent - Provides strategic guidance and project oversight"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Project lifecycle phases
        self.project_phases = self._initialize_project_phases()
        
        # Current project state
        self.current_phase = "planning"
        self.project_context = {}
        self.guidance_history = []
        self.implementation_feedback = []
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()
        
        # Communication client
        self.agent_client = AgentClient("guide_ai")
        
        # Communication
        self.message_queue = asyncio.Queue()
        self.is_running = False
        
        # Strategic knowledge base
        self.strategic_patterns = self._initialize_strategic_patterns()
        self.best_practices = self._initialize_best_practices()
        self.risk_assessments = {}
        
    def _initialize_project_phases(self) -> Dict[str, ProjectPhase]:
        """Initialize project lifecycle phases"""
        return {
            "planning": ProjectPhase(
                name="Planning",
                description="Project planning and requirements gathering",
                key_activities=[
                    "Requirements analysis",
                    "Architecture design",
                    "Technology stack selection",
                    "Resource planning",
                    "Timeline estimation"
                ],
                success_criteria=[
                    "Clear requirements documented",
                    "Architecture approved",
                    "Technology stack finalized",
                    "Resource allocation complete"
                ],
                estimated_duration="1-2 weeks"
            ),
            "development": ProjectPhase(
                name="Development",
                description="Core development and implementation",
                key_activities=[
                    "Environment setup",
                    "Core feature development",
                    "Unit testing",
                    "Code reviews",
                    "Integration testing"
                ],
                success_criteria=[
                    "Core features implemented",
                    "Unit tests passing",
                    "Code review standards met",
                    "Integration tests successful"
                ],
                estimated_duration="4-8 weeks",
                dependencies=["planning"]
            ),
            "testing": ProjectPhase(
                name="Testing",
                description="Comprehensive testing and quality assurance",
                key_activities=[
                    "System testing",
                    "Performance testing",
                    "Security testing",
                    "User acceptance testing",
                    "Bug fixing"
                ],
                success_criteria=[
                    "All test cases passing",
                    "Performance benchmarks met",
                    "Security vulnerabilities resolved",
                    "User acceptance achieved"
                ],
                estimated_duration="2-4 weeks",
                dependencies=["development"]
            ),
            "deployment": ProjectPhase(
                name="Deployment",
                description="Production deployment and go-live",
                key_activities=[
                    "Deployment planning",
                    "Infrastructure setup",
                    "Production deployment",
                    "Monitoring setup",
                    "Post-deployment validation"
                ],
                success_criteria=[
                    "Successful deployment",
                    "Systems operational",
                    "Monitoring active",
                    "Performance within SLA"
                ],
                estimated_duration="1-2 weeks",
                dependencies=["testing"]
            ),
            "maintenance": ProjectPhase(
                name="Maintenance",
                description="Ongoing maintenance and optimization",
                key_activities=[
                    "System monitoring",
                    "Bug fixes",
                    "Performance optimization",
                    "Feature enhancements",
                    "Documentation updates"
                ],
                success_criteria=[
                    "System stability maintained",
                    "Performance optimized",
                    "User satisfaction maintained",
                    "Documentation current"
                ],
                estimated_duration="Ongoing",
                dependencies=["deployment"]
            )
        }
    
    def _initialize_strategic_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize strategic patterns for different project types"""
        return {
            "web_application": {
                "architecture": "Microservices or Monolithic based on scale",
                "key_focus": ["User experience", "Performance", "Security"],
                "common_challenges": ["Scalability", "Security", "Cross-browser compatibility"],
                "recommended_tools": ["React/Vue", "Node.js", "Docker", "Kubernetes"]
            },
            "api_service": {
                "architecture": "RESTful or GraphQL API",
                "key_focus": ["Performance", "Scalability", "Documentation"],
                "common_challenges": ["Rate limiting", "Authentication", "Versioning"],
                "recommended_tools": ["FastAPI", "Django REST", "PostgreSQL", "Redis"]
            },
            "data_pipeline": {
                "architecture": "ETL/ELT pipeline",
                "key_focus": ["Data quality", "Performance", "Reliability"],
                "common_challenges": ["Data consistency", "Performance bottlenecks", "Error handling"],
                "recommended_tools": ["Apache Airflow", "Spark", "Kafka", "AWS/GCP services"]
            },
            "machine_learning": {
                "architecture": "ML Pipeline with model serving",
                "key_focus": ["Model accuracy", "Performance", "Monitoring"],
                "common_challenges": ["Model drift", "Performance", "Reproducibility"],
                "recommended_tools": ["TensorFlow/PyTorch", "MLflow", "Docker", "Kubernetes"]
            }
        }
    
    def _initialize_best_practices(self) -> Dict[str, List[str]]:
        """Initialize best practices for different development aspects"""
        return {
            "code_quality": [
                "Write clean, readable code",
                "Follow consistent naming conventions",
                "Implement proper error handling",
                "Add comprehensive comments",
                "Use appropriate design patterns"
            ],
            "testing": [
                "Write unit tests for all critical functions",
                "Implement integration tests",
                "Use mocking for external dependencies",
                "Maintain high test coverage",
                "Automate testing in CI/CD"
            ],
            "security": [
                "Implement proper authentication",
                "Validate all user inputs",
                "Use encryption for sensitive data",
                "Follow principle of least privilege",
                "Regular security audits"
            ],
            "performance": [
                "Profile and optimize bottlenecks",
                "Implement caching strategies",
                "Use database indexing",
                "Optimize database queries",
                "Monitor performance metrics"
            ],
            "deployment": [
                "Use infrastructure as code",
                "Implement blue-green deployments",
                "Automate deployment pipeline",
                "Monitor deployment health",
                "Have rollback procedures"
            ]
        }
    
    async def initialize(self) -> None:
        """Initialize the GuideAI agent"""
        self.logger.info("Initializing GuideAI Agent...")
        
        # Initialize performance monitor
        await self.performance_monitor.initialize()
        
        # Connect to communication agent
        if not await self.agent_client.connect():
            self.logger.error("Failed to connect to CommunicationAgent")
            return
        
        # Register message handlers
        await self.agent_client.register_message_handler("phase_update", self._handle_phase_update)
        await self.agent_client.register_message_handler("implementation_status", self._handle_implementation_status)
        await self.agent_client.register_message_handler("strategic_query", self._handle_strategic_query)
        await self.agent_client.register_message_handler("risk_assessment", self._handle_risk_assessment)
        await self.agent_client.register_message_handler("best_practice_query", self._handle_best_practice_query)
        await self.agent_client.register_message_handler("project_context_update", self._handle_project_context_update)
        
        # Set up project context
        self.project_context = {
            "start_time": datetime.now().isoformat(),
            "current_phase": self.current_phase,
            "phase_start_time": datetime.now().isoformat(),
            "total_guidance_sessions": 0,
            "strategic_decisions": []
        }
        
        self.logger.info("GuideAI Agent initialized successfully")
    
    async def start(self) -> None:
        """Start the GuideAI agent"""
        if self.is_running:
            self.logger.warning("GuideAI Agent is already running")
            return
            
        self.logger.info("Starting GuideAI Agent...")
        self.is_running = True
        
        # Start message listener
        message_listener_task = asyncio.create_task(self.agent_client.start_message_listener())
        
        # Start background tasks
        tasks = [
            message_listener_task,
            asyncio.create_task(self._process_messages()),
            asyncio.create_task(self._monitor_project_progress()),
            asyncio.create_task(self._provide_strategic_guidance()),
            asyncio.create_task(self._analyze_implementation_feedback())
        ]
        
        self.logger.info("GuideAI Agent started successfully")
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            self.logger.info("Shutting down GuideAI Agent...")
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the GuideAI Agent"""
        self.logger.info("Stopping GuideAI Agent...")
        self.is_running = False
        
        # Save guidance history
        await self._save_guidance_history()
        
        # Stop performance monitor
        await self.performance_monitor.stop_monitoring()
        
        # Stop agent client
        await self.agent_client.stop()
        
        self.logger.info("GuideAI Agent stopped")
    
    async def handle_message(self, message: AgentMessage) -> None:
        """Handle incoming messages"""
        self.logger.info(f"GuideAI received message from {message.sender}: {message.message_type}")
        
        await self.message_queue.put(message)
    
    async def _process_messages(self) -> None:
        """Process messages from the queue"""
        while self.is_running:
            try:
                # Get message from agent client queue
                message = await self.agent_client.get_message()
                if message:
                    await self._handle_message_content(message)
                
                # Also process internal queue messages
                try:
                    internal_message = await asyncio.wait_for(
                        self.message_queue.get(), 
                        timeout=0.1
                    )
                    await self._handle_message_content(internal_message)
                except asyncio.TimeoutError:
                    continue
                    
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
                await asyncio.sleep(1)
    
    async def _handle_message_content(self, message: AgentMessage) -> None:
        """Handle specific message content"""
        try:
            if message.message_type == "phase_update":
                await self._handle_phase_update(message.content)
            
            elif message.message_type == "implementation_status":
                await self._handle_implementation_status(message.content)
            
            elif message.message_type == "strategic_query":
                await self._handle_strategic_query(message.content)
            
            elif message.message_type == "risk_assessment":
                await self._handle_risk_assessment(message.content)
            
            elif message.message_type == "best_practice_query":
                await self._handle_best_practice_query(message.content)
            
            elif message.message_type == "project_context_update":
                await self._handle_project_context_update(message.content)
            
            else:
                self.logger.warning(f"Unknown message type: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling message content: {e}")
    
    async def _handle_phase_update(self, content: Dict[str, Any]) -> None:
        """Handle project phase update"""
        new_phase = content.get("phase")
        if new_phase in self.project_phases:
            old_phase = self.current_phase
            self.current_phase = new_phase
            
            # Update project context
            self.project_context["current_phase"] = new_phase
            self.project_context["phase_start_time"] = datetime.now().isoformat()
            self.project_context["phase_transitions"] = self.project_context.get("phase_transitions", [])
            self.project_context["phase_transitions"].append({
                "from_phase": old_phase,
                "to_phase": new_phase,
                "timestamp": datetime.now().isoformat()
            })
            
            # Provide guidance for new phase
            guidance = await self._generate_phase_guidance(new_phase)
            
            # Send guidance to ImplementAI
            response_message = AgentMessage(
                sender="guide_ai",
                recipient="implement_ai",
                message_type="phase_guidance",
                content={
                    "phase": new_phase,
                    "guidance": guidance,
                    "success_criteria": self.project_phases[new_phase].success_criteria,
                    "key_activities": self.project_phases[new_phase].key_activities
                }
            )
            
            # Send through communication system
            await self.agent_client.send_message(response_message)
            
            self.logger.info(f"Phase transition: {old_phase} -> {new_phase}")
            self.logger.info(f"Guidance provided for {new_phase} phase")
    
    async def _handle_implementation_status(self, content: Dict[str, Any]) -> None:
        """Handle implementation status updates"""
        status = content.get("status", {})
        progress = content.get("progress", 0)
        challenges = content.get("challenges", [])
        
        # Store implementation feedback
        self.implementation_feedback.append({
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "progress": progress,
            "challenges": challenges
        })
        
        # Analyze and provide guidance
        if challenges:
            guidance = await self._analyze_challenges(challenges)
            self.logger.info(f"Providing guidance for {len(challenges)} challenges")
    
    async def _handle_strategic_query(self, content: Dict[str, Any]) -> None:
        """Handle strategic queries"""
        query_type = content.get("query_type")
        query_details = content.get("details", {})
        
        if query_type == "architecture_recommendation":
            response = await self._provide_architecture_recommendation(query_details)
        elif query_type == "technology_stack":
            response = await self._provide_technology_stack_advice(query_details)
        elif query_type == "scaling_strategy":
            response = await self._provide_scaling_strategy(query_details)
        else:
            response = {"error": f"Unknown query type: {query_type}"}
        
        self.logger.info(f"Strategic query handled: {query_type}")
    
    async def _handle_risk_assessment(self, content: Dict[str, Any]) -> None:
        """Handle risk assessment requests"""
        project_type = content.get("project_type")
        complexity = content.get("complexity", "medium")
        
        assessment = await self._perform_risk_assessment(project_type, complexity)
        self.risk_assessments[project_type] = assessment
        
        self.logger.info(f"Risk assessment completed for {project_type}")
    
    async def _handle_best_practice_query(self, content: Dict[str, Any]) -> None:
        """Handle best practice queries"""
        practice_area = content.get("practice_area")
        
        if practice_area in self.best_practices:
            practices = self.best_practices[practice_area]
            self.logger.info(f"Best practices provided for {practice_area}")
        else:
            practices = {"error": f"No best practices found for {practice_area}"}
    
    async def _handle_project_context_update(self, content: Dict[str, Any]) -> None:
        """Handle project context updates"""
        context_updates = content.get("updates", {})
        
        # Update project context
        for key, value in context_updates.items():
            self.project_context[key] = value
        
        self.logger.info("Project context updated")
    
    async def _monitor_project_progress(self) -> None:
        """Monitor project progress and provide proactive guidance"""
        while self.is_running:
            try:
                # Analyze current progress
                progress_analysis = await self._analyze_project_progress()
                
                # Check if guidance is needed
                if progress_analysis.get("needs_guidance", False):
                    guidance = await self._generate_progress_guidance(progress_analysis)
                    self.logger.info("Proactive guidance provided based on progress analysis")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error monitoring project progress: {e}")
                await asyncio.sleep(60)
    
    async def _provide_strategic_guidance(self) -> None:
        """Provide strategic guidance at regular intervals"""
        while self.is_running:
            try:
                # Generate strategic insights
                insights = await self._generate_strategic_insights()
                
                if insights:
                    self.logger.info(f"Generated {len(insights)} strategic insights")
                
                await asyncio.sleep(600)  # Every 10 minutes
                
            except Exception as e:
                self.logger.error(f"Error providing strategic guidance: {e}")
                await asyncio.sleep(120)
    
    async def _analyze_implementation_feedback(self) -> None:
        """Analyze implementation feedback and adjust guidance"""
        while self.is_running:
            try:
                if self.implementation_feedback:
                    # Analyze recent feedback
                    recent_feedback = self.implementation_feedback[-10:]  # Last 10 entries
                    analysis = await self._analyze_feedback_patterns(recent_feedback)
                    
                    if analysis.get("needs_adjustment", False):
                        await self._adjust_guidance_strategy(analysis)
                        self.logger.info("Guidance strategy adjusted based on feedback")
                
                await asyncio.sleep(180)  # Every 3 minutes
                
            except Exception as e:
                self.logger.error(f"Error analyzing implementation feedback: {e}")
                await asyncio.sleep(60)
    
    async def _generate_phase_guidance(self, phase: str) -> Dict[str, Any]:
        """Generate guidance for a specific project phase"""
        phase_info = self.project_phases[phase]
        
        guidance = {
            "phase_overview": phase_info.description,
            "key_focus_areas": phase_info.key_activities,
            "success_criteria": phase_info.success_criteria,
            "estimated_duration": phase_info.estimated_duration,
            "strategic_recommendations": await self._get_phase_recommendations(phase),
            "common_pitfalls": await self._get_phase_pitfalls(phase),
            "metrics_to_track": await self._get_phase_metrics(phase)
        }
        
        return guidance
    
    async def _get_phase_recommendations(self, phase: str) -> List[str]:
        """Get recommendations for a specific phase"""
        recommendations = {
            "planning": [
                "Involve all stakeholders in requirements gathering",
                "Create detailed user stories and acceptance criteria",
                "Consider scalability and maintenance requirements",
                "Plan for contingencies and risk mitigation",
                "Establish clear communication channels"
            ],
            "development": [
                "Follow coding standards and best practices",
                "Implement automated testing from the start",
                "Conduct regular code reviews",
                "Use version control effectively",
                "Document code and architecture decisions"
            ],
            "testing": [
                "Test early and test often",
                "Use both manual and automated testing",
                "Test for edge cases and error conditions",
                "Performance test under realistic conditions",
                "Security test thoroughly"
            ],
            "deployment": [
                "Use automated deployment pipelines",
                "Test deployment process in staging first",
                "Have rollback procedures ready",
                "Monitor deployment closely",
                "Document deployment process"
            ],
            "maintenance": [
                "Monitor system performance and health",
                "Respond quickly to issues",
                "Plan for regular updates and improvements",
                "Keep documentation current",
                "Gather and act on user feedback"
            ]
        }
        
        return recommendations.get(phase, [])
    
    async def _get_phase_pitfalls(self, phase: str) -> List[str]:
        """Get common pitfalls for a specific phase"""
        pitfalls = {
            "planning": [
                "Insufficient requirements gathering",
                "Underestimating complexity",
                "Not considering all stakeholders",
                "Lack of risk assessment",
                "Poor timeline estimation"
            ],
            "development": [
                "Technical debt accumulation",
                "Insufficient testing",
                "Poor code quality",
                "Lack of documentation",
                "Not following best practices"
            ],
            "testing": [
                "Insufficient test coverage",
                "Not testing edge cases",
                "Performance issues not caught",
                "Security vulnerabilities missed",
                "User acceptance not properly tested"
            ],
            "deployment": [
                "Insufficient testing in production-like environment",
                "Poor deployment planning",
                "Lack of monitoring",
                "No rollback procedures",
                "Insufficient communication"
            ],
            "maintenance": [
                "Ignoring performance issues",
                "Not addressing technical debt",
                "Poor monitoring",
                "Insufficient documentation",
                "Not planning for future growth"
            ]
        }
        
        return pitfalls.get(phase, [])
    
    async def _get_phase_metrics(self, phase: str) -> List[str]:
        """Get key metrics to track for a specific phase"""
        metrics = {
            "planning": [
                "Requirements completeness",
                "Stakeholder satisfaction",
                "Architecture review approval",
                "Timeline accuracy",
                "Resource allocation efficiency"
            ],
            "development": [
                "Code quality metrics",
                "Test coverage percentage",
                "Development velocity",
                "Bug density",
                "Code review turnaround time"
            ],
            "testing": [
                "Test pass rate",
                "Defect density",
                "Test coverage",
                "Performance metrics",
                "Security test results"
            ],
            "deployment": [
                "Deployment success rate",
                "Deployment time",
                "Rollback frequency",
                "System availability",
                "Error rates"
            ],
            "maintenance": [
                "System uptime",
                "Mean time to resolution",
                "User satisfaction",
                "Performance metrics",
                "Cost efficiency"
            ]
        }
        
        return metrics.get(phase, [])
    
    async def _analyze_project_progress(self) -> Dict[str, Any]:
        """Analyze current project progress"""
        # This would analyze various metrics and implementation feedback
        # to determine if guidance is needed
        
        current_phase = self.project_context.get("current_phase", "planning")
        phase_start_time = self.project_context.get("phase_start_time")
        
        # Calculate phase duration
        if phase_start_time:
            start_time = datetime.fromisoformat(phase_start_time)
            duration = (datetime.now() - start_time).total_seconds()
            estimated_duration = self.project_phases[current_phase].estimated_duration
            
            # Simple heuristic for determining if guidance is needed
            needs_guidance = (
                len(self.implementation_feedback) > 0 and
                any(feedback.get("challenges") for feedback in self.implementation_feedback[-5:])
            )
        else:
            needs_guidance = True
        
        return {
            "current_phase": current_phase,
            "phase_duration": duration if phase_start_time else 0,
            "feedback_count": len(self.implementation_feedback),
            "recent_challenges": len([f for f in self.implementation_feedback[-5:] if f.get("challenges")]),
            "needs_guidance": needs_guidance
        }
    
    async def _generate_progress_guidance(self, progress_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate guidance based on progress analysis"""
        guidance = {
            "timestamp": datetime.now().isoformat(),
            "analysis": progress_analysis,
            "recommendations": [],
            "priority_actions": []
        }
        
        # Generate specific recommendations based on analysis
        if progress_analysis.get("recent_challenges", 0) > 2:
            guidance["recommendations"].append("Focus on addressing recent implementation challenges")
            guidance["priority_actions"].append("Schedule a review of current implementation approach")
        
        if progress_analysis.get("feedback_count", 0) > 20:
            guidance["recommendations"].append("Consider optimizing development process based on feedback patterns")
        
        return guidance
    
    async def _generate_strategic_insights(self) -> List[Dict[str, Any]]:
        """Generate strategic insights based on project data"""
        insights = []
        
        # Analyze phase transitions
        phase_transitions = self.project_context.get("phase_transitions", [])
        if len(phase_transitions) > 1:
            # Analyze transition patterns
            insights.append({
                "type": "pattern_analysis",
                "insight": "Project is following expected phase progression",
                "confidence": 0.8
            })
        
        # Analyze implementation feedback patterns
        if self.implementation_feedback:
            challenge_count = sum(len(f.get("challenges", [])) for f in self.implementation_feedback)
            if challenge_count > 10:
                insights.append({
                    "type": "risk_alert",
                    "insight": "High number of implementation challenges detected",
                    "confidence": 0.9,
                    "recommendation": "Consider reviewing development approach"
                })
        
        return insights
    
    async def _analyze_feedback_patterns(self, feedback: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in implementation feedback"""
        if not feedback:
            return {"needs_adjustment": False}
        
        # Extract challenges from feedback
        all_challenges = []
        for feedback_item in feedback:
            challenges = feedback_item.get("challenges", [])
            all_challenges.extend(challenges)
        
        # Analyze challenge patterns
        challenge_categories = {}
        for challenge in all_challenges:
            if isinstance(challenge, str):
                category = self._categorize_challenge(challenge)
                challenge_categories[category] = challenge_categories.get(category, 0) + 1
        
        # Determine if adjustment is needed
        needs_adjustment = any(count > 2 for count in challenge_categories.values())
        
        return {
            "needs_adjustment": needs_adjustment,
            "challenge_categories": challenge_categories,
            "total_challenges": len(all_challenges)
        }
    
    def _categorize_challenge(self, challenge: str) -> str:
        """Categorize a challenge into a type"""
        challenge_lower = challenge.lower()
        
        if any(keyword in challenge_lower for keyword in ["performance", "slow", "fast", "speed"]):
            return "performance"
        elif any(keyword in challenge_lower for keyword in ["security", "auth", "vulnerability"]):
            return "security"
        elif any(keyword in challenge_lower for keyword in ["test", "testing", "bug"]):
            return "testing"
        elif any(keyword in challenge_lower for keyword in ["architecture", "design", "structure"]):
            return "architecture"
        elif any(keyword in challenge_lower for keyword in ["dependency", "library", "package"]):
            return "dependencies"
        else:
            return "general"
    
    async def _adjust_guidance_strategy(self, analysis: Dict[str, Any]) -> None:
        """Adjust guidance strategy based on feedback analysis"""
        challenge_categories = analysis.get("challenge_categories", {})
        
        # Log the adjustment
        self.logger.info(f"Adjusting guidance strategy based on challenge categories: {challenge_categories}")
        
        # This would implement specific adjustments to the guidance strategy
        # For example, if there are many performance challenges, focus more on performance guidance
    
    async def _analyze_challenges(self, challenges: List[str]) -> Dict[str, Any]:
        """Analyze implementation challenges and provide guidance"""
        challenge_analysis = {
            "total_challenges": len(challenges),
            "categories": {},
            "recommendations": []
        }
        
        # Categorize challenges
        for challenge in challenges:
            category = self._categorize_challenge(challenge)
            challenge_analysis["categories"][category] = challenge_analysis["categories"].get(category, 0) + 1
        
        # Generate recommendations based on categories
        for category, count in challenge_analysis["categories"].items():
            if count > 1:
                recommendation = await self._get_category_recommendation(category)
                challenge_analysis["recommendations"].append(recommendation)
        
        return challenge_analysis
    
    async def _get_category_recommendation(self, category: str) -> str:
        """Get recommendation for a specific challenge category"""
        recommendations = {
            "performance": "Focus on performance optimization techniques and profiling",
            "security": "Implement security best practices and conduct security audits",
            "testing": "Increase test coverage and implement comprehensive testing strategies",
            "architecture": "Review and refactor architecture for better scalability and maintainability",
            "dependencies": "Audit and optimize dependencies, consider alternatives",
            "general": "Review development process and consider pair programming or code reviews"
        }
        
        return recommendations.get(category, "Review development approach and consider best practices")
    
    async def _provide_architecture_recommendation(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Provide architecture recommendations"""
        project_type = details.get("project_type", "web_application")
        scale = details.get("scale", "medium")
        
        if project_type in self.strategic_patterns:
            pattern = self.strategic_patterns[project_type]
            return {
                "project_type": project_type,
                "scale": scale,
                "architecture": pattern["architecture"],
                "key_focus": pattern["key_focus"],
                "common_challenges": pattern["common_challenges"],
                "recommended_tools": pattern["recommended_tools"]
            }
        else:
            return {"error": f"No strategic pattern found for {project_type}"}
    
    async def _provide_technology_stack_advice(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Provide technology stack advice"""
        project_type = details.get("project_type")
        requirements = details.get("requirements", [])
        
        # This would provide specific technology recommendations based on project type and requirements
        return {
            "project_type": project_type,
            "requirements": requirements,
            "recommendations": [
                "Choose technologies based on team expertise",
                "Consider long-term maintenance",
                "Evaluate community support and documentation",
                "Assess scalability requirements",
                "Consider integration capabilities"
            ]
        }
    
    async def _provide_scaling_strategy(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Provide scaling strategy recommendations"""
        current_scale = details.get("current_scale", "small")
        target_scale = details.get("target_scale", "large")
        
        return {
            "current_scale": current_scale,
            "target_scale": target_scale,
            "strategies": [
                "Implement horizontal scaling",
                "Use load balancing",
                "Optimize database performance",
                "Implement caching strategies",
                "Consider microservices architecture"
            ]
        }
    
    async def _perform_risk_assessment(self, project_type: str, complexity: str) -> Dict[str, Any]:
        """Perform risk assessment for a project"""
        risk_factors = {
            "web_application": ["Security vulnerabilities", "Performance issues", "Cross-browser compatibility"],
            "api_service": ["Rate limiting", "Authentication issues", "Version conflicts"],
            "data_pipeline": ["Data consistency", "Performance bottlenecks", "Data loss"],
            "machine_learning": ["Model drift", "Performance degradation", "Reproducibility issues"]
        }
        
        complexity_multiplier = {
            "low": 1.0,
            "medium": 1.5,
            "high": 2.0
        }
        
        risks = risk_factors.get(project_type, ["General development risks"])
        multiplier = complexity_multiplier.get(complexity, 1.5)
        
        return {
            "project_type": project_type,
            "complexity": complexity,
            "risk_factors": risks,
            "risk_level": "High" if multiplier > 1.5 else "Medium" if multiplier > 1.0 else "Low",
            "mitigation_strategies": [
                "Implement comprehensive testing",
                "Use monitoring and alerting",
                "Have contingency plans",
                "Regular code reviews",
                "Documentation and knowledge sharing"
            ]
        }
    
    async def _save_guidance_history(self) -> None:
        """Save guidance history to file"""
        try:
            filename = f"guidance_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            history_data = {
                "project_context": self.project_context,
                "guidance_sessions": self.guidance_history,
                "implementation_feedback": self.implementation_feedback,
                "risk_assessments": self.risk_assessments,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(filename, 'w') as f:
                json.dump(history_data, f, indent=2)
            
            self.logger.info(f"Guidance history saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving guidance history: {e}")
    
    async def get_project_summary(self) -> Dict[str, Any]:
        """Get a comprehensive project summary"""
        return {
            "current_phase": self.current_phase,
            "project_context": self.project_context,
            "phase_info": self.project_phases[self.current_phase].__dict__,
            "total_guidance_sessions": len(self.guidance_history),
            "total_implementation_feedback": len(self.implementation_feedback),
            "risk_assessments": len(self.risk_assessments),
            "project_health": await self._assess_project_health()
        }
    
    async def _assess_project_health(self) -> Dict[str, Any]:
        """Assess overall project health"""
        # Analyze various factors to determine project health
        feedback_score = self._calculate_feedback_score()
        phase_progress = self._calculate_phase_progress()
        risk_level = self._calculate_risk_level()
        
        overall_health = (feedback_score + phase_progress + (100 - risk_level)) / 3
        
        return {
            "overall_score": round(overall_health, 2),
            "feedback_score": feedback_score,
            "phase_progress": phase_progress,
            "risk_level": risk_level,
            "status": "healthy" if overall_health > 80 else "warning" if overall_health > 60 else "critical"
        }
    
    def _calculate_feedback_score(self) -> float:
        """Calculate score based on implementation feedback"""
        if not self.implementation_feedback:
            return 100.0
        
        # Simple scoring based on challenge frequency
        total_challenges = sum(len(f.get("challenges", [])) for f in self.implementation_feedback)
        challenge_ratio = total_challenges / len(self.implementation_feedback)
        
        return max(0, 100 - (challenge_ratio * 20))
    
    def _calculate_phase_progress(self) -> float:
        """Calculate phase progress score"""
        # This would be more sophisticated in practice
        return 75.0  # Placeholder
    
    def _calculate_risk_level(self) -> float:
        """Calculate risk level score"""
        # Simple risk calculation based on risk assessments
        if not self.risk_assessments:
            return 25.0
        
        total_risk = sum(1 for assessment in self.risk_assessments.values() 
                        if assessment.get("risk_level") == "High")
        
        return min(100, total_risk * 25)