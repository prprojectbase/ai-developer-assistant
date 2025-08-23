#!/usr/bin/env python3
"""
Example: Terminal Operations

This script demonstrates how to use the Terminal Operations module
to execute shell commands and manage terminal sessions.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modules.terminal_operations import TerminalOperations


async def main():
    """Demonstrate terminal operations"""
    print("💻 Terminal Operations Example")
    print("=" * 40)
    
    # Initialize terminal operations
    terminal_ops = TerminalOperations()
    await terminal_ops.initialize()
    
    try:
        # Example 1: Run a simple command
        print("\n1. Running a simple command...")
        result = await terminal_ops.run_command("echo 'Hello, World!'")
        if result["success"]:
            print(f"✅ Command output: {result['stdout'].strip()}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 2: Run a command with timeout
        print("\n2. Running command with timeout...")
        result = await terminal_ops.run_command("sleep 2 && echo 'Done sleeping'", timeout=5)
        if result["success"]:
            print(f"✅ Command completed: {result['stdout'].strip()}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 3: List files in current directory
        print("\n3. Listing files in current directory...")
        result = await terminal_ops.run_command("ls -la")
        if result["success"]:
            print("✅ Directory listing:")
            for line in result['stdout'].strip().split('\n'):
                print(f"  {line}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 4: Get system information
        print("\n4. Getting system information...")
        result = await terminal_ops.get_system_info()
        if result["success"]:
            sys_info = result["system"]
            print(f"✅ System: {sys_info['system']} {sys_info['release']}")
            print(f"✅ Python: {sys_info['python_version']}")
            print(f"✅ CPU Count: {sys_info['cpu_count']}")
            if 'memory_total' in sys_info:
                import psutil
                memory_gb = sys_info['memory_total'] / (1024**3)
                print(f"✅ Total Memory: {memory_gb:.1f} GB")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 5: Start an interactive Python session
        print("\n5. Starting interactive Python session...")
        result = await terminal_ops.run_interactive_command("python")
        if result["success"]:
            process_id = result["process_id"]
            print(f"✅ Process started with ID: {process_id}")
            
            # Send some Python commands
            commands = [
                "print('Hello from interactive Python!')",
                "x = 42",
                "print(f'The answer is {x}')",
                "exit()"
            ]
            
            for cmd in commands:
                print(f"  Sending: {cmd}")
                result = await terminal_ops.send_input_to_process(process_id, cmd)
                if result["success"]:
                    # Wait a bit and get output
                    await asyncio.sleep(0.5)
                    output = await terminal_ops.get_process_output(process_id)
                    if output["success"]:
                        for line in output["output"]:
                            if line["type"] == "stdout":
                                print(f"    Output: {line['content']}")
                else:
                    print(f"  ❌ Error: {result['error']}")
            
            # Terminate the process
            await terminal_ops.terminate_process(process_id)
            print("  ✅ Process terminated")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 6: Run a command in a specific directory
        print("\n6. Running command in specific directory...")
        result = await terminal_ops.run_command("pwd", cwd="/tmp")
        if result["success"]:
            print(f"✅ Working directory: {result['stdout'].strip()}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 7: Run command with environment variables
        print("\n7. Running command with custom environment...")
        env = {"MY_VAR": "test_value", "ANOTHER_VAR": "another_test"}
        result = await terminal_ops.run_command("echo $MY_VAR and $ANOTHER_VAR", env=env)
        if result["success"]:
            print(f"✅ Environment variables: {result['stdout'].strip()}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 8: List active processes
        print("\n8. Listing active processes...")
        result = await terminal_ops.list_active_processes()
        if result["success"]:
            print(f"✅ Active processes: {result['count']}")
            for process in result["processes"]:
                status = "running" if process["is_running"] else "terminated"
                print(f"  - {process['process_id']} (PID: {process['pid']}, Status: {status})")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 9: Change working directory
        print("\n9. Changing working directory...")
        original_dir = await terminal_ops.get_working_directory()
        print(f"  Original directory: {original_dir['working_directory']}")
        
        result = await terminal_ops.change_directory("/tmp")
        if result["success"]:
            print(f"✅ Changed to: {result['new_directory']}")
            
            # Verify the change
            result = await terminal_ops.get_working_directory()
            print(f"  Current directory: {result['working_directory']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 10: Run a failing command
        print("\n10. Running a command that should fail...")
        result = await terminal_ops.run_command("nonexistent_command")
        if not result["success"]:
            print(f"✅ Command failed as expected: {result['error']}")
            print(f"   Exit code: {result['exit_code']}")
        else:
            print("❌ Command should have failed but didn't")
        
    finally:
        # Clean up
        await terminal_ops.stop()
    
    print("\n✅ Terminal operations example completed!")


if __name__ == "__main__":
    asyncio.run(main())