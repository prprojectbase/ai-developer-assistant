import os
import asyncio
import aiofiles
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import shutil
import json
import mimetypes

from ..config.settings import get_settings
from ..utils.cache import cache_manager, cached


class FileOperations:
    """File operations module for the AI Developer Assistant"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.workspace_dir = Path(self.settings.workspace_dir)
        
    async def initialize(self) -> None:
        """Initialize the file operations module"""
        self.logger.info("Initializing File Operations module...")
        
        # Ensure workspace directory exists
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize cache manager
        await cache_manager.initialize()
        
        self.logger.info("File Operations module initialized")
    
    async def stop(self) -> None:
        """Stop the file operations module"""
        self.logger.info("Stopping File Operations module...")
        
        # Stop cache manager
        await cache_manager.stop()
        
        self.logger.info("File Operations module stopped")
    
    async def execute_operation(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a file operation"""
        operation_type = operation.get("type")
        
        try:
            if operation_type == "read_file":
                return await self.read_file(operation["path"])
            
            elif operation_type == "write_file":
                return await self.write_file(operation["path"], operation["content"])
            
            elif operation_type == "create_file":
                return await self.create_file(operation["path"], operation.get("content", ""))
            
            elif operation_type == "delete_file":
                return await self.delete_file(operation["path"])
            
            elif operation_type == "list_directory":
                return await self.list_directory(operation["path"])
            
            elif operation_type == "create_directory":
                return await self.create_directory(operation["path"])
            
            elif operation_type == "delete_directory":
                return await self.delete_directory(operation["path"])
            
            elif operation_type == "copy_file":
                return await self.copy_file(operation["source"], operation["destination"])
            
            elif operation_type == "move_file":
                return await self.move_file(operation["source"], operation["destination"])
            
            elif operation_type == "file_exists":
                return await self.file_exists(operation["path"])
            
            elif operation_type == "get_file_info":
                return await self.get_file_info(operation["path"])
            
            elif operation_type == "search_files":
                return await self.search_files(operation["pattern"], operation.get("directory", "."))
            
            elif operation_type == "read_directory_tree":
                return await self.read_directory_tree(operation["path"])
            
            else:
                return {"error": f"Unknown operation type: {operation_type}"}
                
        except Exception as e:
            self.logger.error(f"Error executing file operation {operation_type}: {e}")
            return {"error": str(e)}
    
    async def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read a file's contents"""
        full_path = self._get_full_path(file_path)
        
        # Generate cache key
        cache_key = f"file_read:{full_path}:{full_path.stat().st_mtime if full_path.exists() else 0}"
        
        # Try to get from cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        if not full_path.exists():
            return {"error": f"File not found: {file_path}"}
        
        if not full_path.is_file():
            return {"error": f"Path is not a file: {file_path}"}
        
        # Check file size
        file_size = full_path.stat().st_size
        if file_size > self.settings.max_file_size:
            return {"error": f"File too large: {file_size} bytes"}
        
        try:
            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            result = {
                "success": True,
                "content": content,
                "size": file_size,
                "path": file_path
            }
            
            # Cache the result (with 5 minute TTL)
            await cache_manager.set(cache_key, result, ttl=300)
            
            return result
            
        except UnicodeDecodeError:
            # Try reading as binary
            async with aiofiles.open(full_path, 'rb') as f:
                content = await f.read()
            
            result = {
                "success": True,
                "content": content.hex(),  # Return hex representation
                "size": file_size,
                "path": file_path,
                "binary": True
            }
            
            # Cache the result (with 5 minute TTL)
            await cache_manager.set(cache_key, result, ttl=300)
            
            return result
    
    async def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Write content to a file"""
        full_path = self._get_full_path(file_path)
        
        # Create parent directories if they don't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            # Invalidate cache for this file
            cache_key = f"file_read:{full_path}:{full_path.stat().st_mtime}"
            await cache_manager.delete(cache_key)
            
            return {
                "success": True,
                "path": file_path,
                "size": len(content)
            }
            
        except Exception as e:
            return {"error": f"Failed to write file: {str(e)}"}
    
    async def create_file(self, file_path: str, content: str = "") -> Dict[str, Any]:
        """Create a new file with optional content"""
        full_path = self._get_full_path(file_path)
        
        if full_path.exists():
            return {"error": f"File already exists: {file_path}"}
        
        return await self.write_file(file_path, content)
    
    async def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Delete a file"""
        full_path = self._get_full_path(file_path)
        
        if not full_path.exists():
            return {"error": f"File not found: {file_path}"}
        
        if not full_path.is_file():
            return {"error": f"Path is not a file: {file_path}"}
        
        try:
            full_path.unlink()
            return {"success": True, "path": file_path}
            
        except Exception as e:
            return {"error": f"Failed to delete file: {str(e)}"}
    
    async def list_directory(self, dir_path: str) -> Dict[str, Any]:
        """List contents of a directory"""
        full_path = self._get_full_path(dir_path)
        
        # Generate cache key
        cache_key = f"dir_list:{full_path}"
        
        # Try to get from cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        if not full_path.exists():
            return {"error": f"Directory not found: {dir_path}"}
        
        if not full_path.is_dir():
            return {"error": f"Path is not a directory: {dir_path}"}
        
        try:
            items = []
            for item in full_path.iterdir():
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "path": str(item.relative_to(self.workspace_dir)),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "created": stat.st_ctime
                })
            
            result = {
                "success": True,
                "path": dir_path,
                "items": sorted(items, key=lambda x: x["name"])
            }
            
            # Cache the result (with 1 minute TTL)
            await cache_manager.set(cache_key, result, ttl=60)
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to list directory: {str(e)}"}
    
    async def create_directory(self, dir_path: str) -> Dict[str, Any]:
        """Create a new directory"""
        full_path = self._get_full_path(dir_path)
        
        if full_path.exists():
            return {"error": f"Directory already exists: {dir_path}"}
        
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            return {"success": True, "path": dir_path}
            
        except Exception as e:
            return {"error": f"Failed to create directory: {str(e)}"}
    
    async def delete_directory(self, dir_path: str) -> Dict[str, Any]:
        """Delete a directory"""
        full_path = self._get_full_path(dir_path)
        
        if not full_path.exists():
            return {"error": f"Directory not found: {dir_path}"}
        
        if not full_path.is_dir():
            return {"error": f"Path is not a directory: {dir_path}"}
        
        try:
            shutil.rmtree(full_path)
            return {"success": True, "path": dir_path}
            
        except Exception as e:
            return {"error": f"Failed to delete directory: {str(e)}"}
    
    async def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy a file from source to destination"""
        source_path = self._get_full_path(source)
        dest_path = self._get_full_path(destination)
        
        if not source_path.exists():
            return {"error": f"Source file not found: {source}"}
        
        if not source_path.is_file():
            return {"error": f"Source path is not a file: {source}"}
        
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dest_path)
            
            return {
                "success": True,
                "source": source,
                "destination": destination
            }
            
        except Exception as e:
            return {"error": f"Failed to copy file: {str(e)}"}
    
    async def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Move a file from source to destination"""
        source_path = self._get_full_path(source)
        dest_path = self._get_full_path(destination)
        
        if not source_path.exists():
            return {"error": f"Source file not found: {source}"}
        
        if not source_path.is_file():
            return {"error": f"Source path is not a file: {source}"}
        
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(dest_path))
            
            return {
                "success": True,
                "source": source,
                "destination": destination
            }
            
        except Exception as e:
            return {"error": f"Failed to move file: {str(e)}"}
    
    async def file_exists(self, file_path: str) -> Dict[str, Any]:
        """Check if a file exists"""
        full_path = self._get_full_path(file_path)
        
        return {
            "success": True,
            "exists": full_path.exists(),
            "is_file": full_path.is_file() if full_path.exists() else False,
            "is_directory": full_path.is_dir() if full_path.exists() else False,
            "path": file_path
        }
    
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get detailed information about a file"""
        full_path = self._get_full_path(file_path)
        
        if not full_path.exists():
            return {"error": f"File not found: {file_path}"}
        
        try:
            stat = full_path.stat()
            mime_type, _ = mimetypes.guess_type(str(full_path))
            
            return {
                "success": True,
                "path": file_path,
                "name": full_path.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "is_file": full_path.is_file(),
                "is_directory": full_path.is_dir(),
                "mime_type": mime_type,
                "permissions": oct(stat.st_mode)[-3:]
            }
            
        except Exception as e:
            return {"error": f"Failed to get file info: {str(e)}"}
    
    async def search_files(self, pattern: str, directory: str = ".") -> Dict[str, Any]:
        """Search for files matching a pattern"""
        search_dir = self._get_full_path(directory)
        
        if not search_dir.exists():
            return {"error": f"Directory not found: {directory}"}
        
        if not search_dir.is_dir():
            return {"error": f"Path is not a directory: {directory}"}
        
        try:
            matches = []
            for item in search_dir.rglob(pattern):
                if item.is_file():
                    matches.append({
                        "path": str(item.relative_to(self.workspace_dir)),
                        "name": item.name,
                        "size": item.stat().st_size
                    })
            
            return {
                "success": True,
                "pattern": pattern,
                "directory": directory,
                "matches": matches
            }
            
        except Exception as e:
            return {"error": f"Failed to search files: {str(e)}"}
    
    async def read_directory_tree(self, dir_path: str) -> Dict[str, Any]:
        """Read directory structure as a tree"""
        full_path = self._get_full_path(dir_path)
        
        if not full_path.exists():
            return {"error": f"Directory not found: {dir_path}"}
        
        if not full_path.is_dir():
            return {"error": f"Path is not a directory: {dir_path}"}
        
        try:
            def build_tree(path: Path, base_path: Path) -> Dict[str, Any]:
                """Recursively build directory tree"""
                tree = {
                    "name": path.name,
                    "path": str(path.relative_to(base_path)),
                    "type": "directory",
                    "children": []
                }
                
                if path.is_file():
                    tree["type"] = "file"
                    tree["size"] = path.stat().st_size
                else:
                    for child in sorted(path.iterdir()):
                        tree["children"].append(build_tree(child, base_path))
                
                return tree
            
            tree = build_tree(full_path, self.workspace_dir)
            
            return {
                "success": True,
                "path": dir_path,
                "tree": tree
            }
            
        except Exception as e:
            return {"error": f"Failed to read directory tree: {str(e)}"}
    
    def _get_full_path(self, path: str) -> Path:
        """Get full path within workspace"""
        # Prevent path traversal attacks
        if ".." in path or path.startswith("/"):
            raise ValueError(f"Invalid path: {path}")
        
        return self.workspace_dir / path