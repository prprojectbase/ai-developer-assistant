import asyncio
import logging
import os
import shlex
import subprocess
import tempfile
import threading
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import json

from ..config.settings import get_settings


class TerminalOperations:
    """Terminal operations module for the AI Developer Assistant"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.workspace_dir = Path(self.settings.workspace_dir)
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.process_outputs: Dict[str, List[str]] = {}
        self.process_locks: Dict[str, threading.Lock] = {}
        
    async def initialize(self) -> None:
        """Initialize the terminal operations module"""
        self.logger.info("Initializing Terminal Operations module...")
        
        # Ensure workspace directory exists
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Terminal Operations module initialized")
    
    async def stop(self) -> None:
        """Stop the terminal operations module"""
        self.logger.info("Stopping Terminal Operations module...")
        
        # Terminate all active processes
        for process_id, process in self.active_processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                self.logger.error(f"Error terminating process {process_id}: {e}")
        
        self.active_processes.clear()
        self.process_outputs.clear()
        self.process_locks.clear()
        
        self.logger.info("Terminal Operations module stopped")
    
    async def execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a terminal command"""
        command_type = command.get("type")
        
        try:
            if command_type == "run_command":
                return await self.run_command(
                    command["command"],
                    command.get("cwd"),
                    command.get("timeout", 30),
                    command.get("env"),
                    command.get("capture_output", True)
                )
            
            elif command_type == "run_interactive":
                return await self.run_interactive_command(
                    command["command"],
                    command.get("cwd"),
                    command.get("process_id"),
                    command.get("env")
                )
            
            elif command_type == "send_input":
                return await self.send_input_to_process(
                    command["process_id"],
                    command["input"]
                )
            
            elif command_type == "get_process_output":
                return await self.get_process_output(command["process_id"])
            
            elif command_type == "terminate_process":
                return await self.terminate_process(command["process_id"])
            
            elif command_type == "list_processes":
                return await self.list_active_processes()
            
            elif command_type == "get_system_info":
                return await self.get_system_info()
            
            elif command_type == "change_directory":
                return await self.change_directory(command["path"])
            
            elif command_type == "get_working_directory":
                return await self.get_working_directory()
            
            else:
                return {"error": f"Unknown command type: {command_type}"}
                
        except Exception as e:
            self.logger.error(f"Error executing terminal command {command_type}: {e}")
            return {"error": str(e)}
    
    async def run_command(self, command: str, cwd: Optional[str] = None, 
                         timeout: int = 30, env: Optional[Dict[str, str]] = None,
                         capture_output: bool = True) -> Dict[str, Any]:
        """Run a command and wait for completion"""
        working_dir = self._get_working_directory(cwd)
        
        # Prepare environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        # Add workspace directory to PATH
        process_env["PATH"] = f"{working_dir}:{process_env.get('PATH', '')}"
        
        try:
            # Parse command safely
            if isinstance(command, str):
                cmd_args = shlex.split(command)
            else:
                cmd_args = command
            
            self.logger.info(f"Executing command: {command} in {working_dir}")
            
            # Run the command
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                cwd=working_dir,
                env=process_env,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                text=True
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                stdout, stderr = await process.communicate()
                return {
                    "success": False,
                    "command": command,
                    "exit_code": -1,
                    "stdout": stdout,
                    "stderr": stderr,
                    "timeout": True,
                    "timeout_seconds": timeout
                }
            
            return {
                "success": process.returncode == 0,
                "command": command,
                "exit_code": process.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "working_directory": str(working_dir)
            }
            
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "working_directory": str(working_dir)
            }
    
    async def run_interactive_command(self, command: str, cwd: Optional[str] = None,
                                    process_id: Optional[str] = None,
                                    env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Run an interactive command that can receive input"""
        working_dir = self._get_working_directory(cwd)
        
        # Generate process ID if not provided
        if not process_id:
            process_id = f"proc_{len(self.active_processes)}"
        
        # Prepare environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        process_env["PATH"] = f"{working_dir}:{process_env.get('PATH', '')}"
        
        try:
            # Parse command safely
            if isinstance(command, str):
                cmd_args = shlex.split(command)
            else:
                cmd_args = command
            
            self.logger.info(f"Starting interactive command: {command} (ID: {process_id})")
            
            # Start the process
            process = subprocess.Popen(
                cmd_args,
                cwd=working_dir,
                env=process_env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            # Store process and initialize output tracking
            self.active_processes[process_id] = process
            self.process_outputs[process_id] = []
            self.process_locks[process_id] = threading.Lock()
            
            # Start output collection thread
            output_thread = threading.Thread(
                target=self._collect_process_output,
                args=(process_id, process),
                daemon=True
            )
            output_thread.start()
            
            return {
                "success": True,
                "process_id": process_id,
                "command": command,
                "working_directory": str(working_dir),
                "pid": process.pid
            }
            
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "working_directory": str(working_dir)
            }
    
    def _collect_process_output(self, process_id: str, process: subprocess.Popen) -> None:
        """Collect output from a running process in a separate thread"""
        try:
            while process.poll() is None:
                # Read stdout
                if process.stdout:
                    line = process.stdout.readline()
                    if line:
                        with self.process_locks[process_id]:
                            self.process_outputs[process_id].append({
                                "type": "stdout",
                                "content": line.rstrip(),
                                "timestamp": asyncio.get_event_loop().time()
                            })
                
                # Read stderr
                if process.stderr:
                    line = process.stderr.readline()
                    if line:
                        with self.process_locks[process_id]:
                            self.process_outputs[process_id].append({
                                "type": "stderr",
                                "content": line.rstrip(),
                                "timestamp": asyncio.get_event_loop().time()
                            })
                
                # Small delay to prevent excessive CPU usage
                threading.Event().wait(0.01)
            
            # Process has terminated, read remaining output
            if process.stdout:
                remaining_stdout = process.stdout.read()
                if remaining_stdout:
                    with self.process_locks[process_id]:
                        self.process_outputs[process_id].append({
                            "type": "stdout",
                            "content": remaining_stdout.rstrip(),
                            "timestamp": asyncio.get_event_loop().time()
                        })
            
            if process.stderr:
                remaining_stderr = process.stderr.read()
                if remaining_stderr:
                    with self.process_locks[process_id]:
                        self.process_outputs[process_id].append({
                            "type": "stderr",
                            "content": remaining_stderr.rstrip(),
                            "timestamp": asyncio.get_event_loop().time()
                        })
            
            # Add process termination message
            with self.process_locks[process_id]:
                self.process_outputs[process_id].append({
                    "type": "process_exit",
                    "content": f"Process exited with code {process.returncode}",
                    "exit_code": process.returncode,
                    "timestamp": asyncio.get_event_loop().time()
                })
            
        except Exception as e:
            self.logger.error(f"Error collecting output for process {process_id}: {e}")
            with self.process_locks[process_id]:
                self.process_outputs[process_id].append({
                    "type": "error",
                    "content": f"Error collecting output: {str(e)}",
                    "timestamp": asyncio.get_event_loop().time()
                })
    
    async def send_input_to_process(self, process_id: str, input_data: str) -> Dict[str, Any]:
        """Send input to an interactive process"""
        if process_id not in self.active_processes:
            return {"error": f"Process not found: {process_id}"}
        
        process = self.active_processes[process_id]
        
        if process.poll() is not None:
            return {"error": f"Process has already terminated: {process_id}"}
        
        try:
            process.stdin.write(input_data + "\n")
            process.stdin.flush()
            
            return {
                "success": True,
                "process_id": process_id,
                "input_sent": input_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "process_id": process_id,
                "error": str(e)
            }
    
    async def get_process_output(self, process_id: str) -> Dict[str, Any]:
        """Get output from an interactive process"""
        if process_id not in self.active_processes:
            return {"error": f"Process not found: {process_id}"}
        
        with self.process_locks[process_id]:
            output_lines = self.process_outputs[process_id].copy()
            self.process_outputs[process_id].clear()  # Clear after reading
        
        process = self.active_processes[process_id]
        
        return {
            "success": True,
            "process_id": process_id,
            "output": output_lines,
            "is_running": process.poll() is None,
            "exit_code": process.returncode if process.poll() is not None else None
        }
    
    async def terminate_process(self, process_id: str) -> Dict[str, Any]:
        """Terminate an interactive process"""
        if process_id not in self.active_processes:
            return {"error": f"Process not found: {process_id}"}
        
        process = self.active_processes[process_id]
        
        try:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            
            # Clean up
            del self.active_processes[process_id]
            if process_id in self.process_outputs:
                del self.process_outputs[process_id]
            if process_id in self.process_locks:
                del self.process_locks[process_id]
            
            return {
                "success": True,
                "process_id": process_id,
                "exit_code": process.returncode
            }
            
        except Exception as e:
            return {
                "success": False,
                "process_id": process_id,
                "error": str(e)
            }
    
    async def list_active_processes(self) -> Dict[str, Any]:
        """List all active processes"""
        processes = []
        
        for process_id, process in self.active_processes.items():
            processes.append({
                "process_id": process_id,
                "pid": process.pid,
                "is_running": process.poll() is None,
                "exit_code": process.returncode if process.poll() is not None else None
            })
        
        return {
            "success": True,
            "processes": processes,
            "count": len(processes)
        }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            import platform
            import psutil
            
            return {
                "success": True,
                "system": {
                    "platform": platform.platform(),
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "python_version": platform.python_version(),
                    "cpu_count": psutil.cpu_count(),
                    "memory_total": psutil.virtual_memory().total,
                    "memory_available": psutil.virtual_memory().available,
                    "disk_usage": {
                        "total": psutil.disk_usage('/').total,
                        "used": psutil.disk_usage('/').used,
                        "free": psutil.disk_usage('/').free
                    }
                }
            }
            
        except ImportError:
            # Fallback if psutil is not available
            import platform
            
            return {
                "success": True,
                "system": {
                    "platform": platform.platform(),
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "python_version": platform.python_version()
                }
            }
    
    async def change_directory(self, path: str) -> Dict[str, Any]:
        """Change working directory"""
        try:
            new_path = Path(path).resolve()
            
            if not new_path.exists():
                return {"error": f"Directory does not exist: {path}"}
            
            if not new_path.is_dir():
                return {"error": f"Path is not a directory: {path}"}
            
            # Update workspace directory
            self.workspace_dir = new_path
            
            return {
                "success": True,
                "new_directory": str(new_path)
            }
            
        except Exception as e:
            return {"error": f"Failed to change directory: {str(e)}"}
    
    async def get_working_directory(self) -> Dict[str, Any]:
        """Get current working directory"""
        return {
            "success": True,
            "working_directory": str(self.workspace_dir)
        }
    
    def _get_working_directory(self, cwd: Optional[str] = None) -> Path:
        """Get the working directory for command execution"""
        if cwd:
            path = Path(cwd).resolve()
            if path.exists() and path.is_dir():
                return path
        return self.workspace_dir