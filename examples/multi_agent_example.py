#!/usr/bin/env python3
"""
Example: Multi-Agent Communication

This script demonstrates how to use the Multi-Agent Communication system
to enable agents to communicate with each other.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.communication_agent import CommunicationAgent, AgentClient, AgentMessage


class SimpleAgent:
    """A simple agent that can send and receive messages"""
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.message_log = []
    
    async def handle_message(self, message):
        """Handle incoming messages"""
        self.message_log.append(message)
        print(f"📨 {self.name} received message from {message.sender}:")
        print(f"   Type: {message.message_type}")
        print(f"   Content: {json.dumps(message.content, indent=2)}")
        
        # Send a response
        if message.message_type == "greeting":
            response = AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type="greeting_response",
                content={
                    "message": f"Hello from {self.name}!",
                    "timestamp": datetime.now().isoformat(),
                    "original_message_id": message.message_id
                }
            )
            return response
        
        elif message.message_type == "task_request":
            # Simulate processing a task
            task_description = message.content.get("task", "Unknown task")
            response = AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type="task_response",
                content={
                    "status": "completed",
                    "result": f"Task '{task_description}' completed by {self.name}",
                    "timestamp": datetime.now().isoformat()
                }
            )
            return response
        
        return None


class FileAgent(SimpleAgent):
    """Agent specialized in file operations"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "File Agent")
        self.files = {}  # Simulated file storage
    
    async def handle_message(self, message):
        """Handle file-related messages"""
        self.message_log.append(message)
        print(f"📁 File Agent received message from {message.sender}:")
        print(f"   Type: {message.message_type}")
        
        if message.message_type == "file_read":
            filename = message.content.get("filename")
            if filename in self.files:
                response = AgentMessage(
                    sender=self.agent_id,
                    recipient=message.sender,
                    message_type="file_content",
                    content={
                        "filename": filename,
                        "content": self.files[filename],
                        "status": "success"
                    }
                )
            else:
                response = AgentMessage(
                    sender=self.agent_id,
                    recipient=message.sender,
                    message_type="file_error",
                    content={
                        "filename": filename,
                        "error": "File not found",
                        "status": "error"
                    }
                )
            return response
        
        elif message.message_type == "file_write":
            filename = message.content.get("filename")
            content = message.content.get("content", "")
            self.files[filename] = content
            
            response = AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type="file_write_response",
                content={
                    "filename": filename,
                    "status": "success",
                    "size": len(content)
                }
            )
            return response
        
        # Handle other message types with parent method
        return await super().handle_message(message)


class ComputeAgent(SimpleAgent):
    """Agent specialized in computational tasks"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "Compute Agent")
    
    async def handle_message(self, message):
        """Handle computation-related messages"""
        self.message_log.append(message)
        print(f"🔢 Compute Agent received message from {message.sender}:")
        print(f"   Type: {message.message_type}")
        
        if message.message_type == "compute_request":
            operation = message.content.get("operation")
            operands = message.content.get("operands", [])
            
            try:
                if operation == "add":
                    result = sum(operands)
                elif operation == "multiply":
                    result = 1
                    for num in operands:
                        result *= num
                elif operation == "factorial":
                    n = operands[0] if operands else 0
                    result = 1
                    for i in range(1, n + 1):
                        result *= i
                else:
                    result = f"Unknown operation: {operation}"
                
                response = AgentMessage(
                    sender=self.agent_id,
                    recipient=message.sender,
                    message_type="compute_result",
                    content={
                        "operation": operation,
                        "operands": operands,
                        "result": result,
                        "status": "success"
                    }
                )
            except Exception as e:
                response = AgentMessage(
                    sender=self.agent_id,
                    recipient=message.sender,
                    message_type="compute_error",
                    content={
                        "operation": operation,
                        "error": str(e),
                        "status": "error"
                    }
                )
            
            return response
        
        # Handle other message types with parent method
        return await super().handle_message(message)


async def main():
    """Demonstrate multi-agent communication"""
    print("🤝 Multi-Agent Communication Example")
    print("=" * 40)
    
    # Initialize communication agent (server)
    comm_agent = CommunicationAgent()
    await comm_agent.initialize()
    
    # Create specialized agents
    file_agent = FileAgent("file_agent")
    compute_agent = ComputeAgent("compute_agent")
    general_agent1 = SimpleAgent("general_agent_1", "General Agent 1")
    general_agent2 = SimpleAgent("general_agent_2", "General Agent 2")
    
    # Register agents with communication system
    await comm_agent.register_agent("file_agent", file_agent)
    await comm_agent.register_agent("compute_agent", compute_agent)
    await comm_agent.register_agent("general_agent_1", general_agent1)
    await comm_agent.register_agent("general_agent_2", general_agent2)
    
    # Create client agents for demonstration
    client1 = AgentClient("client_1")
    client2 = AgentClient("client_2")
    
    try:
        # Connect clients
        await client1.connect()
        await client2.connect()
        
        # Set up message handlers for clients
        async def handle_client1_message(message):
            print(f"📱 Client 1 received: {message.message_type} from {message.sender}")
        
        async def handle_client2_message(message):
            print(f"📱 Client 2 received: {message.message_type} from {message.sender}")
        
        client1.register_message_handler("greeting_response", handle_client1_message)
        client1.register_message_handler("task_response", handle_client1_message)
        client2.register_message_handler("greeting_response", handle_client2_message)
        client2.register_message_handler("task_response", handle_client2_message)
        
        print("\n✅ All agents connected and registered")
        
        # Example 1: Greeting exchange
        print("\n1. Testing greeting exchange...")
        
        # Client 1 sends greeting to general agent 1
        greeting1 = AgentMessage(
            sender="client_1",
            recipient="general_agent_1",
            message_type="greeting",
            content={
                "message": "Hello from Client 1!",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        await client1.send_message(greeting1)
        await asyncio.sleep(1)  # Wait for response
        
        # Client 2 sends greeting to general agent 2
        greeting2 = AgentMessage(
            sender="client_2",
            recipient="general_agent_2",
            message_type="greeting",
            content={
                "message": "Hello from Client 2!",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        await client2.send_message(greeting2)
        await asyncio.sleep(1)  # Wait for response
        
        # Example 2: File operations
        print("\n2. Testing file operations...")
        
        # Write a file
        write_message = AgentMessage(
            sender="client_1",
            recipient="file_agent",
            message_type="file_write",
            content={
                "filename": "test.txt",
                "content": "Hello, Multi-Agent World!"
            }
        )
        
        await client1.send_message(write_message)
        await asyncio.sleep(1)
        
        # Read the file
        read_message = AgentMessage(
            sender="client_2",
            recipient="file_agent",
            message_type="file_read",
            content={
                "filename": "test.txt"
            }
        )
        
        await client2.send_message(read_message)
        await asyncio.sleep(1)
        
        # Try to read non-existent file
        read_error_message = AgentMessage(
            sender="client_1",
            recipient="file_agent",
            message_type="file_read",
            content={
                "filename": "nonexistent.txt"
            }
        )
        
        await client1.send_message(read_error_message)
        await asyncio.sleep(1)
        
        # Example 3: Computational tasks
        print("\n3. Testing computational tasks...")
        
        # Addition
        add_message = AgentMessage(
            sender="client_1",
            recipient="compute_agent",
            message_type="compute_request",
            content={
                "operation": "add",
                "operands": [5, 3, 7]
            }
        )
        
        await client1.send_message(add_message)
        await asyncio.sleep(1)
        
        # Multiplication
        multiply_message = AgentMessage(
            sender="client_2",
            recipient="compute_agent",
            message_type="compute_request",
            content={
                "operation": "multiply",
                "operands": [4, 6, 2]
            }
        )
        
        await client2.send_message(multiply_message)
        await asyncio.sleep(1)
        
        # Factorial
        factorial_message = AgentMessage(
            sender="client_1",
            recipient="compute_agent",
            message_type="compute_request",
            content={
                "operation": "factorial",
                "operands": [5]
            }
        )
        
        await client1.send_message(factorial_message)
        await asyncio.sleep(1)
        
        # Example 4: Task delegation
        print("\n4. Testing task delegation...")
        
        # Client 1 delegates task to general agent 1
        task_message = AgentMessage(
            sender="client_1",
            recipient="general_agent_1",
            message_type="task_request",
            content={
                "task": "Analyze system performance",
                "priority": "high",
                "deadline": "2024-01-01"
            }
        )
        
        await client1.send_message(task_message)
        await asyncio.sleep(1)
        
        # Client 2 delegates different task to general agent 2
        task_message2 = AgentMessage(
            sender="client_2",
            recipient="general_agent_2",
            message_type="task_request",
            content={
                "task": "Generate weekly report",
                "priority": "medium",
                "deadline": "2024-01-02"
            }
        )
        
        await client2.send_message(task_message2)
        await asyncio.sleep(1)
        
        # Example 5: Broadcast message
        print("\n5. Testing broadcast message...")
        
        # Broadcast a system announcement
        broadcast_message = AgentMessage(
            sender="system",
            recipient="all",
            message_type="system_announcement",
            content={
                "message": "System maintenance scheduled for tonight",
                "scheduled_time": "23:00 UTC",
                "duration": "2 hours"
            }
        )
        
        await comm_agent.broadcast_message(broadcast_message)
        await asyncio.sleep(1)
        
        # Example 6: Get message history
        print("\n6. Getting message history...")
        
        history = await comm_agent.get_message_history(limit=10)
        print(f"✅ Message history (last {len(history)} messages):")
        
        for i, message in enumerate(history, 1):
            print(f"   {i}. {message.sender} -> {message.recipient}: {message.message_type}")
        
        # Example 7: Get connected agents
        print("\n7. Getting connected agents...")
        
        connected_agents = await comm_agent.get_connected_agents()
        print(f"✅ Connected agents: {connected_agents}")
        
        # Example 8: Save and load message history
        print("\n8. Testing message persistence...")
        
        # Save message history
        await comm_agent.save_message_history("message_history.json")
        print("✅ Message history saved to message_history.json")
        
        # Load message history (in a real scenario, this would be after a restart)
        await comm_agent.load_message_history("message_history.json")
        print("✅ Message history loaded")
        
        # Example 9: Agent-to-agent communication
        print("\n9. Testing direct agent-to-agent communication...")
        
        # General agent 1 sends message to file agent
        agent_message = AgentMessage(
            sender="general_agent_1",
            recipient="file_agent",
            message_type="file_write",
            content={
                "filename": "agent_communication.txt",
                "content": "This file was created through agent-to-agent communication"
            }
        )
        
        await comm_agent.send_message_to_agent("file_agent", agent_message)
        await asyncio.sleep(1)
        
        # Example 10: Complex workflow
        print("\n10. Testing complex workflow...")
        
        # Client 1 requests computation and file storage
        workflow_message = AgentMessage(
            sender="client_1",
            recipient="compute_agent",
            message_type="compute_request",
            content={
                "operation": "factorial",
                "operands": [6]
            }
        )
        
        await client1.send_message(workflow_message)
        await asyncio.sleep(1)
        
        # Now store the result in a file (simulated - in reality, compute agent would send to file agent)
        storage_message = AgentMessage(
            sender="client_1",
            recipient="file_agent",
            message_type="file_write",
            content={
                "filename": "factorial_result.txt",
                "content": "Factorial of 6 is 720"
            }
        )
        
        await client1.send_message(storage_message)
        await asyncio.sleep(1)
        
        # Verify the file was stored
        verify_message = AgentMessage(
            sender="client_2",
            recipient="file_agent",
            message_type="file_read",
            content={
                "filename": "factorial_result.txt"
            }
        )
        
        await client2.send_message(verify_message)
        await asyncio.sleep(1)
        
    finally:
        # Clean up
        await client1.disconnect()
        await client2.disconnect()
        await comm_agent.stop()
    
    print("\n✅ Multi-agent communication example completed!")


if __name__ == "__main__":
    asyncio.run(main())