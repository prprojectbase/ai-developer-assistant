#!/usr/bin/env python3
"""
Package Management Module

Provides comprehensive package management tools including dependency resolution,
package installation, version management, and security scanning for the AI Developer Assistant.
"""

import asyncio
import logging
import json
import subprocess
import re
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import tempfile
import os
import hashlib

from ..config.settings import get_settings


@dataclass
class Package:
    """Package information"""
    name: str
    version: str
    description: str = ""
    homepage: str = ""
    license: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    dev_dependencies: List[str] = field(default_factory=list)
    size: int = 0
    security_issues: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PackageRegistry:
    """Package registry configuration"""
    name: str
    url: str
    type: str  # npm, pip, maven, nuget, cargo, etc.
    auth_required: bool = False
    credentials: Dict[str, str] = field(default_factory=dict)


@dataclass
class DependencyGraph:
    """Dependency graph representation"""
    root_package: str
    packages: Dict[str, Package] = field(default_factory=dict)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    dev_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    circular_dependencies: List[List[str]] = field(default_factory=list)


@dataclass
class LockFile:
    """Package lock file"""
    package_manager: str  # npm, pip, maven, etc.
    lock_file_version: str
    packages: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PackageManagement:
    """Package management tools for comprehensive dependency management"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Package registries
        self.registries: Dict[str, PackageRegistry] = {}
        
        # Package managers
        self.supported_managers = ["npm", "pip", "maven", "gradle", "cargo", "nuget", "composer"]
        
        # Package cache
        self.package_cache: Dict[str, Package] = {}
        
        # Dependency graphs
        self.dependency_graphs: Dict[str, DependencyGraph] = {}
        
        # Lock files
        self.lock_files: Dict[str, LockFile] = {}
        
        # Security database
        self.vulnerability_database: Dict[str, List[Dict[str, Any]]] = {}
        
        # Statistics
        self.stats = {
            "packages_installed": 0,
            "packages_updated": 0,
            "packages_removed": 0,
            "security_scans": 0,
            "vulnerabilities_found": 0,
            "dependency_resolutions": 0
        }
    
    async def initialize(self) -> None:
        """Initialize the package management tools"""
        self.logger.info("Initializing Package Management...")
        
        # Create workspace
        pkg_workspace = Path(self.settings.workspace_dir) / "packages"
        pkg_workspace.mkdir(parents=True, exist_ok=True)
        
        # Initialize default registries
        await self._initialize_registries()
        
        # Initialize vulnerability database
        await self._initialize_vulnerability_database()
        
        self.logger.info("Package Management initialized successfully")
    
    async def stop(self) -> None:
        """Stop the package management tools"""
        self.logger.info("Stopping Package Management...")
        self.logger.info("Package Management stopped")
    
    async def add_registry(self, registry: PackageRegistry) -> Dict[str, Any]:
        """Add a package registry"""
        try:
            if registry.type not in self.supported_managers:
                return {"error": f"Unsupported package manager: {registry.type}"}
            
            # Test registry connection
            connection_test = await self._test_registry_connection(registry)
            if not connection_test["success"]:
                return {"error": f"Registry connection test failed: {connection_test['error']}"}
            
            self.registries[registry.name] = registry
            
            return {
                "success": True,
                "registry_name": registry.name,
                "registry_type": registry.type,
                "url": registry.url,
                "message": f"Package registry '{registry.name}' added successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error adding registry: {e}")
            return {"error": str(e)}
    
    async def install_package(self, package_name: str, version: str = "latest",
                             project_path: str = ".", package_manager: str = "auto") -> Dict[str, Any]:
        """Install a package"""
        try:
            project_path = Path(project_path)
            if not project_path.exists():
                return {"error": f"Project path '{project_path}' not found"}
            
            # Auto-detect package manager
            if package_manager == "auto":
                package_manager = await self._detect_package_manager(project_path)
            
            if package_manager not in self.supported_managers:
                return {"error": f"Unsupported package manager: {package_manager}"}
            
            # Install package
            result = await self._install_package_with_manager(
                package_name, version, project_path, package_manager
            )
            
            if result["success"]:
                self.stats["packages_installed"] += 1
                
                # Update dependency graph
                await self._update_dependency_graph(project_path, package_manager)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error installing package: {e}")
            return {"error": str(e)}
    
    async def update_package(self, package_name: str, version: str = "latest",
                           project_path: str = ".", package_manager: str = "auto") -> Dict[str, Any]:
        """Update a package"""
        try:
            project_path = Path(project_path)
            if not project_path.exists():
                return {"error": f"Project path '{project_path}' not found"}
            
            # Auto-detect package manager
            if package_manager == "auto":
                package_manager = await self._detect_package_manager(project_path)
            
            # Update package
            result = await self._update_package_with_manager(
                package_name, version, project_path, package_manager
            )
            
            if result["success"]:
                self.stats["packages_updated"] += 1
                
                # Update dependency graph
                await self._update_dependency_graph(project_path, package_manager)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error updating package: {e}")
            return {"error": str(e)}
    
    async def remove_package(self, package_name: str, project_path: str = ".",
                           package_manager: str = "auto") -> Dict[str, Any]:
        """Remove a package"""
        try:
            project_path = Path(project_path)
            if not project_path.exists():
                return {"error": f"Project path '{project_path}' not found"}
            
            # Auto-detect package manager
            if package_manager == "auto":
                package_manager = await self._detect_package_manager(project_path)
            
            # Remove package
            result = await self._remove_package_with_manager(
                package_name, project_path, package_manager
            )
            
            if result["success"]:
                self.stats["packages_removed"] += 1
                
                # Update dependency graph
                await self._update_dependency_graph(project_path, package_manager)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error removing package: {e}")
            return {"error": str(e)}
    
    async def generate_lock_file(self, project_path: str = ".", 
                               package_manager: str = "auto") -> Dict[str, Any]:
        """Generate package lock file"""
        try:
            project_path = Path(project_path)
            if not project_path.exists():
                return {"error": f"Project path '{project_path}' not found"}
            
            # Auto-detect package manager
            if package_manager == "auto":
                package_manager = await self._detect_package_manager(project_path)
            
            # Generate lock file based on package manager
            if package_manager == "npm":
                result = await self._generate_npm_lock_file(project_path)
            elif package_manager == "pip":
                result = await self._generate_pip_lock_file(project_path)
            elif package_manager == "maven":
                result = await self._generate_maven_lock_file(project_path)
            else:
                return {"error": f"Lock file generation not supported for {package_manager}"}
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating lock file: {e}")
            return {"error": str(e)}
    
    async def resolve_dependencies(self, project_path: str = ".",
                                package_manager: str = "auto") -> Dict[str, Any]:
        """Resolve project dependencies"""
        try:
            project_path = Path(project_path)
            if not project_path.exists():
                return {"error": f"Project path '{project_path}' not found"}
            
            # Auto-detect package manager
            if package_manager == "auto":
                package_manager = await self._detect_package_manager(project_path)
            
            # Resolve dependencies
            result = await self._resolve_dependencies_with_manager(
                project_path, package_manager
            )
            
            if result["success"]:
                self.stats["dependency_resolutions"] += 1
                
                # Create dependency graph
                await self._create_dependency_graph(project_path, package_manager)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error resolving dependencies: {e}")
            return {"error": str(e)}
    
    async def scan_security_vulnerabilities(self, project_path: str = ".",
                                         package_manager: str = "auto") -> Dict[str, Any]:
        """Scan packages for security vulnerabilities"""
        try:
            project_path = Path(project_path)
            if not project_path.exists():
                return {"error": f"Project path '{project_path}' not found"}
            
            # Auto-detect package manager
            if package_manager == "auto":
                package_manager = await self._detect_package_manager(project_path)
            
            # Get installed packages
            packages = await self._get_installed_packages(project_path, package_manager)
            
            # Scan for vulnerabilities
            vulnerabilities = []
            for package in packages:
                package_vulns = await self._scan_package_vulnerabilities(
                    package["name"], package["version"]
                )
                vulnerabilities.extend(package_vulns)
            
            self.stats["security_scans"] += 1
            self.stats["vulnerabilities_found"] += len(vulnerabilities)
            
            return {
                "success": True,
                "project_path": str(project_path),
                "package_manager": package_manager,
                "packages_scanned": len(packages),
                "vulnerabilities": vulnerabilities,
                "vulnerability_count": len(vulnerabilities),
                "message": f"Security scan completed for '{project_path.name}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error scanning security vulnerabilities: {e}")
            return {"error": str(e)}
    
    async def get_package_info(self, package_name: str, 
                             registry_name: str = "default") -> Dict[str, Any]:
        """Get package information from registry"""
        try:
            if registry_name not in self.registries:
                return {"error": f"Registry '{registry_name}' not found"}
            
            registry = self.registries[registry_name]
            
            # Get package info from registry
            package_info = await self._fetch_package_info(package_name, registry)
            
            return {
                "success": True,
                "package_name": package_name,
                "registry": registry_name,
                "package_info": package_info,
                "message": f"Package information retrieved for '{package_name}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting package info: {e}")
            return {"error": str(e)}
    
    async def find_package_alternatives(self, package_name: str, 
                                      criteria: Dict[str, Any] = None) -> Dict[str, Any]:
        """Find alternative packages"""
        try:
            if criteria is None:
                criteria = {"category": "similar"}
            
            # Find alternatives (simplified implementation)
            alternatives = []
            
            # This would query registries for similar packages
            # For now, return mock data
            alternatives = [
                {
                    "name": f"{package_name}-alternative-1",
                    "description": f"Alternative to {package_name}",
                    "similarity_score": 0.85,
                    "download_count": 1000000
                },
                {
                    "name": f"{package_name}-alternative-2",
                    "description": f"Another alternative to {package_name}",
                    "similarity_score": 0.75,
                    "download_count": 500000
                }
            ]
            
            return {
                "success": True,
                "original_package": package_name,
                "alternatives": alternatives,
                "criteria": criteria,
                "message": f"Found {len(alternatives)} alternatives for '{package_name}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error finding package alternatives: {e}")
            return {"error": str(e)}
    
    async def optimize_dependencies(self, project_path: str = ".",
                                 package_manager: str = "auto") -> Dict[str, Any]:
        """Optimize project dependencies"""
        try:
            project_path = Path(project_path)
            if not project_path.exists():
                return {"error": f"Project path '{project_path}' not found"}
            
            # Auto-detect package manager
            if package_manager == "auto":
                package_manager = await self._detect_package_manager(project_path)
            
            # Get current dependencies
            current_deps = await self._get_installed_packages(project_path, package_manager)
            
            # Analyze and optimize
            optimizations = []
            
            # Find unused dependencies
            unused_deps = await self._find_unused_dependencies(project_path, package_manager)
            if unused_deps:
                optimizations.append({
                    "type": "unused_dependencies",
                    "packages": unused_deps,
                    "action": "remove",
                    "savings": "reduced bundle size"
                })
            
            # Find outdated packages
            outdated_deps = await self._find_outdated_packages(project_path, package_manager)
            if outdated_deps:
                optimizations.append({
                    "type": "outdated_packages",
                    "packages": outdated_deps,
                    "action": "update",
                    "savings": "security patches and performance improvements"
                })
            
            # Find duplicate functionality
            duplicate_deps = await self._find_duplicate_functionality(project_path, package_manager)
            if duplicate_deps:
                optimizations.append({
                    "type": "duplicate_functionality",
                    "packages": duplicate_deps,
                    "action": "consolidate",
                    "savings": "reduced complexity and bundle size"
                })
            
            return {
                "success": True,
                "project_path": str(project_path),
                "package_manager": package_manager,
                "current_packages": len(current_deps),
                "optimizations": optimizations,
                "message": f"Dependency optimization completed for '{project_path.name}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing dependencies: {e}")
            return {"error": str(e)}
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get package management statistics"""
        return {
            "success": True,
            "statistics": self.stats.copy(),
            "registries": len(self.registries),
            "package_cache": len(self.package_cache),
            "dependency_graphs": len(self.dependency_graphs),
            "lock_files": len(self.lock_files),
            "supported_managers": self.supported_managers
        }
    
    async def _initialize_registries(self) -> None:
        """Initialize default package registries"""
        # npm registry
        npm_registry = PackageRegistry(
            name="npm",
            url="https://registry.npmjs.org",
            type="npm",
            auth_required=False
        )
        
        # PyPI registry
        pypi_registry = PackageRegistry(
            name="pypi",
            url="https://pypi.org/pypi",
            type="pip",
            auth_required=False
        )
        
        # Maven Central
        maven_registry = PackageRegistry(
            name="maven_central",
            url="https://repo.maven.apache.org/maven2",
            type="maven",
            auth_required=False
        )
        
        # NuGet registry
        nuget_registry = PackageRegistry(
            name="nuget",
            url="https://api.nuget.org/v3/index.json",
            type="nuget",
            auth_required=False
        )
        
        # Cargo registry
        cargo_registry = PackageRegistry(
            name="crates",
            url="https://crates.io",
            type="cargo",
            auth_required=False
        )
        
        self.registries = {
            "npm": npm_registry,
            "pypi": pypi_registry,
            "maven": maven_registry,
            "nuget": nuget_registry,
            "crates": cargo_registry
        }
    
    async def _initialize_vulnerability_database(self) -> None:
        """Initialize vulnerability database (simplified)"""
        # In a real implementation, this would load from a vulnerability database
        # For now, use a small sample
        self.vulnerability_database = {
            "lodash": [
                {
                    "id": "CVE-2021-23337",
                    "severity": "high",
                    "affected_versions": "<4.17.11",
                    "fixed_version": "4.17.11",
                    "description": "Prototype Pollution in lodash"
                }
            ],
            "axios": [
                {
                    "id": "CVE-2021-3749",
                    "severity": "medium",
                    "affected_versions": "<0.21.1",
                    "fixed_version": "0.21.1",
                    "description": "Server-Side Request Forgery in axios"
                }
            ],
            "requests": [
                {
                    "id": "CVE-2018-18074",
                    "severity": "high",
                    "affected_versions": "<2.20.0",
                    "fixed_version": "2.20.0",
                    "description": "Redirect vulnerability in requests"
                }
            ]
        }
    
    async def _test_registry_connection(self, registry: PackageRegistry) -> Dict[str, Any]:
        """Test connection to package registry"""
        try:
            # Simple HTTP request to test connectivity
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(registry.url, timeout=10) as response:
                    if response.status < 400:
                        return {"success": True}
                    else:
                        return {"success": False, "error": f"HTTP {response.status}"}
                        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _detect_package_manager(self, project_path: Path) -> str:
        """Detect package manager used in project"""
        # Check for package manager files
        package_manager_files = {
            "npm": ["package.json", "package-lock.json", "yarn.lock"],
            "pip": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
            "maven": ["pom.xml"],
            "gradle": ["build.gradle", "build.gradle.kts"],
            "cargo": ["Cargo.toml", "Cargo.lock"],
            "nuget": ["packages.config", "*.csproj", "packages.lock.json"],
            "composer": ["composer.json", "composer.lock"]
        }
        
        for pm_name, files in package_manager_files.items():
            for file_pattern in files:
                if "*" in file_pattern:
                    # Handle wildcard patterns
                    base_pattern = file_pattern.replace("*", "")
                    for file_path in project_path.glob(file_pattern):
                        if file_path.is_file():
                            return pm_name
                else:
                    if (project_path / file_pattern).exists():
                        return pm_name
        
        # Default to pip if no package manager detected
        return "pip"
    
    async def _install_package_with_manager(self, package_name: str, version: str,
                                          project_path: Path, package_manager: str) -> Dict[str, Any]:
        """Install package using specific package manager"""
        try:
            if package_manager == "npm":
                cmd = ["npm", "install", f"{package_name}@{version}"]
            elif package_manager == "pip":
                cmd = ["pip", "install", f"{package_name}=={version}"]
            elif package_manager == "maven":
                # Maven requires updating pom.xml
                return await self._add_maven_dependency(package_name, version, project_path)
            elif package_manager == "gradle":
                # Gradle requires updating build.gradle
                return await self._add_gradle_dependency(package_name, version, project_path)
            else:
                return {"error": f"Installation not implemented for {package_manager}"}
            
            result = await self._run_command(cmd, cwd=str(project_path))
            
            return {
                "success": True,
                "package_name": package_name,
                "version": version,
                "package_manager": package_manager,
                "output": result,
                "message": f"Package '{package_name}@{version}' installed successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _update_package_with_manager(self, package_name: str, version: str,
                                          project_path: Path, package_manager: str) -> Dict[str, Any]:
        """Update package using specific package manager"""
        try:
            if package_manager == "npm":
                cmd = ["npm", "update", package_name]
            elif package_manager == "pip":
                cmd = ["pip", "install", "--upgrade", f"{package_name}=={version}"]
            else:
                return {"error": f"Update not implemented for {package_manager}"}
            
            result = await self._run_command(cmd, cwd=str(project_path))
            
            return {
                "success": True,
                "package_name": package_name,
                "version": version,
                "package_manager": package_manager,
                "output": result,
                "message": f"Package '{package_name}' updated to '{version}'"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _remove_package_with_manager(self, package_name: str,
                                          project_path: Path, package_manager: str) -> Dict[str, Any]:
        """Remove package using specific package manager"""
        try:
            if package_manager == "npm":
                cmd = ["npm", "uninstall", package_name]
            elif package_manager == "pip":
                cmd = ["pip", "uninstall", package_name]
            else:
                return {"error": f"Removal not implemented for {package_manager}"}
            
            result = await self._run_command(cmd, cwd=str(project_path))
            
            return {
                "success": True,
                "package_name": package_name,
                "package_manager": package_manager,
                "output": result,
                "message": f"Package '{package_name}' removed successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _generate_npm_lock_file(self, project_path: Path) -> Dict[str, Any]:
        """Generate npm lock file"""
        try:
            result = await self._run_command(["npm", "install"], cwd=str(project_path))
            
            return {
                "success": True,
                "package_manager": "npm",
                "lock_file": "package-lock.json",
                "output": result,
                "message": "npm lock file generated successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _generate_pip_lock_file(self, project_path: Path) -> Dict[str, Any]:
        """Generate pip lock file"""
        try:
            # Try pip-tools if available
            try:
                result = await self._run_command(["pip-compile", "requirements.in"], cwd=str(project_path))
                lock_file = "requirements.txt"
            except:
                # Fallback to pip freeze
                result = await self._run_command(["pip", "freeze"], cwd=str(project_path))
                lock_file = "requirements.txt"
            
            return {
                "success": True,
                "package_manager": "pip",
                "lock_file": lock_file,
                "output": result,
                "message": "pip lock file generated successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _generate_maven_lock_file(self, project_path: Path) -> Dict[str, Any]:
        """Generate Maven lock file"""
        try:
            # Maven doesn't have traditional lock files, but we can generate dependency tree
            result = await self._run_command(["mvn", "dependency:tree"], cwd=str(project_path))
            
            return {
                "success": True,
                "package_manager": "maven",
                "lock_file": "dependency-tree.txt",
                "output": result,
                "message": "Maven dependency tree generated successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _resolve_dependencies_with_manager(self, project_path: Path,
                                               package_manager: str) -> Dict[str, Any]:
        """Resolve dependencies using specific package manager"""
        try:
            if package_manager == "npm":
                cmd = ["npm", "install"]
            elif package_manager == "pip":
                cmd = ["pip", "install", "-r", "requirements.txt"]
            elif package_manager == "maven":
                cmd = ["mvn", "dependency:resolve"]
            else:
                return {"error": f"Dependency resolution not implemented for {package_manager}"}
            
            result = await self._run_command(cmd, cwd=str(project_path))
            
            return {
                "success": True,
                "package_manager": package_manager,
                "output": result,
                "message": f"Dependencies resolved using {package_manager}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_installed_packages(self, project_path: Path,
                                    package_manager: str) -> List[Dict[str, Any]]:
        """Get list of installed packages"""
        try:
            packages = []
            
            if package_manager == "npm":
                result = await self._run_command(["npm", "list", "--json"], cwd=str(project_path))
                data = json.loads(result)
                # Parse npm list output
                packages = self._parse_npm_list(data)
            elif package_manager == "pip":
                result = await self._run_command(["pip", "list", "--format=json"], cwd=str(project_path))
                data = json.loads(result)
                packages = [{"name": pkg["name"], "version": pkg["version"]} for pkg in data]
            elif package_manager == "maven":
                result = await self._run_command(["mvn", "dependency:list"], cwd=str(project_path))
                packages = self._parse_maven_dependencies(result)
            
            return packages
            
        except Exception as e:
            self.logger.error(f"Error getting installed packages: {e}")
            return []
    
    async def _scan_package_vulnerabilities(self, package_name: str, version: str) -> List[Dict[str, Any]]:
        """Scan package for security vulnerabilities"""
        vulnerabilities = []
        
        # Check vulnerability database
        if package_name in self.vulnerability_database:
            for vuln in self.vulnerability_database[package_name]:
                # Check if version is affected
                if self._is_version_affected(version, vuln["affected_versions"]):
                    vulnerabilities.append({
                        "id": vuln["id"],
                        "severity": vuln["severity"],
                        "package": package_name,
                        "current_version": version,
                        "fixed_version": vuln["fixed_version"],
                        "description": vuln["description"]
                    })
        
        return vulnerabilities
    
    async def _fetch_package_info(self, package_name: str, registry: PackageRegistry) -> Dict[str, Any]:
        """Fetch package information from registry"""
        try:
            # This would make actual API calls to the registry
            # For now, return mock data
            return {
                "name": package_name,
                "version": "1.0.0",
                "description": f"Mock package information for {package_name}",
                "author": "Mock Author",
                "license": "MIT",
                "homepage": f"https://example.com/{package_name}",
                "dependencies": [],
                "downloads": 1000000
            }
            
        except Exception as e:
            raise
    
    async def _find_unused_dependencies(self, project_path: Path,
                                      package_manager: str) -> List[str]:
        """Find unused dependencies"""
        # This is a simplified implementation
        # In a real implementation, this would analyze code usage
        return []
    
    async def _find_outdated_packages(self, project_path: Path,
                                     package_manager: str) -> List[Dict[str, Any]]:
        """Find outdated packages"""
        try:
            outdated = []
            
            if package_manager == "npm":
                result = await self._run_command(["npm", "outdated", "--json"], cwd=str(project_path))
                data = json.loads(result)
                outdated = [
                    {
                        "name": pkg["name"],
                        "current": pkg["current"],
                        "latest": pkg["latest"],
                        "wanted": pkg["wanted"]
                    }
                    for pkg in data
                ]
            elif package_manager == "pip":
                result = await self._run_command(["pip", "list", "--outdated"], cwd=str(project_path))
                outdated = self._parse_pip_outdated(result)
            
            return outdated
            
        except Exception as e:
            self.logger.error(f"Error finding outdated packages: {e}")
            return []
    
    async def _find_duplicate_functionality(self, project_path: Path,
                                          package_manager: str) -> List[Dict[str, Any]]:
        """Find packages with duplicate functionality"""
        # This is a simplified implementation
        # In a real implementation, this would analyze package functionality
        return []
    
    async def _update_dependency_graph(self, project_path: Path, package_manager: str) -> None:
        """Update dependency graph for project"""
        try:
            graph_id = str(project_path)
            
            if graph_id not in self.dependency_graphs:
                await self._create_dependency_graph(project_path, package_manager)
            else:
                # Update existing graph
                graph = self.dependency_graphs[graph_id]
                # Re-scan dependencies
                packages = await self._get_installed_packages(project_path, package_manager)
                
                # Update packages in graph
                for pkg in packages:
                    if pkg["name"] not in graph.packages:
                        graph.packages[pkg["name"]] = Package(
                            name=pkg["name"],
                            version=pkg["version"]
                        )
                
        except Exception as e:
            self.logger.error(f"Error updating dependency graph: {e}")
    
    async def _create_dependency_graph(self, project_path: Path, package_manager: str) -> None:
        """Create dependency graph for project"""
        try:
            graph_id = str(project_path)
            
            # Get project name
            project_name = project_path.name
            
            # Get installed packages
            packages = await self._get_installed_packages(project_path, package_manager)
            
            # Create dependency graph
            graph = DependencyGraph(root_package=project_name)
            
            # Add packages to graph
            for pkg in packages:
                package_obj = Package(name=pkg["name"], version=pkg["version"])
                graph.packages[pkg["name"]] = package_obj
            
            # In a real implementation, this would analyze actual dependencies
            # For now, create a simple graph
            for pkg in packages:
                graph.dependencies[pkg["name"]] = []
            
            self.dependency_graphs[graph_id] = graph
            
        except Exception as e:
            self.logger.error(f"Error creating dependency graph: {e}")
    
    async def _add_maven_dependency(self, package_name: str, version: str,
                                  project_path: Path) -> Dict[str, Any]:
        """Add Maven dependency to pom.xml"""
        try:
            pom_path = project_path / "pom.xml"
            if not pom_path.exists():
                return {"error": "pom.xml not found"}
            
            # Parse pom.xml and add dependency
            with open(pom_path, 'r') as f:
                content = f.read()
            
            # Find dependencies section and add new dependency
            dependency_xml = f"""
    <dependency>
        <groupId>{package_name.split(':')[0]}</groupId>
        <artifactId>{package_name.split(':')[1] if ':' in package_name else package_name}</artifactId>
        <version>{version}</version>
    </dependency>"""
            
            if "<dependencies>" in content:
                # Add to existing dependencies section
                content = content.replace(
                    "</dependencies>",
                    dependency_xml + "\n    </dependencies>"
                )
            else:
                # Add new dependencies section
                content = content.replace(
                    "</project>",
                    "    <dependencies>" + dependency_xml + "\n    </dependencies>\n</project>"
                )
            
            # Write back to pom.xml
            with open(pom_path, 'w') as f:
                f.write(content)
            
            return {
                "success": True,
                "package_name": package_name,
                "version": version,
                "message": f"Maven dependency '{package_name}' added successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _add_gradle_dependency(self, package_name: str, version: str,
                                   project_path: Path) -> Dict[str, Any]:
        """Add Gradle dependency to build.gradle"""
        try:
            build_path = project_path / "build.gradle"
            if not build_path.exists():
                return {"error": "build.gradle not found"}
            
            # Parse build.gradle and add dependency
            with open(build_path, 'r') as f:
                content = f.read()
            
            # Add dependency
            dependency_line = f"    implementation '{package_name}:{version}'\n"
            
            if "dependencies {" in content:
                # Add to existing dependencies block
                content = content.replace(
                    "dependencies {",
                    "dependencies {" + dependency_line
                )
            else:
                # Add new dependencies block
                content += f"\ndependencies {{\n{dependency_line}}}\n"
            
            # Write back to build.gradle
            with open(build_path, 'w') as f:
                f.write(content)
            
            return {
                "success": True,
                "package_name": package_name,
                "version": version,
                "message": f"Gradle dependency '{package_name}' added successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _run_command(self, command: List[str], cwd: Optional[str] = None) -> str:
        """Run a shell command"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, command, stderr)
            
            return stdout.decode('utf-8', errors='replace')
            
        except Exception as e:
            raise
    
    def _is_version_affected(self, version: str, affected_versions: str) -> bool:
        """Check if version is affected by vulnerability"""
        # Simplified version comparison
        # In a real implementation, this would use proper semantic version comparison
        try:
            if affected_versions.startswith("<"):
                max_version = affected_versions[1:]
                return self._compare_versions(version, max_version) < 0
            elif affected_versions.startswith(">="):
                min_version = affected_versions[2:]
                return self._compare_versions(version, min_version) >= 0
            else:
                return False
        except:
            return False
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two versions"""
        # Simplified version comparison
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        
        # Pad shorter version with zeros
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for i in range(max_len):
            if v1_parts[i] < v2_parts[i]:
                return -1
            elif v1_parts[i] > v2_parts[i]:
                return 1
        
        return 0
    
    def _parse_npm_list(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse npm list output"""
        packages = []
        
        def parse_dependencies(deps: Dict[str, Any], prefix: str = ""):
            for name, info in deps.items():
                if isinstance(info, dict) and "version" in info:
                    packages.append({
                        "name": name,
                        "version": info["version"]
                    })
                    if "dependencies" in info:
                        parse_dependencies(info["dependencies"], prefix + "  ")
        
        if "dependencies" in data:
            parse_dependencies(data["dependencies"])
        
        return packages
    
    def _parse_maven_dependencies(self, output: str) -> List[Dict[str, Any]]:
        """Parse Maven dependency list output"""
        packages = []
        
        for line in output.split('\n'):
            if "compile" in line or "runtime" in line:
                # Parse Maven dependency line
                # Format: groupId:artifactId:type:version:scope
                parts = line.strip().split(':')
                if len(parts) >= 4:
                    packages.append({
                        "name": f"{parts[0]}:{parts[1]}",
                        "version": parts[3]
                    })
        
        return packages
    
    def _parse_pip_outdated(self, output: str) -> List[Dict[str, Any]]:
        """Parse pip outdated output"""
        packages = []
        
        for line in output.split('\n')[2:]:  # Skip header lines
            if line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    packages.append({
                        "name": parts[0],
                        "current": parts[1],
                        "latest": parts[2],
                        "wanted": parts[1]  # pip doesn't show wanted
                    })
        
        return packages