#!/usr/bin/env python3
"""
Example: Task Manager

This script demonstrates how to use the Task Manager module
to create, manage, and monitor asynchronous tasks.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modules.task_manager import TaskManager, TaskPriority


async def sample_task_handler(parameters):
    """Sample task handler that simulates work"""
    task_name = parameters.get("name", "Unknown Task")
    duration = parameters.get("duration", 2)
    
    print(f"🔄 Starting task: {task_name}")
    await asyncio.sleep(duration)
    print(f"✅ Completed task: {task_name}")
    
    return {
        "success": True,
        "task_name": task_name,
        "duration": duration,
        "completed_at": time.time()
    }


async def failing_task_handler(parameters):
    """Sample task handler that always fails"""
    await asyncio.sleep(1)
    raise Exception("This task is designed to fail")


async def main():
    """Demonstrate task management"""
    print("📋 Task Manager Example")
    print("=" * 40)
    
    # Initialize task manager
    task_manager = TaskManager(max_concurrent_tasks=3)
    await task_manager.initialize()
    
    try:
        # Register task handlers
        await task_manager.register_task_handler("sample_task", sample_task_handler)
        await task_manager.register_task_handler("failing_task", failing_task_handler)
        
        # Example 1: Create a simple task
        print("\n1. Creating a simple task...")
        task_data = {
            "name": "Sample Task 1",
            "description": "A simple sample task",
            "type": "sample_task",
            "parameters": {
                "name": "First Task",
                "duration": 2
            }
        }
        
        result = await task_manager.create_task(task_data)
        if result["success"]:
            task_id = result["task_id"]
            print(f"✅ Task created: {task_id}")
        else:
            print(f"❌ Error: {result['error']}")
            return
        
        # Example 2: Create multiple tasks
        print("\n2. Creating multiple tasks...")
        task_ids = []
        for i in range(5):
            task_data = {
                "name": f"Sample Task {i+2}",
                "description": f"Sample task number {i+2}",
                "type": "sample_task",
                "parameters": {
                    "name": f"Task {i+2}",
                    "duration": 1
                },
                "priority": TaskPriority.HIGH if i < 2 else TaskPriority.MEDIUM
            }
            
            result = await task_manager.create_task(task_data)
            if result["success"]:
                task_ids.append(result["task_id"])
                print(f"✅ Task created: {result['task_id']}")
            else:
                print(f"❌ Error: {result['error']}")
        
        # Example 3: Create a failing task
        print("\n3. Creating a task that will fail...")
        failing_task_data = {
            "name": "Failing Task",
            "description": "This task is designed to fail",
            "type": "failing_task",
            "parameters": {}
        }
        
        result = await task_manager.create_task(failing_task_data)
        if result["success"]:
            failing_task_id = result["task_id"]
            print(f"✅ Failing task created: {failing_task_id}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 4: Monitor task progress
        print("\n4. Monitoring task progress...")
        all_task_ids = [task_id] + task_ids + [failing_task_id]
        
        # Wait for tasks to complete
        while True:
            completed_count = 0
            for task_id in all_task_ids:
                status = await task_manager.get_task_status(task_id)
                if status["status"] in ["completed", "failed", "cancelled"]:
                    completed_count += 1
                
                print(f"  Task {task_id[:8]}: {status['status']} "
                      f"({status['progress']:.1%})")
            
            if completed_count == len(all_task_ids):
                break
            
            await asyncio.sleep(1)
        
        print("✅ All tasks completed!")
        
        # Example 5: Get task details
        print("\n5. Getting task details...")
        for task_id in task_ids[:2]:  # Check first two tasks
            task_info = await task_manager.get_task(task_id)
            if task_info["success"]:
                task = task_info["task"]
                print(f"✅ Task: {task['name']}")
                print(f"   Status: {task['status']}")
                print(f"   Created: {task['created_at']}")
                print(f"   Duration: {task['completed_at'] - task['started_at']:.2f}s" if task['started_at'] and task['completed_at'] else "   Duration: N/A")
                if task['result']:
                    print(f"   Result: {task['result']['task_name']}")
            else:
                print(f"❌ Error: {task_info['error']}")
        
        # Example 6: List all tasks
        print("\n6. Listing all tasks...")
        result = await task_manager.list_tasks()
        if result["success"]:
            print(f"✅ Total tasks: {result['total']}")
            for task in result["tasks"]:
                status_icon = "✅" if task["status"] == "completed" else "❌" if task["status"] == "failed" else "🔄"
                print(f"  {status_icon} {task['name']} ({task['status']})")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 7: Get statistics
        print("\n7. Getting task manager statistics...")
        stats = await task_manager.get_statistics()
        if stats["success"]:
            print("✅ Task Manager Statistics:")
            print(f"   Total tasks: {stats['statistics']['total_tasks']}")
            print(f"   Completed: {stats['statistics']['completed_tasks']}")
            print(f"   Failed: {stats['statistics']['failed_tasks']}")
            print(f"   Cancelled: {stats['statistics']['cancelled_tasks']}")
            print(f"   Average execution time: {stats['statistics']['average_execution_time']:.2f}s")
            print(f"   Active workers: {stats['active_tasks']}")
            print(f"   Queued tasks: {stats['queued_tasks']}")
        else:
            print(f"❌ Error: {stats['error']}")
        
        # Example 8: Create tasks with dependencies
        print("\n8. Creating tasks with dependencies...")
        
        # First, create a dependency task
        dep_task_data = {
            "name": "Dependency Task",
            "description": "Task that others depend on",
            "type": "sample_task",
            "parameters": {"name": "Dependency", "duration": 1}
        }
        
        dep_result = await task_manager.create_task(dep_task_data)
        if not dep_result["success"]:
            print(f"❌ Error creating dependency task: {dep_result['error']}")
            return
        
        dep_task_id = dep_result["task_id"]
        
        # Create tasks that depend on the first task
        dependent_task_ids = []
        for i in range(3):
            task_data = {
                "name": f"Dependent Task {i+1}",
                "description": f"Task that depends on {dep_task_id}",
                "type": "sample_task",
                "parameters": {"name": f"Dependent {i+1}", "duration": 1},
                "dependencies": [dep_task_id]
            }
            
            result = await task_manager.create_task(task_data)
            if result["success"]:
                dependent_task_ids.append(result["task_id"])
                print(f"✅ Created dependent task: {result['task_id']}")
            else:
                print(f"❌ Error: {result['error']}")
        
        # Wait for all tasks to complete
        all_dependent_ids = [dep_task_id] + dependent_task_ids
        while True:
            completed_count = 0
            for task_id in all_dependent_ids:
                status = await task_manager.get_task_status(task_id)
                if status["status"] in ["completed", "failed", "cancelled"]:
                    completed_count += 1
            
            if completed_count == len(all_dependent_ids):
                break
            
            await asyncio.sleep(0.5)
        
        print("✅ All dependent tasks completed!")
        
        # Example 9: Cancel a task (create a long-running task first)
        print("\n9. Creating and cancelling a long-running task...")
        
        long_task_data = {
            "name": "Long Running Task",
            "description": "Task that will be cancelled",
            "type": "sample_task",
            "parameters": {"name": "Long Task", "duration": 10}
        }
        
        result = await task_manager.create_task(long_task_data)
        if result["success"]:
            long_task_id = result["task_id"]
            print(f"✅ Created long task: {long_task_id}")
            
            # Wait a bit then cancel it
            await asyncio.sleep(2)
            
            cancel_result = await task_manager.cancel_task(long_task_id)
            if cancel_result["success"]:
                print(f"✅ Task cancelled: {long_task_id}")
            else:
                print(f"❌ Error cancelling task: {cancel_result['error']}")
        else:
            print(f"❌ Error creating long task: {result['error']}")
        
        # Example 10: Filter tasks by status
        print("\n10. Filtering tasks by status...")
        
        # Get only completed tasks
        result = await task_manager.list_tasks(status="completed")
        if result["success"]:
            print(f"✅ Completed tasks ({result['total']}):")
            for task in result["tasks"][:5]:  # Show first 5
                print(f"  ✅ {task['name']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Get only failed tasks
        result = await task_manager.list_tasks(status="failed")
        if result["success"]:
            print(f"✅ Failed tasks ({result['total']}):")
            for task in result["tasks"]:
                print(f"  ❌ {task['name']}")
        else:
            print(f"❌ Error: {result['error']}")
        
    finally:
        # Clean up
        await task_manager.stop()
    
    print("\n✅ Task manager example completed!")


if __name__ == "__main__":
    asyncio.run(main())