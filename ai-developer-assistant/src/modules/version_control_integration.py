#!/usr/bin/env python3
"""
Version Control Integration Module

Provides comprehensive Git operations and version control management
for the AI Developer Assistant.
"""

import asyncio
import logging
import os
import subprocess
import json
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from ..config.settings import get_settings


@dataclass
class GitCommit:
    """Git commit information"""
    hash: str
    author: str
    email: str
    date: datetime
    message: str
    files_changed: List[str] = field(default_factory=list)
    insertions: int = 0
    deletions: int = 0


@dataclass
class GitBranch:
    """Git branch information"""
    name: str
    is_current: bool = False
    is_remote: bool = False
    commit_hash: str = ""
    last_commit_date: Optional[datetime] = None


@dataclass
class GitStatus:
    """Git repository status"""
    is_clean: bool = True
    staged_files: List[str] = field(default_factory=list)
    unstaged_files: List[str] = field(default_factory=list)
    untracked_files: List[str] = field(default_factory=list)
    branch: str = ""
    ahead: int = 0
    behind: int = 0


class VersionControlIntegration:
    """Version Control Integration for Git operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Git configuration
        self.git_path = "git"
        self.default_branch = "main"
        self.default_remote = "origin"
        
        # Repository state
        self.current_repo_path: Optional[str] = None
        self.repo_config: Dict[str, Any] = {}
        
        # Statistics
        self.stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "commits_created": 0,
            "branches_created": 0,
            "merges_performed": 0
        }
    
    async def initialize(self) -> None:
        """Initialize the version control integration"""
        self.logger.info("Initializing Version Control Integration...")
        
        # Check if git is available
        try:
            result = await self._run_git_command(["--version"])
            self.logger.info(f"Git version: {result.strip()}")
        except Exception as e:
            self.logger.error(f"Git not available: {e}")
            raise RuntimeError("Git is required for version control integration")
        
        # Create workspace directory if it doesn't exist
        workspace_dir = Path(self.settings.workspace_dir)
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Version Control Integration initialized successfully")
    
    async def stop(self) -> None:
        """Stop the version control integration"""
        self.logger.info("Stopping Version Control Integration...")
        self.logger.info("Version Control Integration stopped")
    
    async def initialize_repository(self, repo_path: str, init: bool = True) -> Dict[str, Any]:
        """Initialize or open a Git repository"""
        try:
            repo_path = str(Path(repo_path).absolute())
            
            # Create directory if it doesn't exist
            Path(repo_path).mkdir(parents=True, exist_ok=True)
            
            # Initialize repository if requested
            if init:
                git_dir = Path(repo_path) / ".git"
                if not git_dir.exists():
                    await self._run_git_command(["init"], cwd=repo_path)
                    self.logger.info(f"Initialized Git repository: {repo_path}")
            
            # Set current repository path
            self.current_repo_path = repo_path
            
            # Get repository configuration
            await self._load_repo_config(repo_path)
            
            # Set default branch name
            try:
                result = await self._run_git_command(["branch", "--show-current"], cwd=repo_path)
                self.default_branch = result.strip() or "main"
            except:
                self.default_branch = "main"
            
            return {
                "success": True,
                "repo_path": repo_path,
                "branch": self.default_branch,
                "is_initialized": True
            }
            
        except Exception as e:
            self.logger.error(f"Error initializing repository: {e}")
            return {"error": str(e)}
    
    async def clone_repository(self, url: str, destination: str, 
                             branch: Optional[str] = None) -> Dict[str, Any]:
        """Clone a Git repository"""
        try:
            destination = str(Path(destination).absolute())
            
            # Create parent directory if it doesn't exist
            Path(destination).parent.mkdir(parents=True, exist_ok=True)
            
            # Build clone command
            clone_cmd = ["clone"]
            if branch:
                clone_cmd.extend(["--branch", branch])
            clone_cmd.extend([url, destination])
            
            # Clone repository
            result = await self._run_git_command(clone_cmd)
            
            # Set current repository path
            self.current_repo_path = destination
            
            # Load repository configuration
            await self._load_repo_config(destination)
            
            return {
                "success": True,
                "repo_path": destination,
                "url": url,
                "branch": branch or self.default_branch,
                "output": result
            }
            
        except Exception as e:
            self.logger.error(f"Error cloning repository: {e}")
            return {"error": str(e)}
    
    async def add_files(self, files: Union[str, List[str]], 
                        repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Add files to staging area"""
        try:
            cwd = repo_path or self.current_repo_path
            if not cwd:
                return {"error": "No repository path specified"}
            
            if isinstance(files, str):
                files = [files]
            
            # Add files to staging area
            result = await self._run_git_command(["add"] + files, cwd=cwd)
            
            return {
                "success": True,
                "files_added": files,
                "output": result
            }
            
        except Exception as e:
            self.logger.error(f"Error adding files: {e}")
            return {"error": str(e)}
    
    async def commit_changes(self, message: str, files: Optional[List[str]] = None,
                           repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Commit changes to repository"""
        try:
            cwd = repo_path or self.current_repo_path
            if not cwd:
                return {"error": "No repository path specified"}
            
            # Add specific files if provided
            if files:
                await self.add_files(files, cwd)
            
            # Commit changes
            result = await self._run_git_command(["commit", "-m", message], cwd=cwd)
            
            # Update statistics
            self.stats["commits_created"] += 1
            
            return {
                "success": True,
                "message": message,
                "output": result
            }
            
        except Exception as e:
            self.logger.error(f"Error committing changes: {e}")
            return {"error": str(e)}
    
    async def push_changes(self, remote: Optional[str] = None, 
                          branch: Optional[str] = None,
                          repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Push changes to remote repository"""
        try:
            cwd = repo_path or self.current_repo_path
            if not cwd:
                return {"error": "No repository path specified"}
            
            remote = remote or self.default_remote
            branch = branch or self.default_branch
            
            # Push changes
            result = await self._run_git_command(["push", remote, branch], cwd=cwd)
            
            return {
                "success": True,
                "remote": remote,
                "branch": branch,
                "output": result
            }
            
        except Exception as e:
            self.logger.error(f"Error pushing changes: {e}")
            return {"error": str(e)}
    
    async def pull_changes(self, remote: Optional[str] = None,
                          branch: Optional[str] = None,
                          repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Pull changes from remote repository"""
        try:
            cwd = repo_path or self.current_repo_path
            if not cwd:
                return {"error": "No repository path specified"}
            
            remote = remote or self.default_remote
            branch = branch or self.default_branch
            
            # Pull changes
            result = await self._run_git_command(["pull", remote, branch], cwd=cwd)
            
            return {
                "success": True,
                "remote": remote,
                "branch": branch,
                "output": result
            }
            
        except Exception as e:
            self.logger.error(f"Error pulling changes: {e}")
            return {"error": str(e)}
    
    async def create_branch(self, branch_name: str, 
                           base_branch: Optional[str] = None,
                           repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Create a new branch"""
        try:
            cwd = repo_path or self.current_repo_path
            if not cwd:
                return {"error": "No repository path specified"}
            
            base_branch = base_branch or self.default_branch
            
            # Create and checkout new branch
            result = await self._run_git_command(
                ["checkout", "-b", branch_name, base_branch], 
                cwd=cwd
            )
            
            # Update statistics
            self.stats["branches_created"] += 1
            
            return {
                "success": True,
                "branch_name": branch_name,
                "base_branch": base_branch,
                "output": result
            }
            
        except Exception as e:
            self.logger.error(f"Error creating branch: {e}")
            return {"error": str(e)}
    
    async def switch_branch(self, branch_name: str,
                           repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Switch to a different branch"""
        try:
            cwd = repo_path or self.current_repo_path
            if not cwd:
                return {"error": "No repository path specified"}
            
            # Switch branch
            result = await self._run_git_command(["checkout", branch_name], cwd=cwd)
            
            # Update default branch
            self.default_branch = branch_name
            
            return {
                "success": True,
                "branch_name": branch_name,
                "output": result
            }
            
        except Exception as e:
            self.logger.error(f"Error switching branch: {e}")
            return {"error": str(e)}
    
    async def merge_branch(self, source_branch: str, target_branch: Optional[str] = None,
                          repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Merge a branch into another branch"""
        try:
            cwd = repo_path or self.current_repo_path
            if not cwd:
                return {"error": "No repository path specified"}
            
            target_branch = target_branch or self.default_branch
            
            # Switch to target branch
            await self.switch_branch(target_branch, cwd)
            
            # Merge source branch
            result = await self._run_git_command(["merge", source_branch], cwd=cwd)
            
            # Update statistics
            self.stats["merges_performed"] += 1
            
            return {
                "success": True,
                "source_branch": source_branch,
                "target_branch": target_branch,
                "output": result
            }
            
        except Exception as e:
            self.logger.error(f"Error merging branch: {e}")
            return {"error": str(e)}
    
    async def get_status(self, repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Get repository status"""
        try:
            cwd = repo_path or self.current_repo_path
            if not cwd:
                return {"error": "No repository path specified"}
            
            # Get git status
            result = await self._run_git_command(["status", "--porcelain"], cwd=cwd)
            
            # Parse status
            staged_files = []
            unstaged_files = []
            untracked_files = []
            
            for line in result.strip().split('\n'):
                if not line.strip():
                    continue
                
                status_code = line[:2]
                file_path = line[3:]
                
                if status_code == '??':
                    untracked_files.append(file_path)
                elif status_code[0] != ' ':
                    staged_files.append(file_path)
                elif status_code[1] != ' ':
                    unstaged_files.append(file_path)
            
            # Get current branch and ahead/behind info
            branch_info = await self._run_git_command(["status", "--branch", "--porcelain"], cwd=cwd)
            branch = ""
            ahead = 0
            behind = 0
            
            for line in branch_info.strip().split('\n'):
                if line.startswith("## "):
                    branch_info = line[3:]
                    if "..." in branch_info:
                        branch = branch_info.split("...")[0]
                        
                        # Parse ahead/behind info
                        if "[" in branch_info:
                            status_part = branch_info.split("[")[1].split("]")[0]
                            if "ahead " in status_part:
                                ahead = int(status_part.split("ahead ")[1].split(",")[0])
                            if "behind " in status_part:
                                behind = int(status_part.split("behind ")[1].split(",")[0])
                    else:
                        branch = branch_info
                    break
            
            status = GitStatus(
                is_clean=len(staged_files) == 0 and len(unstaged_files) == 0 and len(untracked_files) == 0,
                staged_files=staged_files,
                unstaged_files=unstaged_files,
                untracked_files=untracked_files,
                branch=branch,
                ahead=ahead,
                behind=behind
            )
            
            return {
                "success": True,
                "status": self._status_to_dict(status)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {"error": str(e)}
    
    async def get_log(self, limit: int = 10, repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Get commit history"""
        try:
            cwd = repo_path or self.current_repo_path
            if not cwd:
                return {"error": "No repository path specified"}
            
            # Get commit log
            result = await self._run_git_command([
                "log", f"--max-count={limit}",
                "--pretty=format:%H|%an|%ae|%ci|%s",
                "--numstat"
            ], cwd=cwd)
            
            commits = []
            current_commit = None
            
            for line in result.strip().split('\n'):
                if not line.strip():
                    continue
                
                if '|' in line and line.count('|') >= 3:
                    # This is a commit header
                    if current_commit:
                        commits.append(current_commit)
                    
                    parts = line.split('|')
                    current_commit = GitCommit(
                        hash=parts[0],
                        author=parts[1],
                        email=parts[2],
                        date=datetime.strptime(parts[3], "%Y-%m-%d %H:%M:%S %z"),
                        message=parts[4]
                    )
                elif current_commit and '\t' in line:
                    # This is a file change line
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        current_commit.files_changed.append(parts[2])
                        if parts[0].isdigit():
                            current_commit.insertions += int(parts[0])
                        if parts[1].isdigit():
                            current_commit.deletions += int(parts[1])
            
            # Add last commit
            if current_commit:
                commits.append(current_commit)
            
            return {
                "success": True,
                "commits": [self._commit_to_dict(commit) for commit in commits]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting log: {e}")
            return {"error": str(e)}
    
    async def get_branches(self, repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Get list of branches"""
        try:
            cwd = repo_path or self.current_repo_path
            if not cwd:
                return {"error": "No repository path specified"}
            
            # Get local branches
            local_result = await self._run_git_command(["branch", "-v"], cwd=cwd)
            local_branches = []
            
            for line in local_result.strip().split('\n'):
                if not line.strip():
                    continue
                
                is_current = line.startswith('* ')
                branch_name = line[2:].split()[0]
                commit_hash = line[2:].split()[1] if len(line[2:].split()) > 1 else ""
                
                local_branches.append(GitBranch(
                    name=branch_name,
                    is_current=is_current,
                    is_remote=False,
                    commit_hash=commit_hash
                ))
            
            # Get remote branches
            remote_result = await self._run_git_command(["branch", "-r", "-v"], cwd=cwd)
            remote_branches = []
            
            for line in remote_result.strip().split('\n'):
                if not line.strip():
                    continue
                
                parts = line.strip().split()
                if len(parts) >= 2:
                    branch_name = parts[0]
                    commit_hash = parts[1]
                    
                    remote_branches.append(GitBranch(
                        name=branch_name,
                        is_current=False,
                        is_remote=True,
                        commit_hash=commit_hash
                    ))
            
            all_branches = local_branches + remote_branches
            
            return {
                "success": True,
                "branches": [self._branch_to_dict(branch) for branch in all_branches]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting branches: {e}")
            return {"error": str(e)}
    
    async def resolve_conflicts(self, strategy: str = "merge",
                              repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Resolve merge conflicts"""
        try:
            cwd = repo_path or self.current_repo_path
            if not cwd:
                return {"error": "No repository path specified"}
            
            if strategy == "merge":
                # Use merge tool
                result = await self._run_git_command(["mergetool"], cwd=cwd)
            elif strategy == "ours":
                # Accept our changes
                result = await self._run_git_command(["checkout", "--ours", "."], cwd=cwd)
                await self._run_git_command(["add", "."], cwd=cwd)
            elif strategy == "theirs":
                # Accept their changes
                result = await self._run_git_command(["checkout", "--theirs", "."], cwd=cwd)
                await self._run_git_command(["add", "."], cwd=cwd)
            else:
                return {"error": f"Unknown conflict resolution strategy: {strategy}"}
            
            return {
                "success": True,
                "strategy": strategy,
                "output": result
            }
            
        except Exception as e:
            self.logger.error(f"Error resolving conflicts: {e}")
            return {"error": str(e)}
    
    async def create_tag(self, tag_name: str, message: Optional[str] = None,
                        repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Create a tag"""
        try:
            cwd = repo_path or self.current_repo_path
            if not cwd:
                return {"error": "No repository path specified"}
            
            # Create tag
            if message:
                result = await self._run_git_command(["tag", "-a", tag_name, "-m", message], cwd=cwd)
            else:
                result = await self._run_git_command(["tag", tag_name], cwd=cwd)
            
            return {
                "success": True,
                "tag_name": tag_name,
                "message": message,
                "output": result
            }
            
        except Exception as e:
            self.logger.error(f"Error creating tag: {e}")
            return {"error": str(e)}
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get version control statistics"""
        return {
            "success": True,
            "statistics": self.stats.copy(),
            "current_repo": self.current_repo_path,
            "default_branch": self.default_branch,
            "repo_config": self.repo_config
        }
    
    async def _run_git_command(self, args: List[str], cwd: Optional[str] = None) -> str:
        """Run a Git command"""
        cmd = [self.git_path] + args
        
        # Update statistics
        self.stats["total_operations"] += 1
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd, stderr)
            
            self.stats["successful_operations"] += 1
            return stdout.decode('utf-8', errors='replace')
            
        except Exception as e:
            self.stats["failed_operations"] += 1
            raise
    
    async def _load_repo_config(self, repo_path: str) -> None:
        """Load repository configuration"""
        try:
            # Get git config
            result = await self._run_git_command(["config", "--list"], cwd=repo_path)
            
            config = {}
            for line in result.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
            
            self.repo_config = config
            
        except Exception as e:
            self.logger.warning(f"Could not load repo config: {e}")
            self.repo_config = {}
    
    def _commit_to_dict(self, commit: GitCommit) -> Dict[str, Any]:
        """Convert GitCommit to dictionary"""
        return {
            "hash": commit.hash,
            "author": commit.author,
            "email": commit.email,
            "date": commit.date.isoformat(),
            "message": commit.message,
            "files_changed": commit.files_changed,
            "insertions": commit.insertions,
            "deletions": commit.deletions
        }
    
    def _branch_to_dict(self, branch: GitBranch) -> Dict[str, Any]:
        """Convert GitBranch to dictionary"""
        return {
            "name": branch.name,
            "is_current": branch.is_current,
            "is_remote": branch.is_remote,
            "commit_hash": branch.commit_hash,
            "last_commit_date": branch.last_commit_date.isoformat() if branch.last_commit_date else None
        }
    
    def _status_to_dict(self, status: GitStatus) -> Dict[str, Any]:
        """Convert GitStatus to dictionary"""
        return {
            "is_clean": status.is_clean,
            "staged_files": status.staged_files,
            "unstaged_files": status.unstaged_files,
            "untracked_files": status.untracked_files,
            "branch": status.branch,
            "ahead": status.ahead,
            "behind": status.behind
        }