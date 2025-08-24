"""
ImplementAI Agent - Handles implementation tasks and executes development activities
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
import subprocess
from pathlib import Path

from ..config.settings import get_settings
from ..agents.message_types import AgentMessage
from ..modules.file_operations import FileOperations
from ..modules.terminal_operations import TerminalOperations
from ..modules.task_manager import TaskManager
from ..utils.performance_monitor import PerformanceMonitor
from ..agents.agent_client import AgentClient


@dataclass
class ImplementationTask:
    """Represents an implementation task"""
    id: str
    name: str
    description: str
    task_type: str
    priority: str = "medium"
    status: str = "pending"
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: str = "1 hour"
    actual_duration: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImplementationResult:
    """Represents the result of an implementation task"""
    task_id: str
    success: bool
    output: Any
    error_message: Optional[str] = None
    execution_time: float = 0.0
    resources_used: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)


class ImplementAI:
    """ImplementAI Agent - Handles implementation and execution tasks"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Implementation modules
        self.file_ops = FileOperations()
        self.terminal_ops = TerminalOperations()
        self.task_manager = TaskManager(max_concurrent_tasks=self.settings.max_concurrent_tasks)
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()
        
        # Communication client
        self.agent_client = AgentClient("implement_ai")
        
        # Task management
        self.pending_tasks: List[ImplementationTask] = []
        self.active_tasks: Dict[str, ImplementationTask] = {}
        self.completed_tasks: List[ImplementationTask] = []
        self.task_queue = asyncio.Queue()
        
        # Communication
        self.message_queue = asyncio.Queue()
        self.is_running = False
        
        # Implementation context
        self.implementation_context = {
            "current_phase": "planning",
            "workspace_dir": self.settings.workspace_dir,
            "environment_setup": False,
            "active_projects": {},
            "implementation_history": []
        }
        
        # Implementation capabilities
        self.capabilities = self._initialize_capabilities()
        self.execution_strategies = self._initialize_execution_strategies()
        
    def _initialize_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Initialize implementation capabilities"""
        return {
            "file_operations": {
                "description": "File and directory operations",
                "operations": ["create", "read", "update", "delete", "copy", "move"],
                "supported_types": ["text", "json", "yaml", "xml", "binary"]
            },
            "code_generation": {
                "description": "Code generation and modification",
                "languages": ["python", "javascript", "typescript", "java", "go", "rust"],
                "frameworks": ["react", "vue", "angular", "django", "flask", "fastapi"]
            },
            "terminal_execution": {
                "description": "Terminal command execution",
                "command_types": ["system", "package_manager", "build_tools", "testing"],
                "environments": ["linux", "windows", "macos"]
            },
            "testing": {
                "description": "Test execution and management",
                "test_types": ["unit", "integration", "functional", "performance"],
                "frameworks": ["pytest", "jest", "mocha", "junit"]
            },
            "build_deployment": {
                "description": "Build and deployment operations",
                "build_tools": ["docker", "kubernetes", "webpack", "gradle", "maven"],
                "deployment_strategies": ["blue_green", "rolling", "canary"]
            }
        }
    
    def _initialize_execution_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize execution strategies for different task types"""
        return {
            "sequential": {
                "description": "Execute tasks sequentially",
                "use_case": "Tasks with dependencies",
                "advantages": ["Predictable", "Easy to debug", "Resource efficient"],
                "disadvantages": ["Slower for independent tasks"]
            },
            "parallel": {
                "description": "Execute tasks in parallel",
                "use_case": "Independent tasks",
                "advantages": ["Faster execution", "Better resource utilization"],
                "disadvantages": ["Complex debugging", "Resource contention"]
            },
            "adaptive": {
                "description": "Adaptive execution based on resources",
                "use_case": "Mixed task types",
                "advantages": ["Optimized performance", "Resource aware"],
                "disadvantages": ["Complex implementation"]
            }
        }
    
    async def initialize(self) -> None:
        """Initialize the ImplementAI agent"""
        self.logger.info("Initializing ImplementAI Agent...")
        
        # Initialize performance monitor
        await self.performance_monitor.initialize()
        
        # Initialize modules
        await self.file_ops.initialize()
        await self.terminal_ops.initialize()
        await self.task_manager.initialize()
        
        # Connect to communication agent
        if not await self.agent_client.connect():
            self.logger.error("Failed to connect to CommunicationAgent")
            return
        
        # Register message handlers
        await self.agent_client.register_message_handler("implementation_request", self._handle_implementation_request)
        await self.agent_client.register_message_handler("task_assignment", self._handle_task_assignment)
        await self.agent_client.register_message_handler("phase_guidance", self._handle_phase_guidance)
        await self.agent_client.register_message_handler("execution_command", self._handle_execution_command)
        await self.agent_client.register_message_handler("status_query", self._handle_status_query)
        await self.agent_client.register_message_handler("optimization_request", self._handle_optimization_request)
        await self.agent_client.register_message_handler("environment_setup", self._handle_environment_setup)
        
        # Create workspace directory
        os.makedirs(self.settings.workspace_dir, exist_ok=True)
        
        # Set up implementation environment
        await self._setup_implementation_environment()
        
        self.logger.info("ImplementAI Agent initialized successfully")
    
    async def start(self) -> None:
        """Start the ImplementAI agent"""
        if self.is_running:
            self.logger.warning("ImplementAI Agent is already running")
            return
            
        self.logger.info("Starting ImplementAI Agent...")
        self.is_running = True
        
        # Start message listener
        message_listener_task = asyncio.create_task(self.agent_client.start_message_listener())
        
        # Start background tasks
        tasks = [
            message_listener_task,
            asyncio.create_task(self._process_messages()),
            asyncio.create_task(self._execute_tasks()),
            asyncio.create_task(self._monitor_implementation()),
            asyncio.create_task(self._report_progress()),
            asyncio.create_task(self._optimize_execution())
        ]
        
        self.logger.info("ImplementAI Agent started successfully")
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            self.logger.info("Shutting down ImplementAI Agent...")
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the ImplementAI Agent"""
        self.logger.info("Stopping ImplementAI Agent...")
        self.is_running = False
        
        # Save implementation history
        await self._save_implementation_history()
        
        # Stop modules
        await self.file_ops.stop()
        await self.terminal_ops.stop()
        await self.task_manager.stop()
        await self.performance_monitor.stop_monitoring()
        
        # Stop agent client
        await self.agent_client.stop()
        
        self.logger.info("ImplementAI Agent stopped")
    
    async def handle_message(self, message: AgentMessage) -> None:
        """Handle incoming messages"""
        self.logger.info(f"ImplementAI received message from {message.sender}: {message.message_type}")
        
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
            if message.message_type == "implementation_request":
                await self._handle_implementation_request(message.content)
            
            elif message.message_type == "task_assignment":
                await self._handle_task_assignment(message.content)
            
            elif message.message_type == "phase_guidance":
                await self._handle_phase_guidance(message.content)
            
            elif message.message_type == "execution_command":
                await self._handle_execution_command(message.content)
            
            elif message.message_type == "status_query":
                await self._handle_status_query(message.content)
            
            elif message.message_type == "optimization_request":
                await self._handle_optimization_request(message.content)
            
            elif message.message_type == "environment_setup":
                await self._handle_environment_setup(message.content)
            
            else:
                self.logger.warning(f"Unknown message type: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling message content: {e}")
    
    async def _handle_implementation_request(self, content: Dict[str, Any]) -> None:
        """Handle implementation requests"""
        request_type = content.get("request_type")
        request_details = content.get("details", {})
        
        # Create implementation task
        task = ImplementationTask(
            id=f"task_{len(self.pending_tasks) + 1}",
            name=f"Implementation: {request_type}",
            description=f"Execute implementation request: {request_type}",
            task_type=request_type,
            metadata={"request_details": request_details}
        )
        
        self.pending_tasks.append(task)
        await self.task_queue.put(task)
        
        self.logger.info(f"Implementation request queued: {request_type}")
    
    async def _handle_task_assignment(self, content: Dict[str, Any]) -> None:
        """Handle task assignments"""
        task_data = content.get("task", {})
        
        task = ImplementationTask(
            id=task_data.get("id", f"assigned_{len(self.pending_tasks) + 1}"),
            name=task_data.get("name", "Assigned Task"),
            description=task_data.get("description", "Task assigned by GuideAI"),
            task_type=task_data.get("task_type", "general"),
            priority=task_data.get("priority", "medium"),
            dependencies=task_data.get("dependencies", []),
            estimated_duration=task_data.get("estimated_duration", "1 hour"),
            metadata=task_data.get("metadata", {})
        )
        
        self.pending_tasks.append(task)
        await self.task_queue.put(task)
        
        self.logger.info(f"Task assigned: {task.name}")
    
    async def _handle_phase_guidance(self, content: Dict[str, Any]) -> None:
        """Handle phase guidance from GuideAI"""
        phase = content.get("phase")
        guidance = content.get("guidance", {})
        success_criteria = content.get("success_criteria", [])
        key_activities = content.get("key_activities", [])
        
        # Update implementation context
        self.implementation_context["current_phase"] = phase
        self.implementation_context["phase_guidance"] = guidance
        self.implementation_context["success_criteria"] = success_criteria
        self.implementation_context["key_activities"] = key_activities
        
        # Create phase-specific tasks
        phase_tasks = await self._create_phase_tasks(phase, key_activities)
        for task in phase_tasks:
            self.pending_tasks.append(task)
            await self.task_queue.put(task)
        
        self.logger.info(f"Phase guidance received for {phase} phase")
        self.logger.info(f"Created {len(phase_tasks)} phase-specific tasks")
    
    async def _handle_execution_command(self, content: Dict[str, Any]) -> None:
        """Handle direct execution commands"""
        command = content.get("command")
        command_type = content.get("command_type", "terminal")
        parameters = content.get("parameters", {})
        
        # Create immediate execution task
        task = ImplementationTask(
            id=f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=f"Execute: {command}",
            description=f"Direct execution command: {command}",
            task_type="execution",
            priority="high",
            metadata={
                "command": command,
                "command_type": command_type,
                "parameters": parameters
            }
        )
        
        self.pending_tasks.append(task)
        await self.task_queue.put(task)
        
        self.logger.info(f"Execution command queued: {command}")
    
    async def _handle_status_query(self, content: Dict[str, Any]) -> None:
        """Handle status queries"""
        query_type = content.get("query_type")
        sender = content.get("sender", "unknown")
        
        if query_type == "overall_status":
            status = await self._get_overall_status()
        elif query_type == "task_status":
            task_id = content.get("task_id")
            status = await self._get_task_status(task_id)
        elif query_type == "phase_status":
            status = await self._get_phase_status()
        else:
            status = {"error": f"Unknown query type: {query_type}"}
        
        # Send status response through communication system
        response_message = AgentMessage(
            sender="implement_ai",
            recipient=sender,
            message_type="status_response",
            content={
                "query_type": query_type,
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        await self.agent_client.send_message(response_message)
        self.logger.info(f"Status query handled: {query_type}")
    
    async def _handle_optimization_request(self, content: Dict[str, Any]) -> None:
        """Handle optimization requests"""
        optimization_type = content.get("optimization_type")
        parameters = content.get("parameters", {})
        
        # Create optimization task
        task = ImplementationTask(
            id=f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=f"Optimize: {optimization_type}",
            description=f"Optimization task: {optimization_type}",
            task_type="optimization",
            priority="medium",
            metadata={
                "optimization_type": optimization_type,
                "parameters": parameters
            }
        )
        
        self.pending_tasks.append(task)
        await self.task_queue.put(task)
        
        self.logger.info(f"Optimization request queued: {optimization_type}")
    
    async def _handle_environment_setup(self, content: Dict[str, Any]) -> None:
        """Handle environment setup requests"""
        environment_type = content.get("environment_type")
        setup_config = content.get("config", {})
        
        # Create environment setup task
        task = ImplementationTask(
            id=f"env_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=f"Setup Environment: {environment_type}",
            description=f"Environment setup: {environment_type}",
            task_type="environment_setup",
            priority="high",
            metadata={
                "environment_type": environment_type,
                "config": setup_config
            }
        )
        
        self.pending_tasks.append(task)
        await self.task_queue.put(task)
        
        self.logger.info(f"Environment setup queued: {environment_type}")
    
    async def _execute_tasks(self) -> None:
        """Execute tasks from the queue"""
        while self.is_running:
            try:
                # Get task from queue
                task = await asyncio.wait_for(
                    self.task_queue.get(), 
                    timeout=1.0
                )
                
                # Check if task can be executed (dependencies met)
                if await self._can_execute_task(task):
                    await self._execute_task(task)
                else:
                    # Re-queue task for later
                    await asyncio.sleep(5)
                    await self.task_queue.put(task)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error executing task: {e}")
    
    async def _can_execute_task(self, task: ImplementationTask) -> bool:
        """Check if a task can be executed (dependencies met)"""
        if not task.dependencies:
            return True
        
        # Check if all dependencies are completed
        for dep_id in task.dependencies:
            dep_completed = any(
                completed_task.id == dep_id and completed_task.status == "completed"
                for completed_task in self.completed_tasks
            )
            if not dep_completed:
                return False
        
        return True
    
    async def _execute_task(self, task: ImplementationTask) -> None:
        """Execute a specific task"""
        self.logger.info(f"Executing task: {task.name}")
        
        # Update task status
        task.status = "running"
        task.started_at = datetime.now()
        self.active_tasks[task.id] = task
        
        try:
            # Execute based on task type
            result = await self._execute_task_by_type(task)
            
            # Update task with result
            task.status = "completed"
            task.completed_at = datetime.now()
            task.result = result
            
            # Move to completed tasks
            self.completed_tasks.append(task)
            del self.active_tasks[task.id]
            
            self.logger.info(f"Task completed: {task.name}")
            
            # Report completion to GuideAI
            await self._report_task_completion(task, result)
            
        except Exception as e:
            # Handle task failure
            task.status = "failed"
            task.completed_at = datetime.now()
            task.result = {"error": str(e)}
            
            # Move to completed tasks
            self.completed_tasks.append(task)
            del self.active_tasks[task.id]
            
            self.logger.error(f"Task failed: {task.name} - {e}")
            
            # Report failure to GuideAI
            await self._report_task_failure(task, str(e))
    
    async def _execute_task_by_type(self, task: ImplementationTask) -> ImplementationResult:
        """Execute task based on its type"""
        start_time = datetime.now()
        
        try:
            if task.task_type == "file_operations":
                result = await self._execute_file_operations(task)
            
            elif task.task_type == "code_generation":
                result = await self._execute_code_generation(task)
            
            elif task.task_type == "terminal_execution":
                result = await self._execute_terminal_command(task)
            
            elif task.task_type == "testing":
                result = await self._execute_testing(task)
            
            elif task.task_type == "build_deployment":
                result = await self._execute_build_deployment(task)
            
            elif task.task_type == "execution":
                result = await self._execute_direct_command(task)
            
            elif task.task_type == "optimization":
                result = await self._execute_optimization(task)
            
            elif task.task_type == "environment_setup":
                result = await self._execute_environment_setup(task)
            
            else:
                result = await self._execute_general_task(task)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            
            return result
            
        except Exception as e:
            return ImplementationResult(
                task_id=task.id,
                success=False,
                output=None,
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def _execute_file_operations(self, task: ImplementationTask) -> ImplementationResult:
        """Execute file operations task"""
        metadata = task.metadata.get("request_details", {})
        operation = metadata.get("operation")
        file_path = metadata.get("file_path")
        content = metadata.get("content")
        
        if operation == "create":
            success = await self.file_ops.create_file(file_path, content)
            return ImplementationResult(
                task_id=task.id,
                success=success,
                output={"file_created": file_path},
                artifacts=[file_path]
            )
        
        elif operation == "read":
            file_content = await self.file_ops.read_file(file_path)
            return ImplementationResult(
                task_id=task.id,
                success=True,
                output={"file_content": file_content}
            )
        
        elif operation == "update":
            success = await self.file_ops.update_file(file_path, content)
            return ImplementationResult(
                task_id=task.id,
                success=success,
                output={"file_updated": file_path},
                artifacts=[file_path]
            )
        
        elif operation == "delete":
            success = await self.file_ops.delete_file(file_path)
            return ImplementationResult(
                task_id=task.id,
                success=success,
                output={"file_deleted": file_path}
            )
        
        else:
            raise ValueError(f"Unknown file operation: {operation}")
    
    async def _execute_code_generation(self, task: ImplementationTask) -> ImplementationResult:
        """Execute code generation task"""
        metadata = task.metadata.get("request_details", {})
        language = metadata.get("language", "python")
        framework = metadata.get("framework")
        code_spec = metadata.get("code_spec", {})
        
        # Generate code based on specifications
        generated_code = await self._generate_code(language, framework, code_spec)
        
        # Save generated code
        file_path = code_spec.get("output_file", f"generated_{task.id}.{language}")
        success = await self.file_ops.create_file(file_path, generated_code)
        
        return ImplementationResult(
            task_id=task.id,
            success=success,
            output={"code_generated": file_path, "language": language},
            artifacts=[file_path]
        )
    
    async def _execute_terminal_command(self, task: ImplementationTask) -> ImplementationResult:
        """Execute terminal command task"""
        metadata = task.metadata.get("request_details", {})
        command = metadata.get("command")
        working_dir = metadata.get("working_dir", self.settings.workspace_dir)
        timeout = metadata.get("timeout", 300)
        
        # Execute command
        result = await self.terminal_ops.execute_command(command, working_dir, timeout)
        
        return ImplementationResult(
            task_id=task.id,
            success=result.get("success", False),
            output=result,
            resources_used={"execution_time": result.get("execution_time", 0)}
        )
    
    async def _execute_testing(self, task: ImplementationTask) -> ImplementationResult:
        """Execute testing task"""
        metadata = task.metadata.get("request_details", {})
        test_type = metadata.get("test_type", "unit")
        test_path = metadata.get("test_path")
        framework = metadata.get("framework", "pytest")
        
        # Build test command
        if framework == "pytest":
            command = f"pytest {test_path} -v"
        elif framework == "jest":
            command = f"jest {test_path}"
        else:
            command = f"python -m pytest {test_path}"
        
        # Execute tests
        result = await self.terminal_ops.execute_command(command, self.settings.workspace_dir)
        
        return ImplementationResult(
            task_id=task.id,
            success=result.get("success", False),
            output=result,
            resources_used={"test_type": test_type, "framework": framework}
        )
    
    async def _execute_build_deployment(self, task: ImplementationTask) -> ImplementationResult:
        """Execute build and deployment task"""
        metadata = task.metadata.get("request_details", {})
        operation = metadata.get("operation", "build")
        build_tool = metadata.get("build_tool", "docker")
        config = metadata.get("config", {})
        
        if operation == "build":
            if build_tool == "docker":
                command = f"docker build -t {config.get('image_name', 'app')} ."
            else:
                command = f"{build_tool} build"
        
        elif operation == "deploy":
            if build_tool == "docker":
                command = f"docker run -d {config.get('image_name', 'app')}"
            else:
                command = f"{build_tool} deploy"
        
        else:
            raise ValueError(f"Unknown build/deployment operation: {operation}")
        
        # Execute command
        result = await self.terminal_ops.execute_command(command, self.settings.workspace_dir)
        
        return ImplementationResult(
            task_id=task.id,
            success=result.get("success", False),
            output=result,
            resources_used={"build_tool": build_tool, "operation": operation}
        )
    
    async def _execute_direct_command(self, task: ImplementationTask) -> ImplementationResult:
        """Execute direct command task"""
        metadata = task.metadata
        command = metadata.get("command")
        command_type = metadata.get("command_type", "terminal")
        parameters = metadata.get("parameters", {})
        
        if command_type == "terminal":
            result = await self.terminal_ops.execute_command(command, self.settings.workspace_dir)
        else:
            result = {"error": f"Unknown command type: {command_type}"}
        
        return ImplementationResult(
            task_id=task.id,
            success=result.get("success", False),
            output=result
        )
    
    async def _execute_optimization(self, task: ImplementationTask) -> ImplementationResult:
        """Execute optimization task"""
        metadata = task.metadata
        optimization_type = metadata.get("optimization_type")
        parameters = metadata.get("parameters", {})
        
        # Analyze current performance
        performance_data = await self.performance_monitor.get_current_metrics()
        
        # Generate optimization recommendations
        recommendations = await self._generate_optimization_recommendations(
            optimization_type, performance_data, parameters
        )
        
        # Apply optimizations
        optimization_results = []
        for recommendation in recommendations:
            result = await self._apply_optimization(recommendation)
            optimization_results.append(result)
        
        return ImplementationResult(
            task_id=task.id,
            success=True,
            output={
                "optimization_type": optimization_type,
                "recommendations": recommendations,
                "results": optimization_results
            }
        )
    
    async def _execute_environment_setup(self, task: ImplementationTask) -> ImplementationResult:
        """Execute environment setup task"""
        metadata = task.metadata
        environment_type = metadata.get("environment_type")
        config = metadata.get("config", {})
        
        setup_commands = await self._get_environment_setup_commands(environment_type, config)
        
        results = []
        for command in setup_commands:
            result = await self.terminal_ops.execute_command(command, self.settings.workspace_dir)
            results.append(result)
        
        success = all(r.get("success", False) for r in results)
        
        return ImplementationResult(
            task_id=task.id,
            success=success,
            output={"environment_type": environment_type, "setup_results": results}
        )
    
    async def _execute_general_task(self, task: ImplementationTask) -> ImplementationResult:
        """Execute general task"""
        # For general tasks, we'll execute the task's metadata as a command
        metadata = task.metadata
        command = metadata.get("command", "echo 'General task executed'")
        
        result = await self.terminal_ops.execute_command(command, self.settings.workspace_dir)
        
        return ImplementationResult(
            task_id=task.id,
            success=result.get("success", False),
            output=result
        )
    
    async def _generate_code(self, language: str, framework: str, code_spec: Dict[str, Any]) -> str:
        """Generate code based on specifications"""
        # This is a simplified code generation
        # In practice, this would use AI models or templates
        
        if language == "python":
            if framework == "fastapi":
                return '''
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None

@app.post("/items/")
async def create_item(item: Item):
    return {"item": item}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
'''
            else:
                return '''
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
'''
        
        elif language == "javascript":
            if framework == "react":
                return '''
import React from 'react';

function App() {
  return (
    <div className="App">
      <h1>Hello, World!</h1>
    </div>
  );
}

export default App;
'''
            else:
                return '''
console.log("Hello, World!");
'''
        
        else:
            return f"// Generated {language} code for {framework or 'general'}"
    
    async def _generate_optimization_recommendations(
        self, optimization_type: str, performance_data: Dict[str, Any], parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if optimization_type == "performance":
            # Analyze performance data and generate recommendations
            if performance_data.get("cpu_usage", 0) > 80:
                recommendations.append({
                    "type": "cpu_optimization",
                    "description": "High CPU usage detected",
                    "action": "Optimize algorithms and reduce computational complexity"
                })
            
            if performance_data.get("memory_usage", 0) > 80:
                recommendations.append({
                    "type": "memory_optimization",
                    "description": "High memory usage detected",
                    "action": "Implement memory pooling and optimize data structures"
                })
        
        elif optimization_type == "code_quality":
            recommendations.append({
                "type": "code_refactoring",
                "description": "Improve code quality",
                "action": "Refactor code for better readability and maintainability"
            })
        
        return recommendations
    
    async def _apply_optimization(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Apply optimization recommendation"""
        # This would implement the actual optimization
        return {
            "recommendation": recommendation,
            "applied": True,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_environment_setup_commands(self, environment_type: str, config: Dict[str, Any]) -> List[str]:
        """Get environment setup commands"""
        commands = []
        
        if environment_type == "python":
            commands.extend([
                "python -m venv venv",
                "source venv/bin/activate" if os.name != 'nt' else "venv\\Scripts\\activate",
                "pip install --upgrade pip"
            ])
            
            requirements = config.get("requirements", [])
            if requirements:
                commands.append(f"pip install {' '.join(requirements)}")
        
        elif environment_type == "node":
            commands.extend([
                "node --version",
                "npm --version",
                "npm install"
            ])
        
        elif environment_type == "docker":
            commands.extend([
                "docker --version",
                "docker-compose --version"
            ])
        
        return commands
    
    async def _create_phase_tasks(self, phase: str, key_activities: List[str]) -> List[ImplementationTask]:
        """Create tasks for a specific phase"""
        tasks = []
        
        for i, activity in enumerate(key_activities):
            task = ImplementationTask(
                id=f"{phase}_task_{i+1}",
                name=f"{phase.title()}: {activity}",
                description=f"Execute {activity} for {phase} phase",
                task_type="phase_activity",
                priority="medium",
                metadata={"phase": phase, "activity": activity}
            )
            tasks.append(task)
        
        return tasks
    
    async def _setup_implementation_environment(self) -> None:
        """Set up the implementation environment"""
        self.logger.info("Setting up implementation environment...")
        
        # Check if environment is already set up
        if self.implementation_context["environment_setup"]:
            return
        
        # Create necessary directories
        directories = [
            "projects",
            "temp",
            "logs",
            "artifacts"
        ]
        
        for directory in directories:
            dir_path = os.path.join(self.settings.workspace_dir, directory)
            os.makedirs(dir_path, exist_ok=True)
        
        # Initialize environment
        self.implementation_context["environment_setup"] = True
        
        self.logger.info("Implementation environment setup completed")
    
    async def _monitor_implementation(self) -> None:
        """Monitor implementation progress and performance"""
        while self.is_running:
            try:
                # Collect performance metrics
                metrics = await self.performance_monitor.get_current_metrics()
                
                # Check for performance issues
                if metrics.get("cpu_usage", 0) > 90:
                    self.logger.warning("High CPU usage detected")
                
                if metrics.get("memory_usage", 0) > 90:
                    self.logger.warning("High memory usage detected")
                
                # Monitor task execution
                active_count = len(self.active_tasks)
                if active_count > self.settings.max_concurrent_tasks:
                    self.logger.warning(f"Too many active tasks: {active_count}")
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                self.logger.error(f"Error monitoring implementation: {e}")
                await asyncio.sleep(30)
    
    async def _report_progress(self) -> None:
        """Report implementation progress to GuideAI"""
        while self.is_running:
            try:
                # Calculate progress metrics
                total_tasks = len(self.pending_tasks) + len(self.active_tasks) + len(self.completed_tasks)
                completed_tasks = len(self.completed_tasks)
                progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                
                # Collect challenges and issues
                challenges = []
                for task in self.completed_tasks:
                    if task.status == "failed":
                        challenges.append(f"Task failed: {task.name}")
                
                # Send progress report
                progress_report = {
                    "timestamp": datetime.now().isoformat(),
                    "progress": progress,
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "active_tasks": len(self.active_tasks),
                    "pending_tasks": len(self.pending_tasks),
                    "challenges": challenges,
                    "current_phase": self.implementation_context["current_phase"]
                }
                
                # This would be sent to GuideAI through the communication system
                self.logger.info(f"Progress report: {progress:.1f}% complete")
                
                await asyncio.sleep(300)  # Report every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error reporting progress: {e}")
                await asyncio.sleep(60)
    
    async def _optimize_execution(self) -> None:
        """Optimize task execution strategies"""
        while self.is_running:
            try:
                # Analyze execution patterns
                execution_stats = await self._analyze_execution_patterns()
                
                # Adjust execution strategies based on patterns
                if execution_stats.get("parallel_efficiency", 0) > 0.8:
                    # Use more parallel execution
                    self.logger.info("Optimizing for parallel execution")
                
                elif execution_stats.get("failure_rate", 0) > 0.2:
                    # Use more conservative execution
                    self.logger.info("Optimizing for reliability")
                
                await asyncio.sleep(600)  # Optimize every 10 minutes
                
            except Exception as e:
                self.logger.error(f"Error optimizing execution: {e}")
                await asyncio.sleep(120)
    
    async def _analyze_execution_patterns(self) -> Dict[str, Any]:
        """Analyze execution patterns for optimization"""
        if not self.completed_tasks:
            return {"parallel_efficiency": 0.5, "failure_rate": 0.0}
        
        # Calculate failure rate
        failed_tasks = [t for t in self.completed_tasks if t.status == "failed"]
        failure_rate = len(failed_tasks) / len(self.completed_tasks)
        
        # Calculate average execution time
        execution_times = [
            (t.completed_at - t.started_at).total_seconds()
            for t in self.completed_tasks
            if t.started_at and t.completed_at
        ]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            "failure_rate": failure_rate,
            "avg_execution_time": avg_execution_time,
            "parallel_efficiency": 0.7,  # Placeholder
            "total_tasks_executed": len(self.completed_tasks)
        }
    
    async def _report_task_completion(self, task: ImplementationTask, result: ImplementationResult) -> None:
        """Report task completion to GuideAI"""
        completion_report = {
            "task_id": task.id,
            "task_name": task.name,
            "status": "completed",
            "success": result.success,
            "execution_time": result.execution_time,
            "artifacts": result.artifacts,
            "timestamp": datetime.now().isoformat()
        }
        
        # This would be sent to GuideAI through the communication system
        self.logger.info(f"Task completion reported: {task.name}")
    
    async def _report_task_failure(self, task: ImplementationTask, error_message: str) -> None:
        """Report task failure to GuideAI"""
        failure_report = {
            "task_id": task.id,
            "task_name": task.name,
            "status": "failed",
            "error_message": error_message,
            "timestamp": datetime.now().isoformat()
        }
        
        # This would be sent to GuideAI through the communication system
        self.logger.error(f"Task failure reported: {task.name} - {error_message}")
    
    async def _save_implementation_history(self) -> None:
        """Save implementation history to file"""
        try:
            filename = f"implementation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            history_data = {
                "implementation_context": self.implementation_context,
                "completed_tasks": [
                    {
                        "id": task.id,
                        "name": task.name,
                        "status": task.status,
                        "task_type": task.task_type,
                        "created_at": task.created_at.isoformat(),
                        "started_at": task.started_at.isoformat() if task.started_at else None,
                        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                        "execution_time": (task.completed_at - task.started_at).total_seconds() if task.started_at and task.completed_at else None,
                        "result": task.result
                    }
                    for task in self.completed_tasks
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            with open(filename, 'w') as f:
                json.dump(history_data, f, indent=2)
            
            self.logger.info(f"Implementation history saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving implementation history: {e}")
    
    async def _get_overall_status(self) -> Dict[str, Any]:
        """Get overall implementation status"""
        total_tasks = len(self.pending_tasks) + len(self.active_tasks) + len(self.completed_tasks)
        completed_tasks = len(self.completed_tasks)
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "status": "active",
            "progress": progress,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "active_tasks": len(self.active_tasks),
            "pending_tasks": len(self.pending_tasks),
            "current_phase": self.implementation_context["current_phase"],
            "environment_setup": self.implementation_context["environment_setup"]
        }
    
    async def _get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a specific task"""
        # Check active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                "task_id": task_id,
                "status": task.status,
                "name": task.name,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "progress": "running"
            }
        
        # Check completed tasks
        for task in self.completed_tasks:
            if task.id == task_id:
                return {
                    "task_id": task_id,
                    "status": task.status,
                    "name": task.name,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "progress": "completed"
                }
        
        # Check pending tasks
        for task in self.pending_tasks:
            if task.id == task_id:
                return {
                    "task_id": task_id,
                    "status": task.status,
                    "name": task.name,
                    "created_at": task.created_at.isoformat(),
                    "progress": "pending"
                }
        
        return {"error": f"Task not found: {task_id}"}
    
    async def _get_phase_status(self) -> Dict[str, Any]:
        """Get current phase status"""
        phase_tasks = [
            task for task in self.completed_tasks
            if task.task_type == "phase_activity" and task.metadata.get("phase") == self.implementation_context["current_phase"]
        ]
        
        return {
            "current_phase": self.implementation_context["current_phase"],
            "phase_tasks_completed": len(phase_tasks),
            "phase_progress": len(phase_tasks) / len(self.implementation_context.get("key_activities", [])) * 100 if self.implementation_context.get("key_activities") else 0,
            "phase_start_time": self.implementation_context.get("phase_start_time")
        }
    
    async def get_implementation_summary(self) -> Dict[str, Any]:
        """Get comprehensive implementation summary"""
        total_tasks = len(self.pending_tasks) + len(self.active_tasks) + len(self.completed_tasks)
        completed_tasks = len(self.completed_tasks)
        
        # Calculate success rate
        successful_tasks = len([t for t in self.completed_tasks if t.status == "completed"])
        success_rate = (successful_tasks / completed_tasks * 100) if completed_tasks > 0 else 0
        
        # Calculate average execution time
        execution_times = [
            (t.completed_at - t.started_at).total_seconds()
            for t in self.completed_tasks
            if t.started_at and t.completed_at
        ]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "active_tasks": len(self.active_tasks),
            "pending_tasks": len(self.pending_tasks),
            "success_rate": success_rate,
            "average_execution_time": avg_execution_time,
            "current_phase": self.implementation_context["current_phase"],
            "environment_setup": self.implementation_context["environment_setup"],
            "capabilities": list(self.capabilities.keys()),
            "timestamp": datetime.now().isoformat()
        }