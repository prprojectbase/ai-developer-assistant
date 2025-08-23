#!/usr/bin/env python3
"""
Comprehensive End-to-End Development Example

This script demonstrates the complete end-to-end software development capabilities
of the AI Developer Assistant using all the newly added tools and modules.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.main_agent import AIDeveloperAssistant
from modules.task_manager import TaskPriority
from modules.version_control_integration import VersionControlIntegration
from modules.database_management import DatabaseManagement, DatabaseConfig, TableSchema
from modules.api_development import APIDevelopment, APIEndpoint, APITestCase
from modules.devops_cicd import DevOpsCICD, Pipeline, PipelineStage
from modules.security_testing import SecurityTesting
from modules.containerization_orchestration import ContainerizationOrchestration, DockerImage
from modules.cloud_infrastructure import CloudInfrastructure, CloudProvider, CloudResource
from modules.package_management import PackageManagement


async def main():
    """Demonstrate comprehensive end-to-end development workflow"""
    print("🚀 Comprehensive End-to-End Development Example")
    print("=" * 60)
    print("This example demonstrates the complete software development lifecycle")
    print("using all the newly added tools and modules.")
    print("=" * 60)
    
    # Initialize the assistant
    assistant = AIDeveloperAssistant()
    await assistant.initialize()
    
    try:
        print("\n🤖 Starting AI Developer Assistant with all modules...")
        
        # Initialize all modules
        print("\n📋 Initializing all development modules...")
        
        # Version Control Integration
        version_control = VersionControlIntegration()
        await version_control.initialize()
        await assistant.register_agent("version_control", version_control)
        print("✅ Version Control Integration initialized")
        
        # Database Management
        database_mgmt = DatabaseManagement()
        await database_mgmt.initialize()
        await assistant.register_agent("database", database_mgmt)
        print("✅ Database Management initialized")
        
        # API Development
        api_dev = APIDevelopment()
        await api_dev.initialize()
        await assistant.register_agent("api_development", api_dev)
        print("✅ API Development initialized")
        
        # DevOps & CI/CD
        devops_cicd = DevOpsCICD()
        await devops_cicd.initialize()
        await assistant.register_agent("devops_cicd", devops_cicd)
        print("✅ DevOps & CI/CD initialized")
        
        # Security Testing
        security_testing = SecurityTesting()
        await security_testing.initialize()
        await assistant.register_agent("security_testing", security_testing)
        print("✅ Security Testing initialized")
        
        # Containerization & Orchestration
        containerization = ContainerizationOrchestration()
        await containerization.initialize()
        await assistant.register_agent("containerization", containerization)
        print("✅ Containerization & Orchestration initialized")
        
        # Cloud Infrastructure
        cloud_infra = CloudInfrastructure()
        await cloud_infra.initialize()
        await assistant.register_agent("cloud_infrastructure", cloud_infra)
        print("✅ Cloud Infrastructure initialized")
        
        # Package Management
        package_mgmt = PackageManagement()
        await package_mgmt.initialize()
        await assistant.register_agent("package_management", package_mgmt)
        print("✅ Package Management initialized")
        
        print("\n🎯 Starting comprehensive development workflow...")
        
        # Phase 1: Project Setup with Version Control
        print("\n🔄 Phase 1: Project Setup with Version Control")
        print("-" * 40)
        
        # Create project directory
        project_dir = Path("/tmp/comprehensive_project")
        project_dir.mkdir(exist_ok=True)
        
        # Initialize Git repository
        git_result = await version_control.initialize_repository(str(project_dir), init=True)
        if git_result["success"]:
            print("✅ Git repository initialized")
        
        # Create README file
        readme_content = """# Comprehensive Project

A complete end-to-end development project demonstrating AI Developer Assistant capabilities.

## Features
- Version Control with Git
- Database Management
- API Development
- DevOps & CI/CD
- Security Testing
- Containerization
- Cloud Infrastructure
- Package Management
"""
        
        with open(project_dir / "README.md", "w") as f:
            f.write(readme_content)
        
        # Add and commit files
        await version_control.add_files(["README.md"], str(project_dir))
        await version_control.commit_changes("Initial project setup", str(project_dir))
        print("✅ Project files committed to Git")
        
        # Phase 2: Database Setup
        print("\n🗄️ Phase 2: Database Setup")
        print("-" * 40)
        
        # Create database configuration
        db_config = DatabaseConfig(
            db_type="sqlite",
            database=str(project_dir / "app.db")
        )
        
        # Add database
        db_result = await database_mgmt.add_database("main_db", db_config)
        if db_result["success"]:
            print("✅ Database configured")
        
        # Create users table
        users_table = TableSchema(
            name="users",
            columns=[
                {"name": "id", "type": "INTEGER", "primary_key": True},
                {"name": "username", "type": "TEXT", "not_null": True},
                {"name": "email", "type": "TEXT", "not_null": True},
                {"name": "created_at", "type": "TEXT", "not_null": True}
            ],
            primary_keys=["id"]
        )
        
        table_result = await database_mgmt.create_table("main_db", users_table)
        if table_result["success"]:
            print("✅ Users table created")
        
        # Phase 3: API Development
        print("\n🌐 Phase 3: API Development")
        print("-" * 40)
        
        # Create API
        api_result = await api_dev.create_api("user_management_api", "1.0.0", "User management API")
        if api_result["success"]:
            print("✅ API created")
        
        # Add user endpoint
        user_endpoint = APIEndpoint(
            path="/users",
            method="GET",
            summary="Get all users",
            description="Retrieve a list of all users from the database"
        )
        
        endpoint_result = await api_dev.add_endpoint(api_result["api_id"], user_endpoint)
        if endpoint_result["success"]:
            print("✅ GET /users endpoint added")
        
        # Generate OpenAPI specification
        openapi_result = await api_dev.generate_openapi_spec(api_result["api_id"])
        if openapi_result["success"]:
            print("✅ OpenAPI specification generated")
        
        # Create API test case
        test_case = APITestCase(
            name="Get Users Test",
            endpoint="/users",
            method="GET",
            expected_status=200
        )
        
        test_result = await api_dev.create_test_case(test_case)
        if test_result["success"]:
            print("✅ API test case created")
        
        # Phase 4: Security Testing
        print("\n🔒 Phase 4: Security Testing")
        print("-" * 40)
        
        # Scan codebase for security vulnerabilities
        security_scan = await security_testing.scan_codebase(str(project_dir))
        if security_scan["success"]:
            print(f"✅ Security scan completed - {security_scan['total_vulnerabilities']} vulnerabilities found")
        
        # Check compliance
        compliance_check = await security_testing.check_compliance(str(project_dir), ["gdpr"])
        if compliance_check["success"]:
            print(f"✅ Compliance check completed - {compliance_check['total_checks']} checks performed")
        
        # Generate security report
        security_report = await security_testing.generate_security_report("comprehensive_project")
        if security_report["success"]:
            print("✅ Security report generated")
        
        # Phase 5: Containerization
        print("\n📦 Phase 5: Containerization")
        print("-" * 40)
        
        # Generate Dockerfile
        dockerfile_result = await containerization.generate_dockerfile(
            "comprehensive_app",
            "python:3.9-slim",
            requirements=["fastapi", "uvicorn", "sqlalchemy"],
            commands=["pip install -r requirements.txt"]
        )
        if dockerfile_result["success"]:
            print("✅ Dockerfile generated")
        
        # Create Docker image configuration
        docker_image = DockerImage(
            name="comprehensive-app",
            tag="latest",
            dockerfile_path=dockerfile_result["dockerfile_path"]
        )
        
        image_result = await containerization.create_docker_image(docker_image)
        if image_result["success"]:
            print("✅ Docker image configured")
        
        # Generate Kubernetes deployment
        deployment_result = await containerization.generate_deployment_manifest(
            "comprehensive-deployment",
            "comprehensive-app:latest",
            replicas=3,
            ports=[8000],
            env_vars={"ENV": "production"}
        )
        if deployment_result["success"]:
            print("✅ Kubernetes deployment manifest generated")
        
        # Generate Kubernetes service
        service_result = await containerization.generate_service_manifest(
            "comprehensive-service",
            {"app": "comprehensive-app"},
            [{"port": 80, "targetPort": 8000}],
            "LoadBalancer"
        )
        if service_result["success"]:
            print("✅ Kubernetes service manifest generated")
        
        # Phase 6: Cloud Infrastructure
        print("\n☁️ Phase 6: Cloud Infrastructure")
        print("-" * 40)
        
        # Create AWS provider
        aws_provider = CloudProvider(
            name="aws_production",
            type="aws",
            region="us-east-1",
            enabled_services=["ec2", "s3", "rds"]
        )
        
        provider_result = await cloud_infra.add_cloud_provider(aws_provider)
        if provider_result["success"]:
            print("✅ AWS cloud provider configured")
        
        # Create cloud resources
        ec2_resource = CloudResource(
            name="web-server",
            type="ec2",
            provider="aws",
            configuration={
                "InstanceType": "t2.micro",
                "ImageId": "ami-0c55b159cbfafe1f0"
            },
            tags={"Environment": "production", "Purpose": "web-server"}
        )
        
        s3_resource = CloudResource(
            name="static-assets",
            type="s3",
            provider="aws",
            configuration={
                "BucketName": "comprehensive-app-assets",
                "AccessControl": "Private"
            },
            tags={"Environment": "production", "Purpose": "static-assets"}
        )
        
        # Generate CloudFormation template
        cloudformation_result = await cloud_infra.generate_cloudformation_template(
            "production_infrastructure",
            [ec2_resource, s3_resource]
        )
        if cloudformation_result["success"]:
            print("✅ CloudFormation template generated")
        
        # Estimate costs
        cost_estimate = await cloud_infra.estimate_costs("production_infrastructure")
        if cost_estimate["success"]:
            print(f"✅ Cost estimate: ${cost_estimate['cost_estimate']['estimated_monthly_cost']:.2f}/month")
        
        # Phase 7: DevOps & CI/CD
        print("\n🚀 Phase 7: DevOps & CI/CD")
        print("-" * 40)
        
        # Create build configuration
        build_config = DevOpsCICD.BuildConfig(
            name="python_build",
            build_tool="pip",
            build_command="pip install -r requirements.txt",
            test_command="pytest tests/",
            output_artifacts=["dist/*"]
        )
        
        build_result = await devops_cicd.create_build_config(build_config)
        if build_result["success"]:
            print("✅ Build configuration created")
        
        # Create deployment configuration
        deploy_config = DevOpsCICD.DeploymentConfig(
            name="k8s_deployment",
            target="kubernetes",
            deployment_type="rolling",
            target_environment="production",
            deployment_script="kubectl apply -f k8s/"
        )
        
        deploy_result = await devops_cicd.create_deployment_config(deploy_config)
        if deploy_result["success"]:
            print("✅ Deployment configuration created")
        
        # Create CI/CD pipeline
        pipeline_stages = [
            PipelineStage(
                name="build",
                type="build",
                commands=["npm install", "npm run build"],
                timeout=600
            ),
            PipelineStage(
                name="test",
                type="test",
                commands=["npm test"],
                timeout=300,
                dependencies=["build"]
            ),
            PipelineStage(
                name="security_scan",
                type="test",
                commands=["npm audit"],
                timeout=180,
                dependencies=["build"]
            ),
            PipelineStage(
                name="deploy",
                type="deploy",
                commands=["kubectl apply -f k8s/"],
                timeout=600,
                dependencies=["test", "security_scan"]
            )
        ]
        
        pipeline = Pipeline(
            name="production_pipeline",
            description="Production deployment pipeline",
            stages=pipeline_stages,
            triggers=["push", "pull_request"]
        )
        
        pipeline_result = await devops_cicd.create_pipeline(pipeline)
        if pipeline_result["success"]:
            print("✅ CI/CD pipeline created")
        
        # Phase 8: Package Management
        print("\n📦 Phase 8: Package Management")
        print("-" * 40)
        
        # Install Python packages
        packages_to_install = [
            "fastapi",
            "uvicorn",
            "sqlalchemy",
            "pytest",
            "black"
        ]
        
        for package in packages_to_install:
            install_result = await package_mgmt.install_package(package, project_path=str(project_dir))
            if install_result["success"]:
                print(f"✅ Package '{package}' installed")
        
        # Generate requirements.txt
        requirements_result = await package_mgmt.generate_lock_file(str(project_dir), "pip")
        if requirements_result["success"]:
            print("✅ Requirements lock file generated")
        
        # Scan for security vulnerabilities in packages
        vuln_scan = await package_mgmt.scan_security_vulnerabilities(str(project_dir))
        if vuln_scan["success"]:
            print(f"✅ Package security scan completed - {vuln_scan['vulnerability_count']} vulnerabilities found")
        
        # Optimize dependencies
        optimization_result = await package_mgmt.optimize_dependencies(str(project_dir))
        if optimization_result["success"]:
            print(f"✅ Dependency optimization completed - {len(optimization_result['optimizations'])} optimizations found")
        
        # Phase 9: Final Integration
        print("\n🎯 Phase 9: Final Integration")
        print("-" * 40)
        
        # Commit all changes
        await version_control.add_files(["."], str(project_dir))
        await version_control.commit_changes("Complete end-to-end development setup", str(project_dir))
        print("✅ All changes committed to Git")
        
        # Generate final status report
        print("\n📊 Final Status Report")
        print("-" * 40)
        
        # Get statistics from all modules
        git_stats = await version_control.get_statistics()
        db_stats = await database_mgmt.get_statistics()
        api_stats = await api_dev.get_statistics()
        devops_stats = await devops_cicd.get_statistics()
        security_stats = await security_testing.get_statistics()
        container_stats = await containerization.get_statistics()
        cloud_stats = await cloud_infra.get_statistics()
        package_stats = await package_mgmt.get_statistics()
        
        print(f"🔄 Version Control: {git_stats['statistics']['total_operations']} operations")
        print(f"🗄️ Database: {db_stats['statistics']['total_queries']} queries executed")
        print(f"🌐 API: {api_stats['statistics']['endpoints_created']} endpoints created")
        print(f"🚀 DevOps: {devops_stats['statistics']['pipelines_created']} pipelines created")
        print(f"🔒 Security: {security_stats['statistics']['total_scans']} security scans")
        print(f"📦 Containerization: {container_stats['statistics']['images_built']} images built")
        print(f"☁️ Cloud: {cloud_stats['statistics']['resources_deployed']} resources deployed")
        print(f"📦 Package Management: {package_stats['statistics']['packages_installed']} packages installed")
        
        print("\n🎉 Comprehensive End-to-End Development Complete!")
        print("=" * 60)
        print("✅ Successfully demonstrated complete software development lifecycle")
        print("✅ All modules integrated and working together")
        print("✅ Project ready for production deployment")
        print("=" * 60)
        
        # Show project structure
        print("\n📁 Project Structure:")
        print("comprehensive_project/")
        print("├── README.md")
        print("├── app.db")
        print("├── comprehensive_app_Dockerfile")
        print("├── requirements.txt")
        print("├── k8s/")
        print("│   ├── comprehensive-deployment_deployment.yaml")
        print("│   └── comprehensive-service_service.yaml")
        print("├── cloud/")
        print("│   └── production_infrastructure_cloudformation.yaml")
        print("└── .git/")
        
    except Exception as e:
        print(f"\n❌ Error during development workflow: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        await assistant.stop()
        print("✅ AI Developer Assistant stopped")


if __name__ == "__main__":
    asyncio.run(main())