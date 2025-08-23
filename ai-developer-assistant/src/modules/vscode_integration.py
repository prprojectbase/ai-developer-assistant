import asyncio
import json
import logging
import os
import subprocess
import tempfile
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
import aiohttp
import aiofiles
import websockets
from websockets.client import WebSocketClientProtocol

from ..config.settings import get_settings


class VSCodeIntegration:
    """VS Code local IDE integration for the AI Developer Assistant"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # VS Code configuration
        self.vscode_path = self._find_vscode_path()
        self.port = self.settings.vscode_port
        self.host = self.settings.vscode_host
        
        # Extension and API
        self.extension_installed = False
        self.websocket_client: Optional[WebSocketClientProtocol] = None
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # Workspace management
        self.current_workspace: Optional[str] = None
        self.open_files: List[str] = []
        self.active_editor: Optional[str] = None
        
        # Commands and operations
        self.available_commands: List[Dict[str, Any]] = []
        self.command_history: List[Dict[str, Any]] = []
        
    async def initialize(self) -> None:
        """Initialize the VS Code integration"""
        self.logger.info("Initializing VS Code integration...")
        
        # Create HTTP session
        self.http_session = aiohttp.ClientSession()
        
        # Check if VS Code is available
        if not self.vscode_path:
            self.logger.warning("VS Code not found in system")
            return
        
        # Check if extension is installed
        await self._check_extension_installed()
        
        # Try to connect to VS Code
        await self._connect_to_vscode()
        
        self.logger.info("VS Code integration initialized")
    
    async def stop(self) -> None:
        """Stop the VS Code integration"""
        self.logger.info("Stopping VS Code integration...")
        
        # Close WebSocket connection
        if self.websocket_client:
            await self.websocket_client.close()
            self.websocket_client = None
        
        # Close HTTP session
        if self.http_session:
            await self.http_session.close()
        
        self.logger.info("VS Code integration stopped")
    
    async def execute_operation(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a VS Code operation"""
        operation_type = operation.get("type")
        
        try:
            if operation_type == "open_file":
                return await self.open_file(operation["file_path"])
            
            elif operation_type == "close_file":
                return await self.close_file(operation["file_path"])
            
            elif operation_type == "save_file":
                return await self.save_file(operation["file_path"], operation.get("content"))
            
            elif operation_type == "get_file_content":
                return await self.get_file_content(operation["file_path"])
            
            elif operation_type == "create_file":
                return await self.create_file(operation["file_path"], operation.get("content", ""))
            
            elif operation_type == "delete_file":
                return await self.delete_file(operation["file_path"])
            
            elif operation_type == "list_files":
                return await self.list_files(operation.get("directory", "."))
            
            elif operation_type == "search_in_files":
                return await self.search_in_files(
                    operation["pattern"],
                    operation.get("directory", "."),
                    operation.get("file_pattern")
                )
            
            elif operation_type == "execute_command":
                return await self.execute_vscode_command(
                    operation["command"],
                    operation.get("args", [])
                )
            
            elif operation_type == "get_available_commands":
                return await self.get_available_commands()
            
            elif operation_type == "open_workspace":
                return await self.open_workspace(operation["workspace_path"])
            
            elif operation_type == "get_workspace_info":
                return await self.get_workspace_info()
            
            elif operation_type == "get_diagnostics":
                return await self.get_diagnostics(operation.get("file_path"))
            
            elif operation_type == "get_symbols":
                return await self.get_symbols(operation["file_path"])
            
            elif operation_type == "format_document":
                return await self.format_document(operation["file_path"])
            
            elif operation_type == "run_terminal_command":
                return await self.run_terminal_command(
                    operation["command"],
                    operation.get("cwd"),
                    operation.get("terminal_name")
                )
            
            elif operation_type == "get_terminal_output":
                return await self.get_terminal_output(operation.get("terminal_name"))
            
            elif operation_type == "create_terminal":
                return await self.create_terminal(operation.get("terminal_name"))
            
            elif operation_type == "show_message":
                return await self.show_message(
                    operation["message"],
                    operation.get("type", "info")
                )
            
            elif operation_type == "show_input_box":
                return await self.show_input_box(
                    operation.get("prompt", "Enter value:"),
                    operation.get("default_value", "")
                )
            
            elif operation_type == "show_quick_pick":
                return await self.show_quick_pick(
                    operation["items"],
                    operation.get("placeholder", "Select an item:")
                )
            
            elif operation_type == "set_status_bar_message":
                return await self.set_status_bar_message(
                    operation["message"],
                    operation.get("timeout", 5000)
                )
            
            elif operation_type == "get_configuration":
                return await self.get_configuration(
                    operation["section"],
                    operation.get("scope")
                )
            
            elif operation_type == "update_configuration":
                return await self.update_configuration(
                    operation["section"],
                    operation["value"],
                    operation.get("scope")
                )
            
            elif operation_type == "install_extension":
                return await self.install_extension(operation["extension_id"])
            
            elif operation_type == "uninstall_extension":
                return await self.uninstall_extension(operation["extension_id"])
            
            elif operation_type == "get_installed_extensions":
                return await self.get_installed_extensions()
            
            elif operation_type == "start_debugging":
                return await self.start_debugging(
                    operation.get("configuration", {}),
                    operation.get("folder")
                )
            
            elif operation_type == "stop_debugging":
                return await self.stop_debugging()
            
            elif operation_type == "get_debug_sessions":
                return await self.get_debug_sessions()
            
            else:
                return {"error": f"Unknown operation type: {operation_type}"}
                
        except Exception as e:
            self.logger.error(f"Error executing VS Code operation {operation_type}: {e}")
            return {"error": str(e)}
    
    async def open_file(self, file_path: str) -> Dict[str, Any]:
        """Open a file in VS Code"""
        if not self.vscode_path:
            return {"error": "VS Code not available"}
        
        try:
            # Use VS Code CLI to open file
            result = subprocess.run(
                [self.vscode_path, "--new-window", "--reuse-window", file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.open_files.append(file_path)
                self.active_editor = file_path
                
                return {
                    "success": True,
                    "file_path": file_path,
                    "message": "File opened successfully"
                }
            else:
                return {"error": f"Failed to open file: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            return {"error": "Timeout opening file"}
        except Exception as e:
            return {"error": f"Error opening file: {str(e)}"}
    
    async def close_file(self, file_path: str) -> Dict[str, Any]:
        """Close a file in VS Code"""
        try:
            if self.websocket_client:
                # Send close command via WebSocket
                command = {
                    "type": "close_file",
                    "file_path": file_path
                }
                await self.websocket_client.send(json.dumps(command))
                
                if file_path in self.open_files:
                    self.open_files.remove(file_path)
                
                if self.active_editor == file_path:
                    self.active_editor = self.open_files[0] if self.open_files else None
                
                return {
                    "success": True,
                    "file_path": file_path,
                    "message": "File closed successfully"
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error closing file: {str(e)}"}
    
    async def save_file(self, file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Save a file in VS Code"""
        try:
            if content:
                # Write content to file
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(content)
            
            if self.websocket_client:
                # Send save command via WebSocket
                command = {
                    "type": "save_file",
                    "file_path": file_path
                }
                await self.websocket_client.send(json.dumps(command))
            
            return {
                "success": True,
                "file_path": file_path,
                "message": "File saved successfully"
            }
            
        except Exception as e:
            return {"error": f"Error saving file: {str(e)}"}
    
    async def get_file_content(self, file_path: str) -> Dict[str, Any]:
        """Get content of a file"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            return {
                "success": True,
                "file_path": file_path,
                "content": content,
                "size": len(content)
            }
            
        except FileNotFoundError:
            return {"error": f"File not found: {file_path}"}
        except Exception as e:
            return {"error": f"Error reading file: {str(e)}"}
    
    async def create_file(self, file_path: str, content: str = "") -> Dict[str, Any]:
        """Create a new file"""
        try:
            # Create parent directories if they don't exist
            parent_dir = Path(file_path).parent
            parent_dir.mkdir(parents=True, exist_ok=True)
            
            # Write content to file
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            # Open the file in VS Code
            await self.open_file(file_path)
            
            return {
                "success": True,
                "file_path": file_path,
                "message": "File created successfully"
            }
            
        except Exception as e:
            return {"error": f"Error creating file: {str(e)}"}
    
    async def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Delete a file"""
        try:
            Path(file_path).unlink()
            
            if file_path in self.open_files:
                self.open_files.remove(file_path)
            
            if self.active_editor == file_path:
                self.active_editor = self.open_files[0] if self.open_files else None
            
            return {
                "success": True,
                "file_path": file_path,
                "message": "File deleted successfully"
            }
            
        except FileNotFoundError:
            return {"error": f"File not found: {file_path}"}
        except Exception as e:
            return {"error": f"Error deleting file: {str(e)}"}
    
    async def list_files(self, directory: str = ".") -> Dict[str, Any]:
        """List files in a directory"""
        try:
            files = []
            dir_path = Path(directory)
            
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            
            for item in dir_path.iterdir():
                if item.is_file():
                    files.append({
                        "name": item.name,
                        "path": str(item),
                        "size": item.stat().st_size,
                        "modified": item.stat().st_mtime
                    })
            
            return {
                "success": True,
                "directory": directory,
                "files": sorted(files, key=lambda x: x["name"])
            }
            
        except Exception as e:
            return {"error": f"Error listing files: {str(e)}"}
    
    async def search_in_files(self, pattern: str, directory: str = ".", 
                            file_pattern: Optional[str] = None) -> Dict[str, Any]:
        """Search for a pattern in files"""
        try:
            results = []
            dir_path = Path(directory)
            
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            
            # Use ripgrep if available, otherwise fall back to Python
            try:
                # Try to use ripgrep for faster search
                cmd = ["rg", pattern, str(dir_path), "--json"]
                if file_pattern:
                    cmd.extend(["-g", file_pattern])
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            match_data = json.loads(line)
                            results.append({
                                "file": match_data["data"]["path"]["text"],
                                "line": match_data["data"]["line_number"],
                                "content": match_data["data"]["lines"]["text"]
                            })
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                # Fall back to Python search
                import re
                
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        if file_pattern and not file_path.match(file_pattern):
                            continue
                        
                        try:
                            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                                content = await f.read()
                            
                            lines = content.split('\n')
                            for line_num, line in enumerate(lines, 1):
                                if re.search(pattern, line):
                                    results.append({
                                        "file": str(file_path),
                                        "line": line_num,
                                        "content": line
                                    })
                        except Exception:
                            continue
            
            return {
                "success": True,
                "pattern": pattern,
                "directory": directory,
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            return {"error": f"Error searching files: {str(e)}"}
    
    async def execute_vscode_command(self, command: str, args: List[Any] = []) -> Dict[str, Any]:
        """Execute a VS Code command"""
        try:
            if self.websocket_client:
                # Send command via WebSocket
                command_data = {
                    "type": "execute_command",
                    "command": command,
                    "args": args
                }
                await self.websocket_client.send(json.dumps(command_data))
                
                # Add to command history
                self.command_history.append({
                    "command": command,
                    "args": args,
                    "timestamp": datetime.now().isoformat()
                })
                
                return {
                    "success": True,
                    "command": command,
                    "args": args,
                    "message": "Command executed successfully"
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error executing command: {str(e)}"}
    
    async def get_available_commands(self) -> Dict[str, Any]:
        """Get list of available VS Code commands"""
        try:
            if self.websocket_client:
                # Request commands via WebSocket
                command = {"type": "get_commands"}
                await self.websocket_client.send(json.dumps(command))
                
                # Wait for response (simplified)
                response = await self.websocket_client.recv()
                commands_data = json.loads(response)
                
                self.available_commands = commands_data.get("commands", [])
                
                return {
                    "success": True,
                    "commands": self.available_commands,
                    "count": len(self.available_commands)
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error getting commands: {str(e)}"}
    
    async def open_workspace(self, workspace_path: str) -> Dict[str, Any]:
        """Open a workspace in VS Code"""
        if not self.vscode_path:
            return {"error": "VS Code not available"}
        
        try:
            # Use VS Code CLI to open workspace
            result = subprocess.run(
                [self.vscode_path, "--new-window", workspace_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.current_workspace = workspace_path
                
                return {
                    "success": True,
                    "workspace_path": workspace_path,
                    "message": "Workspace opened successfully"
                }
            else:
                return {"error": f"Failed to open workspace: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            return {"error": "Timeout opening workspace"}
        except Exception as e:
            return {"error": f"Error opening workspace: {str(e)}"}
    
    async def get_workspace_info(self) -> Dict[str, Any]:
        """Get current workspace information"""
        try:
            info = {
                "workspace_path": self.current_workspace,
                "open_files": self.open_files,
                "active_editor": self.active_editor,
                "vscode_available": bool(self.vscode_path),
                "extension_installed": self.extension_installed,
                "websocket_connected": bool(self.websocket_client)
            }
            
            return {
                "success": True,
                "workspace_info": info
            }
            
        except Exception as e:
            return {"error": f"Error getting workspace info: {str(e)}"}
    
    async def get_diagnostics(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Get diagnostic information"""
        try:
            if self.websocket_client:
                # Request diagnostics via WebSocket
                command = {
                    "type": "get_diagnostics",
                    "file_path": file_path
                }
                await self.websocket_client.send(json.dumps(command))
                
                # Wait for response (simplified)
                response = await self.websocket_client.recv()
                diagnostics_data = json.loads(response)
                
                return {
                    "success": True,
                    "diagnostics": diagnostics_data.get("diagnostics", []),
                    "file_path": file_path
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error getting diagnostics: {str(e)}"}
    
    async def get_symbols(self, file_path: str) -> Dict[str, Any]:
        """Get symbols in a file"""
        try:
            if self.websocket_client:
                # Request symbols via WebSocket
                command = {
                    "type": "get_symbols",
                    "file_path": file_path
                }
                await self.websocket_client.send(json.dumps(command))
                
                # Wait for response (simplified)
                response = await self.websocket_client.recv()
                symbols_data = json.loads(response)
                
                return {
                    "success": True,
                    "symbols": symbols_data.get("symbols", []),
                    "file_path": file_path
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error getting symbols: {str(e)}"}
    
    async def format_document(self, file_path: str) -> Dict[str, Any]:
        """Format a document"""
        try:
            if self.websocket_client:
                # Send format command via WebSocket
                command = {
                    "type": "format_document",
                    "file_path": file_path
                }
                await self.websocket_client.send(json.dumps(command))
                
                return {
                    "success": True,
                    "file_path": file_path,
                    "message": "Document formatted successfully"
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error formatting document: {str(e)}"}
    
    async def run_terminal_command(self, command: str, cwd: Optional[str] = None,
                                 terminal_name: Optional[str] = None) -> Dict[str, Any]:
        """Run a command in the terminal"""
        try:
            if self.websocket_client:
                # Send terminal command via WebSocket
                command_data = {
                    "type": "run_terminal_command",
                    "command": command,
                    "cwd": cwd,
                    "terminal_name": terminal_name
                }
                await self.websocket_client.send(json.dumps(command_data))
                
                return {
                    "success": True,
                    "command": command,
                    "cwd": cwd,
                    "terminal_name": terminal_name,
                    "message": "Terminal command executed"
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error running terminal command: {str(e)}"}
    
    async def get_terminal_output(self, terminal_name: Optional[str] = None) -> Dict[str, Any]:
        """Get terminal output"""
        try:
            if self.websocket_client:
                # Request terminal output via WebSocket
                command = {
                    "type": "get_terminal_output",
                    "terminal_name": terminal_name
                }
                await self.websocket_client.send(json.dumps(command))
                
                # Wait for response (simplified)
                response = await self.websocket_client.recv()
                output_data = json.loads(response)
                
                return {
                    "success": True,
                    "output": output_data.get("output", ""),
                    "terminal_name": terminal_name
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error getting terminal output: {str(e)}"}
    
    async def create_terminal(self, terminal_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new terminal"""
        try:
            if self.websocket_client:
                # Send create terminal command via WebSocket
                command = {
                    "type": "create_terminal",
                    "terminal_name": terminal_name
                }
                await self.websocket_client.send(json.dumps(command))
                
                return {
                    "success": True,
                    "terminal_name": terminal_name,
                    "message": "Terminal created successfully"
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error creating terminal: {str(e)}"}
    
    async def show_message(self, message: str, message_type: str = "info") -> Dict[str, Any]:
        """Show a message in VS Code"""
        try:
            if self.websocket_client:
                # Send message via WebSocket
                command = {
                    "type": "show_message",
                    "message": message,
                    "message_type": message_type
                }
                await self.websocket_client.send(json.dumps(command))
                
                return {
                    "success": True,
                    "message": message,
                    "message_type": message_type
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error showing message: {str(e)}"}
    
    async def show_input_box(self, prompt: str = "Enter value:", 
                           default_value: str = "") -> Dict[str, Any]:
        """Show an input box in VS Code"""
        try:
            if self.websocket_client:
                # Send input box command via WebSocket
                command = {
                    "type": "show_input_box",
                    "prompt": prompt,
                    "default_value": default_value
                }
                await self.websocket_client.send(json.dumps(command))
                
                # Wait for response (simplified)
                response = await self.websocket_client.recv()
                input_data = json.loads(response)
                
                return {
                    "success": True,
                    "value": input_data.get("value", ""),
                    "prompt": prompt
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error showing input box: {str(e)}"}
    
    async def show_quick_pick(self, items: List[str], 
                            placeholder: str = "Select an item:") -> Dict[str, Any]:
        """Show a quick pick dialog in VS Code"""
        try:
            if self.websocket_client:
                # Send quick pick command via WebSocket
                command = {
                    "type": "show_quick_pick",
                    "items": items,
                    "placeholder": placeholder
                }
                await self.websocket_client.send(json.dumps(command))
                
                # Wait for response (simplified)
                response = await self.websocket_client.recv()
                pick_data = json.loads(response)
                
                return {
                    "success": True,
                    "selected_item": pick_data.get("selected_item"),
                    "items": items,
                    "placeholder": placeholder
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error showing quick pick: {str(e)}"}
    
    async def set_status_bar_message(self, message: str, timeout: int = 5000) -> Dict[str, Any]:
        """Set status bar message"""
        try:
            if self.websocket_client:
                # Send status bar message via WebSocket
                command = {
                    "type": "set_status_bar_message",
                    "message": message,
                    "timeout": timeout
                }
                await self.websocket_client.send(json.dumps(command))
                
                return {
                    "success": True,
                    "message": message,
                    "timeout": timeout
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error setting status bar message: {str(e)}"}
    
    async def get_configuration(self, section: str, scope: Optional[str] = None) -> Dict[str, Any]:
        """Get VS Code configuration"""
        try:
            if self.websocket_client:
                # Request configuration via WebSocket
                command = {
                    "type": "get_configuration",
                    "section": section,
                    "scope": scope
                }
                await self.websocket_client.send(json.dumps(command))
                
                # Wait for response (simplified)
                response = await self.websocket_client.recv()
                config_data = json.loads(response)
                
                return {
                    "success": True,
                    "section": section,
                    "configuration": config_data.get("configuration", {}),
                    "scope": scope
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error getting configuration: {str(e)}"}
    
    async def update_configuration(self, section: str, value: Any, 
                                 scope: Optional[str] = None) -> Dict[str, Any]:
        """Update VS Code configuration"""
        try:
            if self.websocket_client:
                # Send configuration update via WebSocket
                command = {
                    "type": "update_configuration",
                    "section": section,
                    "value": value,
                    "scope": scope
                }
                await self.websocket_client.send(json.dumps(command))
                
                return {
                    "success": True,
                    "section": section,
                    "value": value,
                    "scope": scope,
                    "message": "Configuration updated successfully"
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error updating configuration: {str(e)}"}
    
    async def install_extension(self, extension_id: str) -> Dict[str, Any]:
        """Install a VS Code extension"""
        if not self.vscode_path:
            return {"error": "VS Code not available"}
        
        try:
            # Use VS Code CLI to install extension
            result = subprocess.run(
                [self.vscode_path, "--install-extension", extension_id],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "extension_id": extension_id,
                    "message": "Extension installed successfully"
                }
            else:
                return {"error": f"Failed to install extension: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            return {"error": "Timeout installing extension"}
        except Exception as e:
            return {"error": f"Error installing extension: {str(e)}"}
    
    async def uninstall_extension(self, extension_id: str) -> Dict[str, Any]:
        """Uninstall a VS Code extension"""
        if not self.vscode_path:
            return {"error": "VS Code not available"}
        
        try:
            # Use VS Code CLI to uninstall extension
            result = subprocess.run(
                [self.vscode_path, "--uninstall-extension", extension_id],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "extension_id": extension_id,
                    "message": "Extension uninstalled successfully"
                }
            else:
                return {"error": f"Failed to uninstall extension: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            return {"error": "Timeout uninstalling extension"}
        except Exception as e:
            return {"error": f"Error uninstalling extension: {str(e)}"}
    
    async def get_installed_extensions(self) -> Dict[str, Any]:
        """Get list of installed extensions"""
        if not self.vscode_path:
            return {"error": "VS Code not available"}
        
        try:
            # Use VS Code CLI to list extensions
            result = subprocess.run(
                [self.vscode_path, "--list-extensions", "--show-versions"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                extensions = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('@')
                        if len(parts) == 2:
                            extensions.append({
                                "id": parts[0],
                                "version": parts[1]
                            })
                
                return {
                    "success": True,
                    "extensions": extensions,
                    "count": len(extensions)
                }
            else:
                return {"error": f"Failed to list extensions: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            return {"error": "Timeout listing extensions"}
        except Exception as e:
            return {"error": f"Error listing extensions: {str(e)}"}
    
    async def start_debugging(self, configuration: Dict[str, Any], 
                            folder: Optional[str] = None) -> Dict[str, Any]:
        """Start debugging session"""
        try:
            if self.websocket_client:
                # Send start debugging command via WebSocket
                command = {
                    "type": "start_debugging",
                    "configuration": configuration,
                    "folder": folder
                }
                await self.websocket_client.send(json.dumps(command))
                
                return {
                    "success": True,
                    "configuration": configuration,
                    "folder": folder,
                    "message": "Debugging session started"
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error starting debugging: {str(e)}"}
    
    async def stop_debugging(self) -> Dict[str, Any]:
        """Stop debugging session"""
        try:
            if self.websocket_client:
                # Send stop debugging command via WebSocket
                command = {"type": "stop_debugging"}
                await self.websocket_client.send(json.dumps(command))
                
                return {
                    "success": True,
                    "message": "Debugging session stopped"
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error stopping debugging: {str(e)}"}
    
    async def get_debug_sessions(self) -> Dict[str, Any]:
        """Get active debugging sessions"""
        try:
            if self.websocket_client:
                # Request debug sessions via WebSocket
                command = {"type": "get_debug_sessions"}
                await self.websocket_client.send(json.dumps(command))
                
                # Wait for response (simplified)
                response = await self.websocket_client.recv()
                debug_data = json.loads(response)
                
                return {
                    "success": True,
                    "sessions": debug_data.get("sessions", []),
                    "count": len(debug_data.get("sessions", []))
                }
            else:
                return {"error": "WebSocket connection not available"}
                
        except Exception as e:
            return {"error": f"Error getting debug sessions: {str(e)}"}
    
    def _find_vscode_path(self) -> Optional[str]:
        """Find VS Code executable path"""
        # Common VS Code paths
        possible_paths = [
            # Windows
            "C:\\Program Files\\Microsoft VS Code\\Code.exe",
            "C:\\Program Files (x86)\\Microsoft VS Code\\Code.exe",
            # macOS
            "/Applications/Visual Studio Code.app/Contents/MacOS/Electron",
            "/usr/local/bin/code",
            # Linux
            "/usr/bin/code",
            "/usr/local/bin/code",
            "/snap/bin/code"
        ]
        
        # Check if code is in PATH
        try:
            result = subprocess.run(["which", "code"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            pass
        
        # Check common paths
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    async def _check_extension_installed(self) -> None:
        """Check if the AI Assistant extension is installed"""
        try:
            extensions = await self.get_installed_extensions()
            if extensions.get("success"):
                for ext in extensions["extensions"]:
                    if ext["id"] == "ai-developer-assistant.assistant":
                        self.extension_installed = True
                        break
        except Exception:
            pass
    
    async def _connect_to_vscode(self) -> None:
        """Connect to VS Code via WebSocket"""
        try:
            uri = f"ws://{self.host}:{self.port}"
            self.websocket_client = await websockets.connect(uri)
            self.logger.info(f"Connected to VS Code at {uri}")
        except Exception as e:
            self.logger.warning(f"Failed to connect to VS Code: {e}")
            self.websocket_client = None