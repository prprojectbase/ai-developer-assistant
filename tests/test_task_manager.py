"""
Unit tests for Task Manager module
"""

import pytest
import asyncio
import uuid
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.modules.task_manager import TaskManager, Task, TaskStatus, TaskPriority
from src.config.settings import get_settings


class TestTaskManager:
    """Test cases for TaskManager class"""
    
    @pytest.fixture
    def task_manager(self):
        """Create a TaskManager instance for testing"""
        return TaskManager(max_concurrent_tasks=2)
    
    @pytest.fixture
    def sample_task_data(self):
        """Sample task data for testing"""
        return {
            "name": "Test Task",
            "description": "A test task for unit testing",
            "type": "test_task",
            "parameters": {"test_param": "test_value"},
            "priority": TaskPriority.HIGH.value,
            "timeout": 30
        }
    
    @pytest.fixture
    def mock_handler(self):
        """Mock task handler for testing"""
        async def handler(parameters):
            await asyncio.sleep(0.1)  # Simulate work
            return {"result": "success", "parameters": parameters}
        return handler
    
    @pytest.mark.asyncio
    async def test_initialize(self, task_manager):
        """Test TaskManager initialization"""
        with patch('src.modules.task_manager.logging.getLogger') as mock_logger:
            mock_logger.return_value = Mock()
            
            await task_manager.initialize()
            
            assert task_manager.is_running is True
            assert len(task_manager.worker_tasks) == 2
            assert task_manager.event_loop is not None
            mock_logger.return_value.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_stop(self, task_manager):
        """Test TaskManager stop"""
        await task_manager.initialize()
        
        # Create a running task
        task_data = {
            "name": "Running Task",
            "description": "A running task",
            "type": "test_task",
            "parameters": {}
        }
        
        result = await task_manager.create_task(task_data)
        task_id = result["task_id"]
        
        # Give task time to start
        await asyncio.sleep(0.1)
        
        # Stop task manager
        await task_manager.stop()
        
        assert task_manager.is_running is False
        assert len(task_manager.worker_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_create_task(self, task_manager, sample_task_data):
        """Test creating a task"""
        await task_manager.initialize()
        
        result = await task_manager.create_task(sample_task_data)
        
        assert result["success"] is True
        assert "task_id" in result
        assert "task" in result
        
        task_id = result["task_id"]
        assert task_id in task_manager.tasks
        
        task = task_manager.tasks[task_id]
        assert task.name == sample_task_data["name"]
        assert task.description == sample_task_data["description"]
        assert task.task_type == sample_task_data["type"]
        assert task.parameters == sample_task_data["parameters"]
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_get_task(self, task_manager, sample_task_data):
        """Test getting task information"""
        await task_manager.initialize()
        
        # Create task
        result = await task_manager.create_task(sample_task_data)
        task_id = result["task_id"]
        
        # Get task
        result = await task_manager.get_task(task_id)
        
        assert result["success"] is True
        assert "task" in result
        assert result["task"]["id"] == task_id
        assert result["task"]["name"] == sample_task_data["name"]
        
        # Test getting non-existent task
        result = await task_manager.get_task("nonexistent_task")
        assert "error" in result
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_task_status(self, task_manager, sample_task_data):
        """Test getting task status"""
        await task_manager.initialize()
        
        # Create task
        result = await task_manager.create_task(sample_task_data)
        task_id = result["task_id"]
        
        # Get specific task status
        result = await task_manager.get_task_status(task_id)
        assert result["success"] is True
        assert result["task_id"] == task_id
        assert result["status"] == TaskStatus.PENDING.value
        
        # Get all tasks status
        result = await task_manager.get_task_status()
        assert result["success"] is True
        assert "tasks" in result
        assert "stats" in result
        assert task_id in result["tasks"]
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, task_manager, sample_task_data):
        """Test cancelling a task"""
        await task_manager.initialize()
        
        # Create task
        result = await task_manager.create_task(sample_task_data)
        task_id = result["task_id"]
        
        # Cancel task
        result = await task_manager.cancel_task(task_id)
        assert result["success"] is True
        assert result["status"] == TaskStatus.CANCELLED.value
        
        # Verify task is cancelled
        task = task_manager.tasks[task_id]
        assert task.status == TaskStatus.CANCELLED
        assert task.completed_at is not None
        
        # Test cancelling non-existent task
        result = await task_manager.cancel_task("nonexistent_task")
        assert "error" in result
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_list_tasks(self, task_manager):
        """Test listing tasks with filtering"""
        await task_manager.initialize()
        
        # Create multiple tasks
        tasks_data = [
            {
                "name": "Task 1",
                "description": "First task",
                "type": "type_a",
                "parameters": {}
            },
            {
                "name": "Task 2",
                "description": "Second task",
                "type": "type_b",
                "parameters": {}
            },
            {
                "name": "Task 3",
                "description": "Third task",
                "type": "type_a",
                "parameters": {}
            }
        ]
        
        task_ids = []
        for task_data in tasks_data:
            result = await task_manager.create_task(task_data)
            task_ids.append(result["task_id"])
        
        # List all tasks
        result = await task_manager.list_tasks()
        assert result["success"] is True
        assert result["total"] == 3
        assert len(result["tasks"]) == 3
        
        # Filter by type
        result = await task_manager.list_tasks(task_type="type_a")
        assert result["success"] is True
        assert result["total"] == 2
        assert len(result["tasks"]) == 2
        
        # Filter by status
        result = await task_manager.list_tasks(status="pending")
        assert result["success"] is True
        assert result["total"] == 3
        
        # Apply limit
        result = await task_manager.list_tasks(limit=2)
        assert result["success"] is True
        assert result["total"] == 2
        assert len(result["tasks"]) == 2
    
    @pytest.mark.asyncio
    async def test_register_task_handler(self, task_manager, mock_handler):
        """Test registering task handlers"""
        await task_manager.initialize()
        
        # Register handler
        await task_manager.register_task_handler("test_task", mock_handler)
        
        assert "test_task" in task_manager.task_handlers
        assert task_manager.task_handlers["test_task"] == mock_handler
        
        # Unregister handler
        await task_manager.unregister_task_handler("test_task")
        
        assert "test_task" not in task_manager.task_handlers
    
    @pytest.mark.asyncio
    async def test_task_execution(self, task_manager, mock_handler):
        """Test task execution with handler"""
        await task_manager.initialize()
        
        # Register handler
        await task_manager.register_task_handler("test_task", mock_handler)
        
        # Create and execute task
        task_data = {
            "name": "Execution Test",
            "description": "Test task execution",
            "type": "test_task",
            "parameters": {"test": "value"}
        }
        
        result = await task_manager.create_task(task_data)
        task_id = result["task_id"]
        
        # Wait for task to complete
        await asyncio.sleep(0.5)
        
        # Check task status
        result = await task_manager.get_task_status(task_id)
        assert result["status"] == TaskStatus.COMPLETED.value
        assert result["progress"] == 1.0
        
        # Check task result
        task = task_manager.tasks[task_id]
        assert task.result is not None
        assert task.result["result"] == "success"
        assert task.result["parameters"]["test"] == "value"
    
    @pytest.mark.asyncio
    async def test_task_timeout(self, task_manager):
        """Test task timeout handling"""
        await task_manager.initialize()
        
        # Create a slow handler
        async def slow_handler(parameters):
            await asyncio.sleep(2)  # Sleep longer than timeout
            return {"result": "completed"}
        
        await task_manager.register_task_handler("slow_task", slow_handler)
        
        # Create task with short timeout
        task_data = {
            "name": "Slow Task",
            "description": "Task that will timeout",
            "type": "slow_task",
            "parameters": {},
            "timeout": 0.5  # 0.5 second timeout
        }
        
        result = await task_manager.create_task(task_data)
        task_id = result["task_id"]
        
        # Wait for task to timeout
        await asyncio.sleep(1)
        
        # Check task status
        result = await task_manager.get_task_status(task_id)
        assert result["status"] == TaskStatus.TIMEOUT.value
        assert "timed out" in result["error"]
    
    @pytest.mark.asyncio
    async def test_task_dependencies(self, task_manager, mock_handler):
        """Test task dependencies"""
        await task_manager.initialize()
        
        # Register handler
        await task_manager.register_task_handler("test_task", mock_handler)
        
        # Create dependency task
        dep_task_data = {
            "name": "Dependency Task",
            "description": "Task that others depend on",
            "type": "test_task",
            "parameters": {}
        }
        
        dep_result = await task_manager.create_task(dep_task_data)
        dep_task_id = dep_result["task_id"]
        
        # Wait for dependency to complete
        await asyncio.sleep(0.5)
        
        # Create task with dependency
        task_data = {
            "name": "Dependent Task",
            "description": "Task with dependencies",
            "type": "test_task",
            "parameters": {},
            "dependencies": [dep_task_id]
        }
        
        result = await task_manager.create_task(task_data)
        task_id = result["task_id"]
        
        # Wait for task to complete
        await asyncio.sleep(0.5)
        
        # Check task status
        result = await task_manager.get_task_status(task_id)
        assert result["status"] == TaskStatus.COMPLETED.value
    
    @pytest.mark.asyncio
    async def test_task_statistics(self, task_manager, mock_handler):
        """Test task manager statistics"""
        await task_manager.initialize()
        
        # Register handler
        await task_manager.register_task_handler("test_task", mock_handler)
        
        # Create and execute multiple tasks
        for i in range(3):
            task_data = {
                "name": f"Task {i}",
                "description": f"Test task {i}",
                "type": "test_task",
                "parameters": {}
            }
            await task_manager.create_task(task_data)
        
        # Wait for tasks to complete
        await asyncio.sleep(1)
        
        # Get statistics
        result = await task_manager.get_statistics()
        assert result["success"] is True
        assert "statistics" in result
        assert "active_tasks" in result
        assert "queued_tasks" in result
        assert "registered_handlers" in result
        
        stats = result["statistics"]
        assert stats["total_tasks"] == 3
        assert stats["completed_tasks"] == 3
        assert stats["failed_tasks"] == 0
    
    @pytest.mark.asyncio
    async def test_task_error_handling(self, task_manager):
        """Test task error handling"""
        await task_manager.initialize()
        
        # Create a failing handler
        async def failing_handler(parameters):
            raise ValueError("Test error")
        
        await task_manager.register_task_handler("failing_task", failing_handler)
        
        # Create task that will fail
        task_data = {
            "name": "Failing Task",
            "description": "Task that will fail",
            "type": "failing_task",
            "parameters": {}
        }
        
        result = await task_manager.create_task(task_data)
        task_id = result["task_id"]
        
        # Wait for task to fail
        await asyncio.sleep(0.5)
        
        # Check task status
        result = await task_manager.get_task_status(task_id)
        assert result["status"] == TaskStatus.FAILED.value
        assert "error" in result
        assert "Test error" in result["error"]
        
        # Check statistics
        stats_result = await task_manager.get_statistics()
        assert stats_result["statistics"]["failed_tasks"] == 1
    
    @pytest.mark.asyncio
    async def test_task_tags_and_metadata(self, task_manager, mock_handler):
        """Test task tags and metadata"""
        await task_manager.initialize()
        
        # Register handler
        await task_manager.register_task_handler("test_task", mock_handler)
        
        # Create task with tags and metadata
        task_data = {
            "name": "Tagged Task",
            "description": "Task with tags and metadata",
            "type": "test_task",
            "parameters": {},
            "tags": ["important", "frontend"],
            "metadata": {"project": "web_app", "version": "1.0"}
        }
        
        result = await task_manager.create_task(task_data)
        task_id = result["task_id"]
        
        # Check task tags and metadata
        task = task_manager.tasks[task_id]
        assert "important" in task.tags
        assert "frontend" in task.tags
        assert task.metadata["project"] == "web_app"
        assert task.metadata["version"] == "1.0"
    
    @pytest.mark.asyncio
    async def test_task_persistence(self, task_manager, mock_handler):
        """Test task persistence (save/load)"""
        await task_manager.initialize()
        
        # Register handler
        await task_manager.register_task_handler("test_task", mock_handler)
        
        # Create tasks
        for i in range(2):
            task_data = {
                "name": f"Persist Task {i}",
                "description": f"Task for persistence test {i}",
                "type": "test_task",
                "parameters": {}
            }
            await task_manager.create_task(task_data)
        
        # Wait for tasks to complete
        await asyncio.sleep(0.5)
        
        # Save tasks
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            mock_json = Mock()
            
            with patch('json.dump', mock_json):
                await task_manager.save_tasks("test_tasks.json")
                mock_open.assert_called_once_with("test_tasks.json", 'w')
                mock_json.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self, task_manager):
        """Test concurrent task execution"""
        await task_manager.initialize()
        
        # Create a handler that tracks execution
        execution_times = []
        
        async def tracking_handler(parameters):
            start_time = datetime.now()
            await asyncio.sleep(0.2)  # Simulate work
            end_time = datetime.now()
            execution_times.append((start_time, end_time))
            return {"result": "completed"}
        
        await task_manager.register_task_handler("tracking_task", tracking_handler)
        
        # Create multiple tasks simultaneously
        task_ids = []
        for i in range(4):  # More tasks than workers
            task_data = {
                "name": f"Concurrent Task {i}",
                "description": f"Concurrent test task {i}",
                "type": "tracking_task",
                "parameters": {}
            }
            result = await task_manager.create_task(task_data)
            task_ids.append(result["task_id"])
        
        # Wait for all tasks to complete
        await asyncio.sleep(1)
        
        # Check that tasks were executed concurrently
        assert len(execution_times) == 4
        
        # Verify that some tasks overlapped (concurrent execution)
        overlaps = 0
        for i in range(len(execution_times)):
            for j in range(i + 1, len(execution_times)):
                start1, end1 = execution_times[i]
                start2, end2 = execution_times[j]
                if start1 < end2 and start2 < end1:
                    overlaps += 1
        
        # Should have some overlaps due to concurrent execution
        assert overlaps > 0