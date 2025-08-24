#!/usr/bin/env python3
"""
Containerization & Orchestration Module

Provides comprehensive containerization and orchestration tools including
Docker, Kubernetes, and container lifecycle management for the AI Developer Assistant.
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
import os

from ..config.settings import get_settings


@dataclass
class DockerImage:
    """Docker image configuration"""
    name: str
    tag: str = "latest"
    dockerfile_path: str = "Dockerfile"
    build_context: str = "."
    build_args: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    ports: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)


@dataclass
class ContainerConfig:
    """Container configuration"""
    name: str
    image: str
    ports: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    networks: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    restart_policy: str = "unless-stopped"


@dataclass
class KubernetesManifest:
    """Kubernetes manifest configuration"""
    kind: str  # Deployment, Service, ConfigMap, Secret, etc.
    name: str
    namespace: str = "default"
    spec: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComposeService:
    """Docker Compose service configuration"""
    name: str
    image: str
    build: Optional[Dict[str, Any]] = None
    ports: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    networks: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)


class ContainerizationOrchestration:
    """Containerization and orchestration management tools"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Docker configurations
        self.docker_images: Dict[str, DockerImage] = {}
        self.container_configs: Dict[str, ContainerConfig] = {}
        
        # Kubernetes configurations
        self.kubernetes_manifests: Dict[str, KubernetesManifest] = {}
        
        # Docker Compose configurations
        self.compose_services: Dict[str, ComposeService] = {}
        self.compose_files: Dict[str, str] = {}
        
        # Container registry
        self.registries: Dict[str, Dict[str, Any]] = {}
        
        # Statistics
        self.stats = {
            "images_built": 0,
            "containers_created": 0,
            "manifests_generated": 0,
            "compose_files_generated": 0,
            "deployments_performed": 0
        }
    
    async def initialize(self) -> None:
        """Initialize the containerization and orchestration tools"""
        self.logger.info("Initializing Containerization & Orchestration...")
        
        # Create workspace
        container_workspace = Path(self.settings.workspace_dir) / "containers"
        container_workspace.mkdir(parents=True, exist_ok=True)
        
        # Check if Docker is available
        try:
            result = await self._run_command(["docker", "--version"])
            self.logger.info(f"Docker version: {result.strip()}")
        except Exception as e:
            self.logger.warning(f"Docker not available: {e}")
        
        # Check if kubectl is available
        try:
            result = await self._run_command(["kubectl", "version", "--client"])
            self.logger.info(f"kubectl version: {result.strip()}")
        except Exception as e:
            self.logger.warning(f"kubectl not available: {e}")
        
        # Initialize default registries
        self.registries = {
            "dockerhub": {
                "url": "https://registry.hub.docker.com",
                "auth_required": False
            },
            "github": {
                "url": "https://ghcr.io",
                "auth_required": True
            }
        }
        
        self.logger.info("Containerization & Orchestration initialized successfully")
    
    async def stop(self) -> None:
        """Stop the containerization and orchestration tools"""
        self.logger.info("Stopping Containerization & Orchestration...")
        self.logger.info("Containerization & Orchestration stopped")
    
    async def create_docker_image(self, image: DockerImage) -> Dict[str, Any]:
        """Create a Docker image configuration"""
        try:
            image_id = f"{image.name}:{image.tag}"
            self.docker_images[image_id] = image
            
            return {
                "success": True,
                "image_id": image_id,
                "name": image.name,
                "tag": image.tag,
                "message": f"Docker image '{image_id}' configured successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating Docker image: {e}")
            return {"error": str(e)}
    
    async def build_docker_image(self, image_name: str, tag: str = "latest") -> Dict[str, Any]:
        """Build a Docker image"""
        try:
            image_id = f"{image_name}:{tag}"
            if image_id not in self.docker_images:
                return {"error": f"Docker image '{image_id}' not found"}
            
            image = self.docker_images[image_id]
            
            # Prepare build command
            build_cmd = ["docker", "build"]
            
            # Add tag
            build_cmd.extend(["-t", image_id])
            
            # Add build args
            for key, value in image.build_args.items():
                build_cmd.extend(["--build-arg", f"{key}={value}"])
            
            # Add build context
            build_cmd.append(image.build_context)
            
            # Add Dockerfile path if different from default
            if image.dockerfile_path != "Dockerfile":
                build_cmd.extend(["-f", image.dockerfile_path])
            
            # Build image
            result = await self._run_command(build_cmd)
            
            self.stats["images_built"] += 1
            
            return {
                "success": True,
                "image_id": image_id,
                "build_output": result,
                "message": f"Docker image '{image_id}' built successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error building Docker image: {e}")
            return {"error": str(e)}
    
    async def create_container(self, config: ContainerConfig) -> Dict[str, Any]:
        """Create a container configuration"""
        try:
            self.container_configs[config.name] = config
            
            return {
                "success": True,
                "container_name": config.name,
                "image": config.image,
                "message": f"Container '{config.name}' configured successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating container: {e}")
            return {"error": str(e)}
    
    async def run_container(self, container_name: str) -> Dict[str, Any]:
        """Run a container"""
        try:
            if container_name not in self.container_configs:
                return {"error": f"Container '{container_name}' not found"}
            
            config = self.container_configs[container_name]
            
            # Prepare run command
            run_cmd = ["docker", "run", "-d", "--name", container_name]
            
            # Add restart policy
            run_cmd.extend(["--restart", config.restart_policy])
            
            # Add ports
            for port_mapping in config.ports:
                run_cmd.extend(["-p", port_mapping])
            
            # Add volumes
            for volume_mapping in config.volumes:
                run_cmd.extend(["-v", volume_mapping])
            
            # Add environment variables
            for key, value in config.environment.items():
                run_cmd.extend(["-e", f"{key}={value}"])
            
            # Add networks
            for network in config.networks:
                run_cmd.extend(["--network", network])
            
            # Add image
            run_cmd.append(config.image)
            
            # Run container
            result = await self._run_command(run_cmd)
            
            self.stats["containers_created"] += 1
            
            return {
                "success": True,
                "container_name": container_name,
                "container_id": result.strip(),
                "message": f"Container '{container_name}' started successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error running container: {e}")
            return {"error": str(e)}
    
    async def generate_dockerfile(self, image_name: str, base_image: str = "python:3.9-slim",
                                 requirements: List[str] = None,
                                 commands: List[str] = None) -> Dict[str, Any]:
        """Generate a Dockerfile"""
        try:
            dockerfile_content = f"FROM {base_image}\n\n"
            
            # Set working directory
            dockerfile_content += "WORKDIR /app\n\n"
            
            # Copy requirements if provided
            if requirements:
                dockerfile_content += "COPY requirements.txt .\n"
                dockerfile_content += "RUN pip install --no-cache-dir -r requirements.txt\n\n"
            
            # Copy application code
            dockerfile_content += "COPY . .\n\n"
            
            # Add custom commands
            if commands:
                for cmd in commands:
                    dockerfile_content += f"RUN {cmd}\n"
                dockerfile_content += "\n"
            
            # Expose port (default to 8000)
            dockerfile_content += "EXPOSE 8000\n\n"
            
            # Set default command
            dockerfile_content += 'CMD ["python", "app.py"]\n'
            
            # Save Dockerfile
            dockerfile_path = Path(self.settings.workspace_dir) / "containers" / f"{image_name}_Dockerfile"
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            # Create Docker image configuration
            image = DockerImage(
                name=image_name,
                dockerfile_path=str(dockerfile_path)
            )
            await self.create_docker_image(image)
            
            return {
                "success": True,
                "image_name": image_name,
                "dockerfile_path": str(dockerfile_path),
                "message": f"Dockerfile generated for '{image_name}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating Dockerfile: {e}")
            return {"error": str(e)}
    
    async def generate_kubernetes_manifest(self, manifest: KubernetesManifest) -> Dict[str, Any]:
        """Generate a Kubernetes manifest"""
        try:
            # Create Kubernetes manifest YAML
            k8s_manifest = {
                "apiVersion": "apps/v1",
                "kind": manifest.kind,
                "metadata": {
                    "name": manifest.name,
                    "namespace": manifest.namespace,
                    **manifest.metadata
                },
                "spec": manifest.spec
            }
            
            # Convert to YAML
            manifest_yaml = yaml.dump(k8s_manifest, default_flow_style=False)
            
            # Save manifest
            manifest_path = Path(self.settings.workspace_dir) / "k8s" / f"{manifest.name}_{manifest.kind.lower()}.yaml"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(manifest_path, 'w') as f:
                f.write(manifest_yaml)
            
            self.kubernetes_manifests[f"{manifest.name}_{manifest.kind}"] = manifest
            self.stats["manifests_generated"] += 1
            
            return {
                "success": True,
                "manifest_name": f"{manifest.name}_{manifest.kind}",
                "manifest_path": str(manifest_path),
                "message": f"Kubernetes manifest generated for '{manifest.name}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating Kubernetes manifest: {e}")
            return {"error": str(e)}
    
    async def generate_deployment_manifest(self, name: str, image: str, replicas: int = 3,
                                         ports: List[int] = None,
                                         env_vars: Dict[str, str] = None) -> Dict[str, Any]:
        """Generate a Kubernetes Deployment manifest"""
        try:
            container_spec = {
                "name": name,
                "image": image,
                "ports": [{"containerPort": port} for port in (ports or [80])]
            }
            
            if env_vars:
                container_spec["env"] = [
                    {"name": key, "value": value} for key, value in env_vars.items()
                ]
            
            manifest = KubernetesManifest(
                kind="Deployment",
                name=name,
                spec={
                    "replicas": replicas,
                    "selector": {
                        "matchLabels": {
                            "app": name
                        }
                    },
                    "template": {
                        "metadata": {
                            "labels": {
                                "app": name
                            }
                        },
                        "spec": {
                            "containers": [container_spec]
                        }
                    }
                }
            )
            
            return await self.generate_kubernetes_manifest(manifest)
            
        except Exception as e:
            self.logger.error(f"Error generating deployment manifest: {e}")
            return {"error": str(e)}
    
    async def generate_service_manifest(self, name: str, selector: Dict[str, str],
                                      ports: List[Dict[str, Any]], service_type: str = "ClusterIP") -> Dict[str, Any]:
        """Generate a Kubernetes Service manifest"""
        try:
            manifest = KubernetesManifest(
                kind="Service",
                name=name,
                spec={
                    "type": service_type,
                    "selector": selector,
                    "ports": ports
                }
            )
            
            return await self.generate_kubernetes_manifest(manifest)
            
        except Exception as e:
            self.logger.error(f"Error generating service manifest: {e}")
            return {"error": str(e)}
    
    async def create_compose_service(self, service: ComposeService) -> Dict[str, Any]:
        """Create a Docker Compose service configuration"""
        try:
            self.compose_services[service.name] = service
            
            return {
                "success": True,
                "service_name": service.name,
                "image": service.image,
                "message": f"Docker Compose service '{service.name}' configured successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating compose service: {e}")
            return {"error": str(e)}
    
    async def generate_docker_compose(self, compose_name: str, 
                                    services: List[ComposeService] = None) -> Dict[str, Any]:
        """Generate a Docker Compose file"""
        try:
            if services is None:
                services = list(self.compose_services.values())
            
            compose_config = {
                "version": "3.8",
                "services": {}
            }
            
            for service in services:
                service_config = {
                    "image": service.image
                }
                
                if service.build:
                    service_config["build"] = service.build
                
                if service.ports:
                    service_config["ports"] = service.ports
                
                if service.volumes:
                    service_config["volumes"] = service.volumes
                
                if service.environment:
                    service_config["environment"] = service.environment
                
                if service.networks:
                    service_config["networks"] = service.networks
                
                if service.depends_on:
                    service_config["depends_on"] = service.depends_on
                
                compose_config["services"][service.name] = service_config
            
            # Convert to YAML
            compose_yaml = yaml.dump(compose_config, default_flow_style=False)
            
            # Save compose file
            compose_path = Path(self.settings.workspace_dir) / "compose" / f"{compose_name}_docker-compose.yml"
            compose_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(compose_path, 'w') as f:
                f.write(compose_yaml)
            
            self.compose_files[compose_name] = str(compose_path)
            self.stats["compose_files_generated"] += 1
            
            return {
                "success": True,
                "compose_name": compose_name,
                "compose_path": str(compose_path),
                "services_count": len(services),
                "message": f"Docker Compose file generated for '{compose_name}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating Docker Compose: {e}")
            return {"error": str(e)}
    
    async def deploy_to_kubernetes(self, manifest_path: str) -> Dict[str, Any]:
        """Deploy to Kubernetes cluster"""
        try:
            # Apply Kubernetes manifest
            result = await self._run_command(["kubectl", "apply", "-f", manifest_path])
            
            self.stats["deployments_performed"] += 1
            
            return {
                "success": True,
                "manifest_path": manifest_path,
                "deployment_output": result,
                "message": "Deployment to Kubernetes completed successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error deploying to Kubernetes: {e}")
            return {"error": str(e)}
    
    async def scale_deployment(self, deployment_name: str, replicas: int,
                             namespace: str = "default") -> Dict[str, Any]:
        """Scale a Kubernetes deployment"""
        try:
            result = await self._run_command([
                "kubectl", "scale", "deployment", deployment_name,
                "--replicas", str(replicas), "-n", namespace
            ])
            
            return {
                "success": True,
                "deployment_name": deployment_name,
                "replicas": replicas,
                "namespace": namespace,
                "scale_output": result,
                "message": f"Deployment '{deployment_name}' scaled to {replicas} replicas"
            }
            
        except Exception as e:
            self.logger.error(f"Error scaling deployment: {e}")
            return {"error": str(e)}
    
    async def get_cluster_status(self, namespace: str = "default") -> Dict[str, Any]:
        """Get Kubernetes cluster status"""
        try:
            # Get pods status
            pods_result = await self._run_command(["kubectl", "get", "pods", "-n", namespace])
            
            # Get services status
            services_result = await self._run_command(["kubectl", "get", "services", "-n", namespace])
            
            # Get deployments status
            deployments_result = await self._run_command(["kubectl", "get", "deployments", "-n", namespace])
            
            return {
                "success": True,
                "namespace": namespace,
                "pods": pods_result,
                "services": services_result,
                "deployments": deployments_result,
                "message": f"Cluster status retrieved for namespace '{namespace}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cluster status: {e}")
            return {"error": str(e)}
    
    async def create_namespace(self, namespace_name: str) -> Dict[str, Any]:
        """Create a Kubernetes namespace"""
        try:
            result = await self._run_command(["kubectl", "create", "namespace", namespace_name])
            
            return {
                "success": True,
                "namespace_name": namespace_name,
                "create_output": result,
                "message": f"Namespace '{namespace_name}' created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating namespace: {e}")
            return {"error": str(e)}
    
    async def push_image_to_registry(self, image_name: str, tag: str = "latest",
                                   registry: str = "dockerhub") -> Dict[str, Any]:
        """Push Docker image to registry"""
        try:
            image_id = f"{image_name}:{tag}"
            
            if registry not in self.registries:
                return {"error": f"Registry '{registry}' not configured"}
            
            registry_config = self.registries[registry]
            
            # Tag image for registry
            registry_image = f"{registry_config['url'].split('//')[-1]}/{image_name}:{tag}"
            await self._run_command(["docker", "tag", image_id, registry_image])
            
            # Push image
            result = await self._run_command(["docker", "push", registry_image])
            
            return {
                "success": True,
                "image_id": image_id,
                "registry": registry,
                "registry_image": registry_image,
                "push_output": result,
                "message": f"Image '{image_id}' pushed to '{registry}' registry"
            }
            
        except Exception as e:
            self.logger.error(f"Error pushing image to registry: {e}")
            return {"error": str(e)}
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get containerization and orchestration statistics"""
        return {
            "success": True,
            "statistics": self.stats.copy(),
            "docker_images": len(self.docker_images),
            "container_configs": len(self.container_configs),
            "kubernetes_manifests": len(self.kubernetes_manifests),
            "compose_services": len(self.compose_services),
            "registries": len(self.registries)
        }
    
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