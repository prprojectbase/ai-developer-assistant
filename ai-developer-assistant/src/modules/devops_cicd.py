#!/usr/bin/env python3
"""
DevOps & CI/CD Module

Provides comprehensive DevOps and CI/CD pipeline management including
build automation, deployment, monitoring, and infrastructure management
for the AI Developer Assistant.
"""

import asyncio
import logging
import json
import yaml
import subprocess
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import tempfile
import shutil
import os

from ..config.settings import get_settings


@dataclass
class PipelineStage:
    """CI/CD pipeline stage"""
    name: str
    type: str  # build, test, deploy, monitor
    commands: List[str]
    timeout: int = 300
    retry_count: int = 0
    retry_delay: int = 5
    on_failure: str = "continue"  # continue, stop, rollback
    dependencies: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)


@dataclass
class Pipeline:
    """CI/CD pipeline definition"""
    name: str
    description: str = ""
    stages: List[PipelineStage] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)  # push, pr, schedule, manual
    environment: str = "development"
    timeout: int = 3600
    notifications: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class BuildConfig:
    """Build configuration"""
    name: str
    build_tool: str  # maven, gradle, npm, docker, make
    build_command: str
    test_command: str = ""
    package_command: str = ""
    environment: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    output_artifacts: List[str] = field(default_factory=list)


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    name: str
    target: str  # kubernetes, docker, aws, azure, gcp
    deployment_type: str  # rolling, blue-green, canary
    target_environment: str
    deployment_script: str = ""
    rollback_script: str = ""
    health_check_url: str = ""
    health_check_timeout: int = 30
    environment_variables: Dict[str, str] = field(default_factory=dict)


@dataclass
class PipelineExecution:
    """Pipeline execution result"""
    pipeline_name: str
    execution_id: str
    status: str  # running, success, failed, cancelled
    start_time: datetime
    end_time: Optional[datetime] = None
    stages: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    error_message: str = ""


class DevOpsCICD:
    """DevOps & CI/CD management tools"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Pipeline management
        self.pipelines: Dict[str, Pipeline] = {}
        self.pipeline_executions: Dict[str, PipelineExecution] = {}
        self.active_executions: Dict[str, asyncio.Task] = {}
        
        # Build configurations
        self.build_configs: Dict[str, BuildConfig] = {}
        
        # Deployment configurations
        self.deployment_configs: Dict[str, DeploymentConfig] = {}
        
        # Environment management
        self.environments: Dict[str, Dict[str, Any]] = {}
        
        # Artifact storage
        self.artifacts: Dict[str, Dict[str, Any]] = {}
        
        # Statistics
        self.stats = {
            "pipelines_created": 0,
            "pipelines_executed": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "builds_performed": 0,
            "deployments_performed": 0
        }
    
    async def initialize(self) -> None:
        """Initialize the DevOps & CI/CD tools"""
        self.logger.info("Initializing DevOps & CI/CD...")
        
        # Create workspace
        cicd_workspace = Path(self.settings.workspace_dir) / "cicd"
        cicd_workspace.mkdir(parents=True, exist_ok=True)
        
        # Initialize default environments
        self.environments = {
            "development": {
                "name": "development",
                "type": "local",
                "url": "http://localhost:3000",
                "auto_deploy": True
            },
            "staging": {
                "name": "staging",
                "type": "remote",
                "url": "https://staging.example.com",
                "auto_deploy": False
            },
            "production": {
                "name": "production",
                "type": "remote",
                "url": "https://example.com",
                "auto_deploy": False,
                "requires_approval": True
            }
        }
        
        self.logger.info("DevOps & CI/CD initialized successfully")
    
    async def stop(self) -> None:
        """Stop the DevOps & CI/CD tools"""
        self.logger.info("Stopping DevOps & CI/CD...")
        
        # Cancel all active executions
        for execution_id, task in self.active_executions.items():
            if not task.done():
                task.cancel()
        
        self.logger.info("DevOps & CI/CD stopped")
    
    async def create_pipeline(self, pipeline: Pipeline) -> Dict[str, Any]:
        """Create a new CI/CD pipeline"""
        try:
            pipeline_id = f"{pipeline.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.pipelines[pipeline_id] = pipeline
            self.stats["pipelines_created"] += 1
            
            return {
                "success": True,
                "pipeline_id": pipeline_id,
                "name": pipeline.name,
                "stages": len(pipeline.stages),
                "message": f"Pipeline '{pipeline.name}' created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating pipeline: {e}")
            return {"error": str(e)}
    
    async def execute_pipeline(self, pipeline_id: str, 
                              trigger_type: str = "manual",
                              trigger_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a CI/CD pipeline"""
        try:
            if pipeline_id not in self.pipelines:
                return {"error": f"Pipeline '{pipeline_id}' not found"}
            
            pipeline = self.pipelines[pipeline_id]
            execution_id = f"{pipeline_id}_exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create execution record
            execution = PipelineExecution(
                pipeline_name=pipeline.name,
                execution_id=execution_id,
                status="running",
                start_time=datetime.now()
            )
            
            self.pipeline_executions[execution_id] = execution
            
            # Start pipeline execution
            execution_task = asyncio.create_task(
                self._execute_pipeline_stages(pipeline, execution)
            )
            self.active_executions[execution_id] = execution_task
            
            self.stats["pipelines_executed"] += 1
            
            return {
                "success": True,
                "pipeline_id": pipeline_id,
                "execution_id": execution_id,
                "status": "running",
                "message": f"Pipeline '{pipeline.name}' execution started"
            }
            
        except Exception as e:
            self.logger.error(f"Error executing pipeline: {e}")
            return {"error": str(e)}
    
    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get pipeline execution status"""
        try:
            if execution_id not in self.pipeline_executions:
                return {"error": f"Execution '{execution_id}' not found"}
            
            execution = self.pipeline_executions[execution_id]
            
            return {
                "success": True,
                "execution_id": execution_id,
                "pipeline_name": execution.pipeline_name,
                "status": execution.status,
                "start_time": execution.start_time.isoformat(),
                "end_time": execution.end_time.isoformat() if execution.end_time else None,
                "stages": execution.stages,
                "artifacts": execution.artifacts,
                "error_message": execution.error_message
            }
            
        except Exception as e:
            self.logger.error(f"Error getting execution status: {e}")
            return {"error": str(e)}
    
    async def create_build_config(self, config: BuildConfig) -> Dict[str, Any]:
        """Create a build configuration"""
        try:
            self.build_configs[config.name] = config
            
            return {
                "success": True,
                "config_name": config.name,
                "build_tool": config.build_tool,
                "message": f"Build configuration '{config.name}' created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating build config: {e}")
            return {"error": str(e)}
    
    async def execute_build(self, config_name: str, 
                          project_path: str) -> Dict[str, Any]:
        """Execute a build"""
        try:
            if config_name not in self.build_configs:
                return {"error": f"Build config '{config_name}' not found"}
            
            config = self.build_configs[config_name]
            self.stats["builds_performed"] += 1
            
            # Prepare build environment
            build_env = os.environ.copy()
            build_env.update(config.environment)
            
            # Create build directory
            build_dir = Path(project_path)
            if not build_dir.exists():
                return {"error": f"Project path '{project_path}' not found"}
            
            # Execute build command
            build_result = await self._execute_command(
                config.build_command,
                cwd=str(build_dir),
                env=build_env,
                timeout=config.timeout if hasattr(config, 'timeout') else 300
            )
            
            if not build_result["success"]:
                return {
                    "success": False,
                    "error": build_result["error"],
                    "logs": build_result["logs"]
                }
            
            # Execute test command if provided
            test_result = {"success": True, "logs": []}
            if config.test_command:
                test_result = await self._execute_command(
                    config.test_command,
                    cwd=str(build_dir),
                    env=build_env,
                    timeout=300
                )
            
            # Execute package command if provided
            package_result = {"success": True, "logs": []}
            if config.package_command:
                package_result = await self._execute_command(
                    config.package_command,
                    cwd=str(build_dir),
                    env=build_env,
                    timeout=300
                )
            
            # Collect artifacts
            artifacts = []
            for artifact_pattern in config.output_artifacts:
                artifact_files = list(build_dir.glob(artifact_pattern))
                artifacts.extend([str(f) for f in artifact_files])
            
            return {
                "success": True,
                "config_name": config_name,
                "build_logs": build_result["logs"],
                "test_logs": test_result["logs"],
                "package_logs": package_result["logs"],
                "artifacts": artifacts,
                "message": f"Build '{config_name}' completed successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error executing build: {e}")
            return {"error": str(e)}
    
    async def create_deployment_config(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Create a deployment configuration"""
        try:
            self.deployment_configs[config.name] = config
            
            return {
                "success": True,
                "config_name": config.name,
                "target": config.target,
                "message": f"Deployment configuration '{config.name}' created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating deployment config: {e}")
            return {"error": str(e)}
    
    async def execute_deployment(self, config_name: str, 
                                artifacts: List[str]) -> Dict[str, Any]:
        """Execute a deployment"""
        try:
            if config_name not in self.deployment_configs:
                return {"error": f"Deployment config '{config_name}' not found"}
            
            config = self.deployment_configs[config_name]
            self.stats["deployments_performed"] += 1
            
            # Create temporary deployment directory
            with tempfile.TemporaryDirectory() as temp_dir:
                deployment_dir = Path(temp_dir)
                
                # Copy artifacts to deployment directory
                for artifact in artifacts:
                    if Path(artifact).exists():
                        shutil.copy2(artifact, deployment_dir)
                
                # Prepare deployment environment
                deploy_env = os.environ.copy()
                deploy_env.update(config.environment_variables)
                
                # Execute deployment script
                if config.deployment_script:
                    deployment_result = await self._execute_command(
                        config.deployment_script,
                        cwd=str(deployment_dir),
                        env=deploy_env,
                        timeout=600
                    )
                    
                    if not deployment_result["success"]:
                        return {
                            "success": False,
                            "error": deployment_result["error"],
                            "logs": deployment_result["logs"]
                        }
                
                # Perform health check if configured
                health_check_result = {"success": True}
                if config.health_check_url:
                    health_check_result = await self._perform_health_check(
                        config.health_check_url,
                        config.health_check_timeout
                    )
                
                return {
                    "success": True,
                    "config_name": config_name,
                    "target_environment": config.target_environment,
                    "deployment_logs": deployment_result.get("logs", []),
                    "health_check": health_check_result,
                    "message": f"Deployment '{config_name}' completed successfully"
                }
                
        except Exception as e:
            self.logger.error(f"Error executing deployment: {e}")
            return {"error": str(e)}
    
    async def rollback_deployment(self, config_name: str) -> Dict[str, Any]:
        """Rollback a deployment"""
        try:
            if config_name not in self.deployment_configs:
                return {"error": f"Deployment config '{config_name}' not found"}
            
            config = self.deployment_configs[config_name]
            
            if not config.rollback_script:
                return {"error": f"No rollback script configured for '{config_name}'"}
            
            # Execute rollback script
            rollback_result = await self._execute_command(
                config.rollback_script,
                timeout=600
            )
            
            if not rollback_result["success"]:
                return {
                    "success": False,
                    "error": rollback_result["error"],
                    "logs": rollback_result["logs"]
                }
            
            return {
                "success": True,
                "config_name": config_name,
                "rollback_logs": rollback_result["logs"],
                "message": f"Rollback for '{config_name}' completed successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error rolling back deployment: {e}")
            return {"error": str(e)}
    
    async def generate_pipeline_config(self, pipeline_id: str, 
                                     format_type: str = "yaml") -> Dict[str, Any]:
        """Generate pipeline configuration file"""
        try:
            if pipeline_id not in self.pipelines:
                return {"error": f"Pipeline '{pipeline_id}' not found"}
            
            pipeline = self.pipelines[pipeline_id]
            
            # Convert pipeline to configuration format
            config = {
                "name": pipeline.name,
                "description": pipeline.description,
                "environment": pipeline.environment,
                "timeout": pipeline.timeout,
                "triggers": pipeline.triggers,
                "stages": []
            }
            
            for stage in pipeline.stages:
                stage_config = {
                    "name": stage.name,
                    "type": stage.type,
                    "commands": stage.commands,
                    "timeout": stage.timeout,
                    "retry_count": stage.retry_count,
                    "retry_delay": stage.retry_delay,
                    "on_failure": stage.on_failure,
                    "dependencies": stage.dependencies,
                    "environment": stage.environment,
                    "artifacts": stage.artifacts
                }
                config["stages"].append(stage_config)
            
            # Generate configuration file
            if format_type == "yaml":
                config_content = yaml.dump(config, default_flow_style=False)
                file_extension = ".yml"
            elif format_type == "json":
                config_content = json.dumps(config, indent=2)
                file_extension = ".json"
            else:
                return {"error": f"Unsupported format: {format_type}"}
            
            # Save configuration file
            config_file = Path(self.settings.workspace_dir) / "cicd" / f"{pipeline.name}{file_extension}"
            with open(config_file, 'w') as f:
                f.write(config_content)
            
            return {
                "success": True,
                "pipeline_id": pipeline_id,
                "format": format_type,
                "config_file": str(config_file),
                "message": f"Pipeline configuration generated as '{config_file}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating pipeline config: {e}")
            return {"error": str(e)}
    
    async def get_environment_info(self, environment_name: str) -> Dict[str, Any]:
        """Get environment information"""
        try:
            if environment_name not in self.environments:
                return {"error": f"Environment '{environment_name}' not found"}
            
            env = self.environments[environment_name]
            
            return {
                "success": True,
                "environment": env,
                "message": f"Environment '{environment_name}' information retrieved"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting environment info: {e}")
            return {"error": str(e)}
    
    async def monitor_deployments(self) -> Dict[str, Any]:
        """Monitor all deployments"""
        try:
            monitoring_data = {
                "active_executions": len(self.active_executions),
                "total_executions": len(self.pipeline_executions),
                "environments": {}
            }
            
            # Get status for each environment
            for env_name, env_config in self.environments.items():
                env_status = {
                    "name": env_name,
                    "type": env_config["type"],
                    "url": env_config.get("url", ""),
                    "health_check": "unknown"
                }
                
                # Perform health check if URL is available
                if env_config.get("url"):
                    health_result = await self._perform_health_check(env_config["url"], 10)
                    env_status["health_check"] = "healthy" if health_result["success"] else "unhealthy"
                
                monitoring_data["environments"][env_name] = env_status
            
            return {
                "success": True,
                "monitoring_data": monitoring_data,
                "message": "Deployment monitoring completed"
            }
            
        except Exception as e:
            self.logger.error(f"Error monitoring deployments: {e}")
            return {"error": str(e)}
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get DevOps & CI/CD statistics"""
        return {
            "success": True,
            "statistics": self.stats.copy(),
            "pipelines": len(self.pipelines),
            "build_configs": len(self.build_configs),
            "deployment_configs": len(self.deployment_configs),
            "environments": len(self.environments),
            "active_executions": len(self.active_executions)
        }
    
    async def _execute_pipeline_stages(self, pipeline: Pipeline, 
                                    execution: PipelineExecution) -> None:
        """Execute pipeline stages"""
        try:
            executed_stages = []
            
            for stage in pipeline.stages:
                # Check dependencies
                if stage.dependencies:
                    dependencies_met = all(
                        dep in executed_stages for dep in stage.dependencies
                    )
                    if not dependencies_met:
                        execution.status = "failed"
                        execution.error_message = f"Dependencies not met for stage '{stage.name}'"
                        break
                
                # Execute stage
                stage_result = await self._execute_stage(stage, pipeline.environment)
                executed_stages.append(stage.name)
                execution.stages.append(stage_result)
                
                # Check if stage failed
                if not stage_result["success"]:
                    if stage.on_failure == "stop":
                        execution.status = "failed"
                        execution.error_message = f"Stage '{stage.name}' failed"
                        break
                    elif stage.on_failure == "rollback":
                        # Execute rollback logic
                        await self._execute_rollback(pipeline, executed_stages)
                        execution.status = "failed"
                        execution.error_message = f"Stage '{stage.name}' failed, rollback executed"
                        break
                    # If on_failure is "continue", just log and continue
            
            # Mark execution as completed
            execution.end_time = datetime.now()
            if execution.status == "running":
                execution.status = "success"
                self.stats["successful_executions"] += 1
            else:
                self.stats["failed_executions"] += 1
            
            # Remove from active executions
            if execution.execution_id in self.active_executions:
                del self.active_executions[execution.execution_id]
            
        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.end_time = datetime.now()
            self.stats["failed_executions"] += 1
            
            if execution.execution_id in self.active_executions:
                del self.active_executions[execution.execution_id]
    
    async def _execute_stage(self, stage: PipelineStage, 
                           pipeline_env: str) -> Dict[str, Any]:
        """Execute a single pipeline stage"""
        try:
            stage_logs = []
            stage_artifacts = []
            
            # Prepare stage environment
            stage_env = os.environ.copy()
            stage_env.update(stage.environment)
            stage_env["PIPELINE_ENVIRONMENT"] = pipeline_env
            
            # Execute stage commands
            for command in stage.commands:
                command_result = await self._execute_command(
                    command,
                    env=stage_env,
                    timeout=stage.timeout
                )
                
                stage_logs.extend(command_result["logs"])
                
                if not command_result["success"]:
                    return {
                        "success": False,
                        "stage_name": stage.name,
                        "logs": stage_logs,
                        "error": command_result["error"]
                    }
            
            # Collect stage artifacts
            for artifact_pattern in stage.artifacts:
                artifact_files = list(Path(".").glob(artifact_pattern))
                stage_artifacts.extend([str(f) for f in artifact_files])
            
            return {
                "success": True,
                "stage_name": stage.name,
                "logs": stage_logs,
                "artifacts": stage_artifacts,
                "execution_time": 0  # Would calculate actual time
            }
            
        except Exception as e:
            return {
                "success": False,
                "stage_name": stage.name,
                "logs": [],
                "error": str(e)
            }
    
    async def _execute_rollback(self, pipeline: Pipeline, 
                               executed_stages: List[str]) -> None:
        """Execute rollback for failed pipeline"""
        try:
            # Find rollback stages (would need to be defined in pipeline)
            rollback_stages = [
                stage for stage in pipeline.stages 
                if stage.name in executed_stages and hasattr(stage, 'rollback_command')
            ]
            
            # Execute rollback in reverse order
            for stage in reversed(rollback_stages):
                if hasattr(stage, 'rollback_command'):
                    await self._execute_command(stage.rollback_command)
                    
        except Exception as e:
            self.logger.error(f"Error during rollback: {e}")
    
    async def _execute_command(self, command: str, cwd: Optional[str] = None,
                            env: Optional[Dict[str, str]] = None,
                            timeout: int = 300) -> Dict[str, Any]:
        """Execute a shell command"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds",
                    "logs": []
                }
            
            logs = []
            if stdout:
                logs.extend(stdout.decode().strip().split('\n'))
            if stderr:
                logs.extend(stderr.decode().strip().split('\n'))
            
            return {
                "success": process.returncode == 0,
                "logs": logs,
                "error": stderr.decode().strip() if process.returncode != 0 else ""
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "logs": []
            }
    
    async def _perform_health_check(self, url: str, timeout: int) -> Dict[str, Any]:
        """Perform health check on a URL"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    return {
                        "success": response.status < 400,
                        "status_code": response.status,
                        "response_time": 0  # Would calculate actual time
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }