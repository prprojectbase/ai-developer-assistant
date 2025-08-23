import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json
import traceback

from ..config.settings import get_settings


class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(Enum):
    """Task priority enumeration"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """Task data structure"""
    id: str
    name: str
    description: str
    task_type: str
    parameters: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timeout: Optional[int] = None
    progress: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskManager:
    """Task manager for the AI Developer Assistant"""
    
    def __init__(self, max_concurrent_tasks: int = 5):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # Task storage
        self.tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # Task handlers
        self.task_handlers: Dict[str, Callable] = {}
        
        # Event loop and control
        self.event_loop = None
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        
        # Statistics
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0,
            "average_execution_time": 0.0
        }
    
    async def initialize(self) -> None:
        """Initialize the task manager"""
        self.logger.info("Initializing Task Manager...")
        
        # Get the current event loop
        self.event_loop = asyncio.get_event_loop()
        
        # Start worker tasks
        self.is_running = True
        for i in range(self.max_concurrent_tasks):
            worker_task = asyncio.create_task(self._worker(f"worker_{i}"))
            self.worker_tasks.append(worker_task)
        
        self.logger.info(f"Task Manager initialized with {self.max_concurrent_tasks} workers")
    
    async def stop(self) -> None:
        """Stop the task manager"""
        self.logger.info("Stopping Task Manager...")
        
        self.is_running = False
        
        # Cancel all running tasks
        for task_id, running_task in self.running_tasks.items():
            if not running_task.done():
                running_task.cancel()
                
                # Update task status
                if task_id in self.tasks:
                    self.tasks[task_id].status = TaskStatus.CANCELLED
                    self.tasks[task_id].completed_at = datetime.now()
        
        # Wait for worker tasks to finish
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        self.logger.info("Task Manager stopped")
    
    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task"""
        try:
            # Generate task ID if not provided
            task_id = task_data.get("id", str(uuid.uuid4()))
            
            # Create task object
            task = Task(
                id=task_id,
                name=task_data["name"],
                description=task_data.get("description", ""),
                task_type=task_data["type"],
                parameters=task_data.get("parameters", {}),
                priority=TaskPriority(task_data.get("priority", TaskPriority.MEDIUM.value)),
                timeout=task_data.get("timeout"),
                dependencies=task_data.get("dependencies", []),
                tags=task_data.get("tags", []),
                metadata=task_data.get("metadata", {})
            )
            
            # Store task
            self.tasks[task_id] = task
            
            # Add to queue
            await self.task_queue.put(task_id)
            
            # Update statistics
            self.stats["total_tasks"] += 1
            
            self.logger.info(f"Created task: {task_id} ({task.name})")
            
            return {
                "success": True,
                "task_id": task_id,
                "task": self._task_to_dict(task)
            }
            
        except Exception as e:
            self.logger.error(f"Error creating task: {e}")
            return {"error": str(e)}
    
    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get task information"""
        if task_id not in self.tasks:
            return {"error": f"Task not found: {task_id}"}
        
        task = self.tasks[task_id]
        return {
            "success": True,
            "task": self._task_to_dict(task)
        }
    
    async def get_task_status(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Get task status"""
        if task_id:
            if task_id not in self.tasks:
                return {"error": f"Task not found: {task_id}"}
            
            task = self.tasks[task_id]
            return {
                "success": True,
                "task_id": task_id,
                "status": task.status.value,
                "progress": task.progress,
                "result": task.result,
                "error": task.error
            }
        else:
            # Return status of all tasks
            tasks_status = {}
            for task_id, task in self.tasks.items():
                tasks_status[task_id] = {
                    "status": task.status.value,
                    "progress": task.progress,
                    "name": task.name,
                    "created_at": task.created_at.isoformat()
                }
            
            return {
                "success": True,
                "tasks": tasks_status,
                "stats": self.stats
            }
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel a task"""
        if task_id not in self.tasks:
            return {"error": f"Task not found: {task_id}"}
        
        task = self.tasks[task_id]
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return {"error": f"Task already finished: {task_id}"}
        
        # Cancel the task
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]
        
        # Update task status
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        
        # Update statistics
        self.stats["cancelled_tasks"] += 1
        
        self.logger.info(f"Cancelled task: {task_id}")
        
        return {
            "success": True,
            "task_id": task_id,
            "status": task.status.value
        }
    
    async def list_tasks(self, status: Optional[str] = None, 
                        task_type: Optional[str] = None,
                        limit: Optional[int] = None) -> Dict[str, Any]:
        """List tasks with optional filtering"""
        filtered_tasks = []
        
        for task in self.tasks.values():
            # Apply filters
            if status and task.status.value != status:
                continue
            
            if task_type and task.task_type != task_type:
                continue
            
            filtered_tasks.append(task)
        
        # Sort by creation time (newest first)
        filtered_tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        # Apply limit
        if limit:
            filtered_tasks = filtered_tasks[:limit]
        
        return {
            "success": True,
            "tasks": [self._task_to_dict(task) for task in filtered_tasks],
            "total": len(filtered_tasks)
        }
    
    async def register_task_handler(self, task_type: str, handler: Callable) -> None:
        """Register a task handler"""
        self.task_handlers[task_type] = handler
        self.logger.info(f"Registered task handler for type: {task_type}")
    
    async def unregister_task_handler(self, task_type: str) -> None:
        """Unregister a task handler"""
        if task_type in self.task_handlers:
            del self.task_handlers[task_type]
            self.logger.info(f"Unregistered task handler for type: {task_type}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get task manager statistics"""
        # Calculate average execution time
        completed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED and t.started_at and t.completed_at]
        
        if completed_tasks:
            total_time = sum((t.completed_at - t.started_at).total_seconds() for t in completed_tasks)
            self.stats["average_execution_time"] = total_time / len(completed_tasks)
        
        return {
            "success": True,
            "statistics": self.stats.copy(),
            "active_tasks": len(self.running_tasks),
            "queued_tasks": self.task_queue.qsize(),
            "registered_handlers": list(self.task_handlers.keys())
        }
    
    async def _worker(self, worker_id: str) -> None:
        """Worker task that processes tasks from the queue"""
        self.logger.info(f"Worker {worker_id} started")
        
        while self.is_running:
            try:
                # Get task from queue with timeout
                task_id = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                
                if task_id not in self.tasks:
                    self.logger.warning(f"Task not found: {task_id}")
                    continue
                
                task = self.tasks[task_id]
                
                # Check dependencies
                if not await self._check_dependencies(task):
                    # Re-queue task if dependencies are not met
                    await self.task_queue.put(task_id)
                    await asyncio.sleep(1)
                    continue
                
                # Execute task
                await self._execute_task(task)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in worker {worker_id}: {e}")
                await asyncio.sleep(1)
        
        self.logger.info(f"Worker {worker_id} stopped")
    
    async def _check_dependencies(self, task: Task) -> bool:
        """Check if task dependencies are satisfied"""
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                self.logger.error(f"Dependency not found: {dep_id}")
                return False
            
            dep_task = self.tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def _execute_task(self, task: Task) -> None:
        """Execute a task"""
        task_id = task.id
        
        try:
            # Update task status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            
            self.logger.info(f"Executing task: {task_id} ({task.name})")
            
            # Get task handler
            if task.task_type not in self.task_handlers:
                raise ValueError(f"No handler for task type: {task.task_type}")
            
            handler = self.task_handlers[task.task_type]
            
            # Create async task for execution
            if task.timeout:
                execution_task = asyncio.wait_for(
                    handler(task.parameters),
                    timeout=task.timeout
                )
            else:
                execution_task = handler(task.parameters)
            
            # Store running task
            self.running_tasks[task_id] = asyncio.create_task(execution_task)
            
            # Wait for completion
            result = await self.running_tasks[task_id]
            
            # Update task with result
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.progress = 1.0
            
            # Update statistics
            self.stats["completed_tasks"] += 1
            
            self.logger.info(f"Task completed: {task_id}")
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.TIMEOUT
            task.completed_at = datetime.now()
            task.error = f"Task timed out after {task.timeout} seconds"
            
            self.logger.warning(f"Task timed out: {task_id}")
            
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            task.error = "Task was cancelled"
            
            self.logger.info(f"Task cancelled: {task_id}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = str(e)
            
            # Update statistics
            self.stats["failed_tasks"] += 1
            
            self.logger.error(f"Task failed: {task_id} - {e}")
            self.logger.error(traceback.format_exc())
        
        finally:
            # Clean up running task
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "task_type": task.task_type,
            "parameters": task.parameters,
            "status": task.status.value,
            "priority": task.priority.value,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result,
            "error": task.error,
            "timeout": task.timeout,
            "progress": task.progress,
            "dependencies": task.dependencies,
            "tags": task.tags,
            "metadata": task.metadata
        }
    
    async def save_tasks(self, filename: str) -> None:
        """Save tasks to a file"""
        try:
            tasks_data = []
            for task in self.tasks.values():
                tasks_data.append(self._task_to_dict(task))
            
            with open(filename, 'w') as f:
                json.dump(tasks_data, f, indent=2)
            
            self.logger.info(f"Tasks saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving tasks: {e}")
    
    async def load_tasks(self, filename: str) -> None:
        """Load tasks from a file"""
        try:
            with open(filename, 'r') as f:
                tasks_data = json.load(f)
            
            for task_data in tasks_data:
                task = Task(
                    id=task_data["id"],
                    name=task_data["name"],
                    description=task_data["description"],
                    task_type=task_data["task_type"],
                    parameters=task_data["parameters"],
                    status=TaskStatus(task_data["status"]),
                    priority=TaskPriority(task_data["priority"]),
                    created_at=datetime.fromisoformat(task_data["created_at"]),
                    started_at=datetime.fromisoformat(task_data["started_at"]) if task_data["started_at"] else None,
                    completed_at=datetime.fromisoformat(task_data["completed_at"]) if task_data["completed_at"] else None,
                    result=task_data["result"],
                    error=task_data["error"],
                    timeout=task_data["timeout"],
                    progress=task_data["progress"],
                    dependencies=task_data["dependencies"],
                    tags=task_data["tags"],
                    metadata=task_data["metadata"]
                )
                
                self.tasks[task.id] = task
                
                # Add pending tasks to queue
                if task.status == TaskStatus.PENDING:
                    await self.task_queue.put(task.id)
            
            self.logger.info(f"Tasks loaded from {filename}")
            
        except Exception as e:
            self.logger.error(f"Error loading tasks: {e}")