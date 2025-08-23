import asyncio
import logging
import json
import os
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import re
import networkx as nx
from enum import Enum
import yaml
import xml.etree.ElementTree as ET

from ..config.settings import get_settings


class IntegrationType(Enum):
    """Types of system integrations"""
    API = "api"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    FILE_SYSTEM = "file_system"
    WEBHOOK = "webhook"
    THIRD_PARTY = "third_party"
    MICROSERVICE = "microservice"
    LEGACY_SYSTEM = "legacy_system"


class ComplexityLevel(Enum):
    """Integration complexity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IntegrationStatus(Enum):
    """Integration status"""
    PLANNED = "planned"
    IN_DEVELOPMENT = "in_development"
    TESTING = "testing"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    FAILED = "failed"


@dataclass
class IntegrationPoint:
    """Integration point representation"""
    id: str
    name: str
    type: IntegrationType
    source_system: str
    target_system: str
    description: str
    protocol: str
    data_format: str
    complexity_level: ComplexityLevel
    status: IntegrationStatus
    dependencies: List[str]
    risk_factors: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationDependency:
    """Integration dependency representation"""
    source_integration: str
    target_integration: str
    dependency_type: str
    strength: float  # 0.0 to 1.0
    description: str
    critical_path: bool = False


@dataclass
class IntegrationRisk:
    """Integration risk representation"""
    id: str
    integration_id: str
    risk_type: str
    severity: str
    probability: float
    impact: str
    mitigation_strategy: str
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class IntegrationTest:
    """Integration test representation"""
    id: str
    integration_id: str
    test_type: str
    description: str
    test_data: Dict[str, Any]
    expected_result: str
    actual_result: Optional[str] = None
    status: str = "pending"
    executed_at: Optional[datetime] = None


class IntegrationComplexityManager:
    """Manager for handling integration complexity in software systems"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Integration storage
        self.integrations: Dict[str, IntegrationPoint] = {}
        self.dependencies: List[IntegrationDependency] = []
        self.risks: List[IntegrationRisk] = []
        self.tests: List[IntegrationTest] = []
        
        # Integration graph
        self.integration_graph = nx.DiGraph()
        
        # Complexity metrics
        self.complexity_metrics = {
            "total_integrations": 0,
            "critical_integrations": 0,
            "average_complexity": 0,
            "dependency_depth": 0,
            "risk_score": 0,
            "test_coverage": 0
        }
        
        # Integration patterns
        self.integration_patterns = self._load_integration_patterns()
        
        # Risk assessment matrix
        self.risk_matrix = self._load_risk_matrix()
        
        # Best practices database
        self.best_practices = self._load_best_practices()
        
        # Integration templates
        self.integration_templates = self._load_integration_templates()
        
        # Monitoring configuration
        self.monitoring_config = {
            "health_check_interval": 60,  # seconds
            "performance_thresholds": {
                "response_time": 5000,  # ms
                "error_rate": 0.05,  # 5%
                "availability": 0.99  # 99%
            },
            "alert_thresholds": {
                "consecutive_failures": 3,
                "response_time_degradation": 2000,  # ms
                "error_rate_spike": 0.1  # 10%
            }
        }
        
        # Historical data
        self.historical_performance: Dict[str, List[Dict[str, Any]]] = {}
        self.integration_trends: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self) -> None:
        """Initialize the integration complexity manager"""
        self.logger.info("Initializing Integration Complexity Manager...")
        
        # Load existing integrations
        await self._load_existing_integrations()
        
        # Initialize integration graph
        await self._initialize_integration_graph()
        
        # Calculate initial metrics
        await self._calculate_complexity_metrics()
        
        self.logger.info("Integration Complexity Manager initialized")
    
    async def analyze_integration_complexity(self, project_path: str) -> Dict[str, Any]:
        """Analyze integration complexity in a project"""
        self.logger.info(f"Analyzing integration complexity for: {project_path}")
        
        try:
            analysis_results = {
                "analysis_id": f"integration_{int(datetime.now().timestamp())}",
                "project_path": project_path,
                "analyzed_at": datetime.now(),
                "discovered_integrations": [],
                "complexity_assessment": {},
                "dependency_analysis": {},
                "risk_assessment": {},
                "recommendations": [],
                "integration_map": {}
            }
            
            # Discover integrations
            discovered_integrations = await self._discover_integrations(project_path)
            analysis_results["discovered_integrations"] = discovered_integrations
            
            # Assess complexity
            complexity_assessment = await self._assess_integration_complexity(discovered_integrations)
            analysis_results["complexity_assessment"] = complexity_assessment
            
            # Analyze dependencies
            dependency_analysis = await self._analyze_integration_dependencies(discovered_integrations)
            analysis_results["dependency_analysis"] = dependency_analysis
            
            # Assess risks
            risk_assessment = await self._assess_integration_risks(discovered_integrations)
            analysis_results["risk_assessment"] = risk_assessment
            
            # Generate recommendations
            recommendations = await self._generate_integration_recommendations(
                discovered_integrations, complexity_assessment, risk_assessment
            )
            analysis_results["recommendations"] = recommendations
            
            # Create integration map
            integration_map = await self._create_integration_map(discovered_integrations)
            analysis_results["integration_map"] = integration_map
            
            # Store discovered integrations
            for integration in discovered_integrations:
                self.integrations[integration.id] = integration
            
            # Update integration graph
            await self._update_integration_graph(discovered_integrations)
            
            # Update metrics
            await self._calculate_complexity_metrics()
            
            return {
                "success": True,
                "integration_analysis": analysis_results,
                "summary": {
                    "total_integrations": len(discovered_integrations),
                    "complexity_score": complexity_assessment.get("overall_complexity", 0),
                    "risk_level": risk_assessment.get("overall_risk", "medium"),
                    "critical_integrations": len([i for i in discovered_integrations if i.complexity_level == ComplexityLevel.CRITICAL])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing integration complexity: {e}")
            return {"error": str(e)}
    
    async def _discover_integrations(self, project_path: str) -> List[IntegrationPoint]:
        """Discover integration points in the project"""
        self.logger.info("Discovering integration points...")
        
        integrations = []
        project_root = Path(project_path)
        
        # Look for integration indicators
        integration_indicators = {
            "api": {
                "files": ["*.py", "*.js", "*.ts", "*.java"],
                "patterns": [
                    r"@app\.route|@router\.",
                    r"flask|fastapi|express|spring",
                    r"rest|graphql|soap",
                    r"api|endpoint|service"
                ]
            },
            "database": {
                "files": ["*.py", "*.js", "*.sql", "*.xml"],
                "patterns": [
                    r"sqlalchemy|django\.db|mongoose|sequelize",
                    r"mysql|postgresql|mongodb|redis",
                    r"select|insert|update|delete",
                    r"connection|cursor|query"
                ]
            },
            "message_queue": {
                "files": ["*.py", "*.js", "*.java"],
                "patterns": [
                    r"rabbitmq|kafka|redis|aws_sqs",
                    r"publish|subscribe|queue|topic",
                    r"producer|consumer|broker"
                ]
            },
            "file_system": {
                "files": ["*.py", "*.js", "*.java"],
                "patterns": [
                    r"open\(|read\(|write\(",
                    r"os\.path|pathlib|fs\.",
                    r"json|yaml|xml|csv"
                ]
            },
            "webhook": {
                "files": ["*.py", "*.js", "*.ts"],
                "patterns": [
                    r"webhook|hook|callback",
                    r"post|receive|event",
                    r"notification|trigger"
                ]
            },
            "third_party": {
                "files": ["*.py", "*.js", "*.json", "*.yaml"],
                "patterns": [
                    r"requests|axios|http",
                    r"api_key|secret|token",
                    r"external|third_party|vendor"
                ]
            }
        }
        
        # Scan files for integration patterns
        for integration_type, config in integration_indicators.items():
            for root, dirs, files in os.walk(project_root):
                # Skip certain directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', 'env', 'build', 'dist']]
                
                for file in files:
                    if any(file.endswith(ext) for ext in config["files"]):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                                # Check for integration patterns
                                for pattern in config["patterns"]:
                                    matches = re.finditer(pattern, content, re.IGNORECASE)
                                    for match in matches:
                                        integration = await self._create_integration_from_match(
                                            file_path, integration_type, match, content
                                        )
                                        if integration:
                                            integrations.append(integration)
                                            
                        except Exception as e:
                            self.logger.warning(f"Error scanning {file_path}: {e}")
        
        # Remove duplicates based on similarity
        unique_integrations = await self._deduplicate_integrations(integrations)
        
        return unique_integrations
    
    async def _create_integration_from_match(self, file_path: str, integration_type: str, match, content: str) -> Optional[IntegrationPoint]:
        """Create integration point from pattern match"""
        try:
            # Extract context around the match
            line_number = content[:match.start()].count('\n') + 1
            lines = content.split('\n')
            context_lines = lines[max(0, line_number-5):line_number+5]
            
            # Determine integration details based on type and context
            integration_details = self._extract_integration_details(integration_type, context_lines, file_path)
            
            if not integration_details:
                return None
            
            # Calculate complexity
            complexity_level = self._calculate_integration_complexity(integration_type, integration_details)
            
            # Create integration point
            integration = IntegrationPoint(
                id=f"{integration_type}_{file_path}_{line_number}_{hash(match.group())}",
                name=integration_details["name"],
                type=IntegrationType(integration_type),
                source_system=integration_details["source_system"],
                target_system=integration_details["target_system"],
                description=integration_details["description"],
                protocol=integration_details["protocol"],
                data_format=integration_details["data_format"],
                complexity_level=complexity_level,
                status=IntegrationStatus.PLANNED,
                dependencies=[],
                risk_factors=integration_details["risk_factors"],
                metadata={
                    "file_path": file_path,
                    "line_number": line_number,
                    "pattern": match.group(),
                    "context": context_lines
                }
            )
            
            return integration
            
        except Exception as e:
            self.logger.warning(f"Error creating integration from match: {e}")
            return None
    
    def _extract_integration_details(self, integration_type: str, context_lines: List[str], file_path: str) -> Optional[Dict[str, Any]]:
        """Extract integration details from context"""
        context_text = '\n'.join(context_lines).lower()
        
        details = {
            "name": "",
            "source_system": Path(file_path).stem,
            "target_system": "",
            "description": "",
            "protocol": "",
            "data_format": "",
            "risk_factors": []
        }
        
        if integration_type == "api":
            details.update({
                "name": self._extract_api_name(context_text),
                "target_system": self._extract_api_target(context_text),
                "description": "API integration point",
                "protocol": self._extract_api_protocol(context_text),
                "data_format": self._extract_api_format(context_text),
                "risk_factors": self._extract_api_risks(context_text)
            })
        elif integration_type == "database":
            details.update({
                "name": self._extract_db_name(context_text),
                "target_system": self._extract_db_target(context_text),
                "description": "Database integration",
                "protocol": "sql",
                "data_format": "structured",
                "risk_factors": self._extract_db_risks(context_text)
            })
        elif integration_type == "message_queue":
            details.update({
                "name": self._extract_mq_name(context_text),
                "target_system": self._extract_mq_target(context_text),
                "description": "Message queue integration",
                "protocol": self._extract_mq_protocol(context_text),
                "data_format": "message",
                "risk_factors": self._extract_mq_risks(context_text)
            })
        else:
            details.update({
                "name": f"{integration_type}_integration",
                "target_system": "external",
                "description": f"{integration_type} integration",
                "protocol": "unknown",
                "data_format": "unknown",
                "risk_factors": ["unknown_protocol", "lack_of_documentation"]
            })
        
        # Validate that we have enough information
        if not details["name"] or not details["target_system"]:
            return None
        
        return details
    
    def _extract_api_name(self, context_text: str) -> str:
        """Extract API name from context"""
        patterns = [
            r"@app\.route\([\'\"]([^\'\"]+)[\'\"]",
            r"router\.(get|post|put|delete)\([\'\"]([^\'\"]+)[\'\"]",
            r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"api.*?([a-zA-Z_][a-zA-Z0-9_]*)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context_text)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        
        return "api_endpoint"
    
    def _extract_api_target(self, context_text: str) -> str:
        """Extract API target system from context"""
        if "external" in context_text:
            return "external_api"
        elif "database" in context_text:
            return "database_api"
        elif "auth" in context_text:
            return "auth_service"
        elif "payment" in context_text:
            return "payment_service"
        else:
            return "unknown_service"
    
    def _extract_api_protocol(self, context_text: str) -> str:
        """Extract API protocol from context"""
        if "rest" in context_text:
            return "rest"
        elif "graphql" in context_text:
            return "graphql"
        elif "soap" in context_text:
            return "soap"
        elif "grpc" in context_text:
            return "grpc"
        else:
            return "http"
    
    def _extract_api_format(self, context_text: str) -> str:
        """Extract API data format from context"""
        if "json" in context_text:
            return "json"
        elif "xml" in context_text:
            return "xml"
        elif "yaml" in context_text:
            return "yaml"
        else:
            return "json"
    
    def _extract_api_risks(self, context_text: str) -> List[str]:
        """Extract API risks from context"""
        risks = []
        if "key" in context_text or "secret" in context_text:
            risks.append("authentication_required")
        if "external" in context_text:
            risks.append("external_dependency")
        if "http" in context_text and "https" not in context_text:
            risks.append("unencrypted_communication")
        if "upload" in context_text or "download" in context_text:
            risks.append("file_handling")
        
        return risks if risks else ["standard_api_risks"]
    
    def _extract_db_name(self, context_text: str) -> str:
        """Extract database name from context"""
        patterns = [
            r"create\s+table\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"select.*from\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context_text)
            if match:
                return match.group(1)
        
        return "database_operation"
    
    def _extract_db_target(self, context_text: str) -> str:
        """Extract database target from context"""
        if "mysql" in context_text:
            return "mysql_database"
        elif "postgresql" in context_text:
            return "postgresql_database"
        elif "mongodb" in context_text:
            return "mongodb_database"
        elif "redis" in context_text:
            return "redis_cache"
        else:
            return "database"
    
    def _extract_db_risks(self, context_text: str) -> List[str]:
        """Extract database risks from context"""
        risks = []
        if "password" in context_text:
            risks.append("credential_exposure")
        if "select.*\*" in context_text:
            risks.append("inefficient_query")
        if "drop" in context_text or "delete" in context_text:
            risks.append("data_loss_risk")
        if "connection" in context_text:
            risks.append("connection_management")
        
        return risks if risks else ["standard_database_risks"]
    
    def _extract_mq_name(self, context_text: str) -> str:
        """Extract message queue name from context"""
        patterns = [
            r"queue\.?name\s*=\s*[\'\"]([^\'\"]+)[\'\"]",
            r"topic\s*=\s*[\'\"]([^\'\"]+)[\'\"]",
            r"channel\s*=\s*[\'\"]([^\'\"]+)[\'\"]",
            r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context_text)
            if match:
                return match.group(1)
        
        return "message_queue_operation"
    
    def _extract_mq_target(self, context_text: str) -> str:
        """Extract message queue target from context"""
        if "rabbitmq" in context_text:
            return "rabbitmq_server"
        elif "kafka" in context_text:
            return "kafka_cluster"
        elif "redis" in context_text:
            return "redis_queue"
        elif "aws" in context_text:
            return "aws_sqs"
        else:
            return "message_broker"
    
    def _extract_mq_protocol(self, context_text: str) -> str:
        """Extract message queue protocol from context"""
        if "amqp" in context_text:
            return "amqp"
        elif "mqtt" in context_text:
            return "mqtt"
        elif "stomp" in context_text:
            return "stomp"
        else:
            return "unknown_protocol"
    
    def _extract_mq_risks(self, context_text: str) -> List[str]:
        """Extract message queue risks from context"""
        risks = []
        if "publish" in context_text:
            risks.append("message_delivery")
        if "subscribe" in context_text:
            risks.append("message_processing")
        if "queue" in context_text:
            risks.append("queue_management")
        if "ack" in context_text:
            risks.append("message_acknowledgment")
        
        return risks if risks else ["standard_mq_risks"]
    
    def _calculate_integration_complexity(self, integration_type: str, details: Dict[str, Any]) -> ComplexityLevel:
        """Calculate integration complexity level"""
        # Base complexity scores by integration type
        base_scores = {
            "api": 3,
            "database": 2,
            "message_queue": 4,
            "file_system": 1,
            "webhook": 2,
            "third_party": 4,
            "microservice": 5,
            "legacy_system": 5
        }
        
        base_score = base_scores.get(integration_type, 3)
        
        # Adjust based on risk factors
        risk_factor_count = len(details.get("risk_factors", []))
        risk_adjustment = min(risk_factor_count * 0.5, 2)
        
        # Adjust based on protocol complexity
        protocol_complexity = {
            "rest": 1,
            "graphql": 2,
            "soap": 3,
            "grpc": 2,
            "sql": 1,
            "amqp": 2,
            "mqtt": 2,
            "unknown": 3
        }
        
        protocol_score = protocol_complexity.get(details.get("protocol", "unknown"), 2)
        
        # Calculate final score
        final_score = base_score + risk_adjustment + protocol_score
        
        # Map to complexity level
        if final_score >= 7:
            return ComplexityLevel.CRITICAL
        elif final_score >= 5:
            return ComplexityLevel.HIGH
        elif final_score >= 3:
            return ComplexityLevel.MEDIUM
        else:
            return ComplexityLevel.LOW
    
    async def _deduplicate_integrations(self, integrations: List[IntegrationPoint]) -> List[IntegrationPoint]:
        """Remove duplicate integrations based on similarity"""
        unique_integrations = []
        seen_signatures = set()
        
        for integration in integrations:
            # Create signature based on key attributes
            signature = f"{integration.type}_{integration.source_system}_{integration.target_system}_{integration.protocol}"
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_integrations.append(integration)
        
        return unique_integrations
    
    async def _assess_integration_complexity(self, integrations: List[IntegrationPoint]) -> Dict[str, Any]:
        """Assess overall integration complexity"""
        complexity_assessment = {
            "overall_complexity": 0,
            "complexity_distribution": {},
            "complexity_factors": {},
            "bottlenecks": [],
            "optimization_opportunities": []
        }
        
        if not integrations:
            return complexity_assessment
        
        # Calculate complexity distribution
        complexity_counts = {}
        for integration in integrations:
            level = integration.complexity_level.value
            complexity_counts[level] = complexity_counts.get(level, 0) + 1
        
        complexity_assessment["complexity_distribution"] = complexity_counts
        
        # Calculate overall complexity score
        total_integrations = len(integrations)
        weighted_score = 0
        
        for integration in integrations:
            level_weights = {
                ComplexityLevel.LOW: 1,
                ComplexityLevel.MEDIUM: 2,
                ComplexityLevel.HIGH: 3,
                ComplexityLevel.CRITICAL: 4
            }
            
            weighted_score += level_weights.get(integration.complexity_level, 2)
        
        complexity_assessment["overall_complexity"] = weighted_score / total_integrations
        
        # Analyze complexity factors
        complexity_assessment["complexity_factors"] = await self._analyze_complexity_factors(integrations)
        
        # Identify bottlenecks
        complexity_assessment["bottlenecks"] = await self._identify_complexity_bottlenecks(integrations)
        
        # Identify optimization opportunities
        complexity_assessment["optimization_opportunities"] = await self._identify_optimization_opportunities(integrations)
        
        return complexity_assessment
    
    async def _analyze_complexity_factors(self, integrations: List[IntegrationPoint]) -> Dict[str, Any]:
        """Analyze factors contributing to integration complexity"""
        factors = {
            "protocol_diversity": 0,
            "data_format_diversity": 0,
            "risk_factor_density": 0,
            "third_party_dependency": 0,
            "legacy_system_count": 0
        }
        
        # Calculate protocol diversity
        protocols = set(integration.protocol for integration in integrations)
        factors["protocol_diversity"] = len(protocols)
        
        # Calculate data format diversity
        formats = set(integration.data_format for integration in integrations)
        factors["data_format_diversity"] = len(formats)
        
        # Calculate risk factor density
        total_risk_factors = sum(len(integration.risk_factors) for integration in integrations)
        factors["risk_factor_density"] = total_risk_factors / len(integrations) if integrations else 0
        
        # Calculate third-party dependency count
        factors["third_party_dependency"] = len([
            i for i in integrations if i.type == IntegrationType.THIRD_PARTY
        ])
        
        # Calculate legacy system count
        factors["legacy_system_count"] = len([
            i for i in integrations if i.type == IntegrationType.LEGACY_SYSTEM
        ])
        
        return factors
    
    async def _identify_complexity_bottlenecks(self, integrations: List[IntegrationPoint]) -> List[Dict[str, Any]]:
        """Identify complexity bottlenecks"""
        bottlenecks = []
        
        # Find critical integrations
        critical_integrations = [
            i for i in integrations if i.complexity_level == ComplexityLevel.CRITICAL
        ]
        
        for integration in critical_integrations:
            bottleneck = {
                "integration_id": integration.id,
                "integration_name": integration.name,
                "complexity_level": integration.complexity_level.value,
                "risk_factors": integration.risk_factors,
                "impact": "High impact on system stability and maintainability",
                "recommendations": [
                    "Consider simplifying the integration",
                    "Implement proper error handling",
                    "Add comprehensive monitoring",
                    "Consider alternative approaches"
                ]
            }
            bottlenecks.append(bottleneck)
        
        # Find integrations with many risk factors
        high_risk_integrations = [
            i for i in integrations if len(i.risk_factors) > 3
        ]
        
        for integration in high_risk_integrations:
            bottleneck = {
                "integration_id": integration.id,
                "integration_name": integration.name,
                "complexity_level": integration.complexity_level.value,
                "risk_factors": integration.risk_factors,
                "impact": "Multiple risk factors increase failure probability",
                "recommendations": [
                    "Address individual risk factors",
                    "Implement risk mitigation strategies",
                    "Add additional testing and monitoring"
                ]
            }
            bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    async def _identify_optimization_opportunities(self, integrations: List[IntegrationPoint]) -> List[Dict[str, Any]]:
        """Identify optimization opportunities"""
        opportunities = []
        
        # Look for protocol standardization opportunities
        protocols = {}
        for integration in integrations:
            protocol = integration.protocol
            if protocol not in protocols:
                protocols[protocol] = []
            protocols[protocol].append(integration)
        
        for protocol, protocol_integrations in protocols.items():
            if len(protocol_integrations) > 1:
                opportunity = {
                    "type": "protocol_standardization",
                    "protocol": protocol,
                    "integrations": [i.id for i in protocol_integrations],
                    "potential_benefit": "Simplified maintenance and reduced complexity",
                    "implementation": "Standardize on common protocol patterns"
                }
                opportunities.append(opportunity)
        
        # Look for data format optimization
        formats = {}
        for integration in integrations:
            format_type = integration.data_format
            if format_type not in formats:
                formats[format_type] = []
            formats[format_type].append(integration)
        
        for format_type, format_integrations in formats.items():
            if len(format_integrations) > 2:
                opportunity = {
                    "type": "data_format_optimization",
                    "format": format_type,
                    "integrations": [i.id for i in format_integrations],
                    "potential_benefit": "Reduced data transformation overhead",
                    "implementation": "Implement common data transformation layer"
                }
                opportunities.append(opportunity)
        
        return opportunities
    
    async def _analyze_integration_dependencies(self, integrations: List[IntegrationPoint]) -> Dict[str, Any]:
        """Analyze dependencies between integrations"""
        dependency_analysis = {
            "dependency_graph": {},
            "critical_paths": [],
            "dependency_cycles": [],
            "impact_analysis": {},
            "recommendations": []
        }
        
        # Build dependency graph
        dependency_graph = nx.DiGraph()
        
        # Add nodes
        for integration in integrations:
            dependency_graph.add_node(integration.id, integration=integration)
        
        # Add edges (dependencies)
        for integration in integrations:
            # Analyze dependencies based on metadata and context
            dependencies = await self._extract_integration_dependencies(integration, integrations)
            for dep_id, dep_strength in dependencies.items():
                dependency_graph.add_edge(integration.id, dep_id, weight=dep_strength)
        
        dependency_analysis["dependency_graph"] = dependency_graph
        
        # Find critical paths
        if dependency_graph.number_of_nodes() > 0:
            try:
                # Find longest paths (critical paths)
                critical_paths = []
                for source in dependency_graph.nodes():
                    for target in dependency_graph.nodes():
                        if source != target and nx.has_path(dependency_graph, source, target):
                            path = nx.shortest_path(dependency_graph, source, target)
                            if len(path) > 2:  # Paths with more than 2 nodes
                                critical_paths.append(path)
                
                dependency_analysis["critical_paths"] = critical_paths
            except Exception as e:
                self.logger.warning(f"Error finding critical paths: {e}")
        
        # Find dependency cycles
        try:
            cycles = list(nx.simple_cycles(dependency_graph))
            dependency_analysis["dependency_cycles"] = cycles
        except Exception as e:
            self.logger.warning(f"Error finding cycles: {e}")
        
        # Analyze impact
        dependency_analysis["impact_analysis"] = await self._analyze_dependency_impact(dependency_graph)
        
        # Generate recommendations
        dependency_analysis["recommendations"] = await self._generate_dependency_recommendations(
            dependency_graph, dependency_analysis["critical_paths"], dependency_analysis["dependency_cycles"]
        )
        
        return dependency_analysis
    
    async def _extract_integration_dependencies(self, integration: IntegrationPoint, all_integrations: List[IntegrationPoint]) -> Dict[str, float]:
        """Extract dependencies for an integration"""
        dependencies = {}
        
        # Analyze integration metadata and context
        context_text = '\n'.join(integration.metadata.get("context", [])).lower()
        
        # Look for references to other systems
        for other_integration in all_integrations:
            if other_integration.id == integration.id:
                continue
            
            # Check if other integration is referenced
            other_system = other_integration.target_system.lower()
            if other_system in context_text:
                # Calculate dependency strength based on context
                strength = self._calculate_dependency_strength(context_text, other_system)
                if strength > 0.3:
                    dependencies[other_integration.id] = strength
        
        return dependencies
    
    def _calculate_dependency_strength(self, context_text: str, target_system: str) -> float:
        """Calculate dependency strength between integrations"""
        # Count occurrences of target system in context
        occurrences = context_text.count(target_system)
        
        # Base strength on occurrences and context
        if occurrences == 0:
            return 0.0
        elif occurrences == 1:
            return 0.4
        elif occurrences == 2:
            return 0.6
        else:
            return 0.8
    
    async def _analyze_dependency_impact(self, dependency_graph: nx.DiGraph) -> Dict[str, Any]:
        """Analyze impact of dependencies"""
        impact_analysis = {
            "high_impact_nodes": [],
            "single_points_of_failure": [],
            "cascading_failure_risk": 0,
            "dependency_depth": 0
        }
        
        if dependency_graph.number_of_nodes() == 0:
            return impact_analysis
        
        # Calculate node importance (centrality)
        try:
            centrality = nx.degree_centrality(dependency_graph)
            
            # Find high-impact nodes (high centrality)
            high_impact_threshold = 0.5
            impact_analysis["high_impact_nodes"] = [
                node for node, centrality_score in centrality.items() 
                if centrality_score > high_impact_threshold
            ]
        except Exception as e:
            self.logger.warning(f"Error calculating centrality: {e}")
        
        # Find single points of failure
        try:
            articulation_points = list(nx.articulation_points(dependency_graph.to_undirected()))
            impact_analysis["single_points_of_failure"] = articulation_points
        except Exception as e:
            self.logger.warning(f"Error finding articulation points: {e}")
        
        # Calculate cascading failure risk
        if dependency_graph.number_of_edges() > 0:
            avg_degree = sum(dict(dependency_graph.degree()).values()) / dependency_graph.number_of_nodes()
            impact_analysis["cascading_failure_risk"] = min(avg_degree / 5, 1.0)
        
        # Calculate maximum dependency depth
        try:
            longest_path = 0
            for source in dependency_graph.nodes():
                for target in dependency_graph.nodes():
                    if source != target and nx.has_path(dependency_graph, source, target):
                        path_length = nx.shortest_path_length(dependency_graph, source, target)
                        longest_path = max(longest_path, path_length)
            
            impact_analysis["dependency_depth"] = longest_path
        except Exception as e:
            self.logger.warning(f"Error calculating dependency depth: {e}")
        
        return impact_analysis
    
    async def _generate_dependency_recommendations(self, dependency_graph: nx.DiGraph, critical_paths: List[List[str]], cycles: List[List[str]]) -> List[str]:
        """Generate dependency recommendations"""
        recommendations = []
        
        # Recommendations for critical paths
        if critical_paths:
            recommendations.append("Consider breaking down critical paths to reduce cascading failure risk")
            recommendations.append("Implement proper error handling and fallback mechanisms for critical path integrations")
        
        # Recommendations for cycles
        if cycles:
            recommendations.append("Resolve dependency cycles to prevent deadlocks and circular dependencies")
            recommendations.append("Consider introducing abstraction layers or event-driven architecture to break cycles")
        
        # Recommendations for high-impact nodes
        high_impact_nodes = []
        try:
            centrality = nx.degree_centrality(dependency_graph)
            high_impact_threshold = 0.5
            high_impact_nodes = [
                node for node, centrality_score in centrality.items() 
                if centrality_score > high_impact_threshold
            ]
        except:
            pass
        
        if high_impact_nodes:
            recommendations.append("Implement redundancy and failover mechanisms for high-impact integration points")
            recommendations.append("Add comprehensive monitoring and alerting for critical integrations")
        
        # General recommendations
        if dependency_graph.number_of_edges() > 10:
            recommendations.append("Consider simplifying integration architecture to reduce complexity")
            recommendations.append("Implement integration patterns like API Gateway or Service Mesh")
        
        return recommendations
    
    async def _assess_integration_risks(self, integrations: List[IntegrationPoint]) -> Dict[str, Any]:
        """Assess risks associated with integrations"""
        risk_assessment = {
            "overall_risk": "medium",
            "risk_distribution": {},
            "high_risk_integrations": [],
            "risk_categories": {},
            "mitigation_strategies": {},
            "risk_trends": {}
        }
        
        if not integrations:
            return risk_assessment
        
        # Analyze risk distribution
        risk_counts = {}
        for integration in integrations:
            for risk_factor in integration.risk_factors:
                risk_counts[risk_factor] = risk_counts.get(risk_factor, 0) + 1
        
        risk_assessment["risk_distribution"] = risk_counts
        
        # Identify high-risk integrations
        high_risk_integrations = [
            integration for integration in integrations
            if (integration.complexity_level in [ComplexityLevel.HIGH, ComplexityLevel.CRITICAL] or
                len(integration.risk_factors) > 3)
        ]
        
        risk_assessment["high_risk_integrations"] = [
            {
                "integration_id": integration.id,
                "integration_name": integration.name,
                "complexity_level": integration.complexity_level.value,
                "risk_factors": integration.risk_factors,
                "risk_score": self._calculate_integration_risk_score(integration)
            }
            for integration in high_risk_integrations
        ]
        
        # Categorize risks
        risk_assessment["risk_categories"] = await self._categorize_risks(integrations)
        
        # Generate mitigation strategies
        risk_assessment["mitigation_strategies"] = await self._generate_risk_mitigation_strategies(integrations)
        
        # Calculate overall risk level
        overall_risk_score = self._calculate_overall_risk_score(integrations)
        risk_assessment["overall_risk"] = self._map_score_to_risk_level(overall_risk_score)
        
        return risk_assessment
    
    def _calculate_integration_risk_score(self, integration: IntegrationPoint) -> float:
        """Calculate risk score for a single integration"""
        # Base score from complexity level
        complexity_scores = {
            ComplexityLevel.LOW: 1,
            ComplexityLevel.MEDIUM: 2,
            ComplexityLevel.HIGH: 3,
            ComplexityLevel.CRITICAL: 4
        }
        
        base_score = complexity_scores.get(integration.complexity_level, 2)
        
        # Add risk factor score
        risk_factor_score = len(integration.risk_factors) * 0.5
        
        # Add type-based risk
        type_risk_scores = {
            IntegrationType.LEGACY_SYSTEM: 2,
            IntegrationType.THIRD_PARTY: 1.5,
            IntegrationType.MICROSERVICE: 1,
            IntegrationType.API: 0.5,
            IntegrationType.DATABASE: 0.5
        }
        
        type_score = type_risk_scores.get(integration.type, 1)
        
        # Calculate final score
        final_score = base_score + risk_factor_score + type_score
        
        return min(final_score, 10)  # Cap at 10
    
    def _calculate_overall_risk_score(self, integrations: List[IntegrationPoint]) -> float:
        """Calculate overall risk score for all integrations"""
        if not integrations:
            return 0
        
        total_score = sum(self._calculate_integration_risk_score(integration) for integration in integrations)
        return total_score / len(integrations)
    
    def _map_score_to_risk_level(self, score: float) -> str:
        """Map risk score to risk level"""
        if score >= 7:
            return "critical"
        elif score >= 5:
            return "high"
        elif score >= 3:
            return "medium"
        else:
            return "low"
    
    async def _categorize_risks(self, integrations: List[IntegrationPoint]) -> Dict[str, Any]:
        """Categorize risks by type"""
        risk_categories = {
            "technical_risks": [],
            "operational_risks": [],
            "security_risks": [],
            "business_risks": []
        }
        
        for integration in integrations:
            for risk_factor in integration.risk_factors:
                if risk_factor in ["authentication_required", "unencrypted_communication", "credential_exposure"]:
                    risk_categories["security_risks"].append({
                        "integration_id": integration.id,
                        "risk_factor": risk_factor
                    })
                elif risk_factor in ["external_dependency", "connection_management", "message_delivery"]:
                    risk_categories["technical_risks"].append({
                        "integration_id": integration.id,
                        "risk_factor": risk_factor
                    })
                elif risk_factor in ["data_loss_risk", "file_handling", "queue_management"]:
                    risk_categories["operational_risks"].append({
                        "integration_id": integration.id,
                        "risk_factor": risk_factor
                    })
                else:
                    risk_categories["business_risks"].append({
                        "integration_id": integration.id,
                        "risk_factor": risk_factor
                    })
        
        return risk_categories
    
    async def _generate_risk_mitigation_strategies(self, integrations: List[IntegrationPoint]) -> Dict[str, List[str]]:
        """Generate risk mitigation strategies"""
        mitigation_strategies = {
            "technical_risks": [
                "Implement proper error handling and retry mechanisms",
                "Use circuit breakers for external dependencies",
                "Implement connection pooling and management",
                "Add comprehensive logging and monitoring"
            ],
            "operational_risks": [
                "Implement data validation and sanitization",
                "Use transaction management for critical operations",
                "Implement proper backup and recovery procedures",
                "Add operational monitoring and alerting"
            ],
            "security_risks": [
                "Implement proper authentication and authorization",
                "Use encryption for sensitive data transmission",
                "Implement proper credential management",
                "Add security monitoring and intrusion detection"
            ],
            "business_risks": [
                "Implement service level agreements (SLAs)",
                "Add business continuity planning",
                "Implement proper vendor management",
                "Add business impact analysis"
            ]
        }
        
        return mitigation_strategies
    
    async def _generate_integration_recommendations(self, integrations: List[IntegrationPoint], complexity_assessment: Dict[str, Any], risk_assessment: Dict[str, Any]) -> List[str]:
        """Generate comprehensive integration recommendations"""
        recommendations = []
        
        # Complexity-based recommendations
        overall_complexity = complexity_assessment.get("overall_complexity", 0)
        if overall_complexity > 3:
            recommendations.append("Consider simplifying integration architecture to reduce complexity")
            recommendations.append("Implement integration patterns like API Gateway or Service Mesh")
        
        # Risk-based recommendations
        overall_risk = risk_assessment.get("overall_risk", "medium")
        if overall_risk in ["high", "critical"]:
            recommendations.append("Implement comprehensive risk mitigation strategies")
            recommendations.append("Add enhanced monitoring and alerting for high-risk integrations")
        
        # Integration type-specific recommendations
        integration_types = set(integration.type for integration in integrations)
        
        if IntegrationType.LEGACY_SYSTEM in integration_types:
            recommendations.append("Consider modernizing legacy system integrations")
            recommendations.append("Implement anti-corruption layer for legacy integrations")
        
        if IntegrationType.THIRD_PARTY in integration_types:
            recommendations.append("Implement proper vendor management and SLAs")
            recommendations.append("Add fallback mechanisms for third-party service failures")
        
        if IntegrationType.MICROSERVICE in integration_types:
            recommendations.append("Implement proper service discovery and load balancing")
            recommendations.append("Add distributed tracing for microservice communications")
        
        # General best practices
        recommendations.extend([
            "Implement comprehensive integration testing",
            "Add proper documentation for all integrations",
            "Implement integration monitoring and health checks",
            "Consider using integration platforms or middleware"
        ])
        
        return list(set(recommendations))  # Remove duplicates
    
    async def _create_integration_map(self, integrations: List[IntegrationPoint]) -> Dict[str, Any]:
        """Create visual integration map"""
        integration_map = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "total_integrations": len(integrations),
                "complexity_levels": {},
                "integration_types": {}
            }
        }
        
        # Create nodes
        for integration in integrations:
            node = {
                "id": integration.id,
                "name": integration.name,
                "type": integration.type.value,
                "complexity": integration.complexity_level.value,
                "status": integration.status.value,
                "source_system": integration.source_system,
                "target_system": integration.target_system,
                "risk_factors": integration.risk_factors
            }
            integration_map["nodes"].append(node)
        
        # Create edges (simplified - would need actual dependency analysis)
        for i, integration in enumerate(integrations):
            if i < len(integrations) - 1:
                edge = {
                    "source": integration.id,
                    "target": integrations[i + 1].id,
                    "type": "dependency",
                    "strength": 0.5
                }
                integration_map["edges"].append(edge)
        
        # Update metadata
        complexity_levels = {}
        for integration in integrations:
            level = integration.complexity_level.value
            complexity_levels[level] = complexity_levels.get(level, 0) + 1
        integration_map["metadata"]["complexity_levels"] = complexity_levels
        
        integration_types = {}
        for integration in integrations:
            int_type = integration.type.value
            integration_types[int_type] = integration_types.get(int_type, 0) + 1
        integration_map["metadata"]["integration_types"] = integration_types
        
        return integration_map
    
    async def _update_integration_graph(self, integrations: List[IntegrationPoint]) -> None:
        """Update the integration graph with new integrations"""
        # Add nodes
        for integration in integrations:
            self.integration_graph.add_node(integration.id, integration=integration)
        
        # Add edges (simplified - would need actual dependency analysis)
        for i, integration in enumerate(integrations):
            if i < len(integrations) - 1:
                self.integration_graph.add_edge(
                    integration.id, 
                    integrations[i + 1].id,
                    weight=0.5
                )
    
    async def _calculate_complexity_metrics(self) -> None:
        """Calculate complexity metrics"""
        self.complexity_metrics["total_integrations"] = len(self.integrations)
        self.complexity_metrics["critical_integrations"] = len([
            i for i in self.integrations.values() 
            if i.complexity_level == ComplexityLevel.CRITICAL
        ])
        
        # Calculate average complexity
        if self.integrations:
            complexity_scores = {
                ComplexityLevel.LOW: 1,
                ComplexityLevel.MEDIUM: 2,
                ComplexityLevel.HIGH: 3,
                ComplexityLevel.CRITICAL: 4
            }
            
            total_score = sum(
                complexity_scores.get(integration.complexity_level, 2)
                for integration in self.integrations.values()
            )
            
            self.complexity_metrics["average_complexity"] = total_score / len(self.integrations)
        else:
            self.complexity_metrics["average_complexity"] = 0
        
        # Calculate dependency depth
        if self.integration_graph.number_of_nodes() > 0:
            try:
                longest_path = 0
                for source in self.integration_graph.nodes():
                    for target in self.integration_graph.nodes():
                        if source != target and nx.has_path(self.integration_graph, source, target):
                            path_length = nx.shortest_path_length(self.integration_graph, source, target)
                            longest_path = max(longest_path, path_length)
                
                self.complexity_metrics["dependency_depth"] = longest_path
            except:
                self.complexity_metrics["dependency_depth"] = 0
        else:
            self.complexity_metrics["dependency_depth"] = 0
        
        # Calculate risk score
        if self.integrations:
            total_risk = sum(
                self._calculate_integration_risk_score(integration)
                for integration in self.integrations.values()
            )
            self.complexity_metrics["risk_score"] = total_risk / len(self.integrations)
        else:
            self.complexity_metrics["risk_score"] = 0
        
        # Calculate test coverage (placeholder)
        self.complexity_metrics["test_coverage"] = 0  # Would be calculated from actual tests
    
    def _load_integration_patterns(self) -> Dict[str, Any]:
        """Load integration patterns"""
        return {
            "api_patterns": {
                "rest_api": {"complexity": 2, "best_practices": ["use_http_status_codes", "implement_rate_limiting"]},
                "graphql": {"complexity": 3, "best_practices": ["use_pagination", "implement_depth_limiting"]},
                "soap": {"complexity": 4, "best_practices": ["use_ws_security", "implement_validation"]}
            },
            "database_patterns": {
                "sql_database": {"complexity": 2, "best_practices": ["use_parameterized_queries", "implement_indexes"]},
                "nosql_database": {"complexity": 3, "best_practices": ["use_proper_indexing", "implement_sharding"]}
            },
            "messaging_patterns": {
                "publish_subscribe": {"complexity": 3, "best_practices": ["use_durable_subscriptions", "implement_dead_letter_queues"]},
                "request_reply": {"complexity": 2, "best_practices": ["use_timeouts", "implement_retry_logic"]}
            }
        }
    
    def _load_risk_matrix(self) -> Dict[str, Any]:
        """Load risk assessment matrix"""
        return {
            "probability_levels": {
                "rare": 0.1,
                "unlikely": 0.3,
                "possible": 0.5,
                "likely": 0.7,
                "almost_certain": 0.9
            },
            "impact_levels": {
                "negligible": 1,
                "minor": 2,
                "moderate": 3,
                "major": 4,
                "severe": 5
            }
        }
    
    def _load_best_practices(self) -> Dict[str, List[str]]:
        """Load integration best practices"""
        return {
            "general": [
                "Implement proper error handling",
                "Use comprehensive logging",
                "Add monitoring and alerting",
                "Document all integrations",
                "Implement proper security measures"
            ],
            "api": [
                "Use standard HTTP methods",
                "Implement proper authentication",
                "Use API versioning",
                "Implement rate limiting",
                "Provide proper API documentation"
            ],
            "database": [
                "Use connection pooling",
                "Implement proper indexing",
                "Use parameterized queries",
                "Implement proper transaction management",
                "Add database monitoring"
            ],
            "messaging": [
                "Use message persistence",
                "Implement proper error handling",
                "Use dead letter queues",
                "Implement message acknowledgment",
                "Add message monitoring"
            ]
        }
    
    def _load_integration_templates(self) -> Dict[str, Any]:
        """Load integration templates"""
        return {
            "api_integration": {
                "description": "Standard API integration template",
                "components": ["http_client", "authentication", "error_handler", "monitoring"],
                "best_practices": ["use_circuit_breaker", "implement_retry_logic", "add_timeout"]
            },
            "database_integration": {
                "description": "Database integration template",
                "components": ["connection_pool", "query_builder", "transaction_manager", "monitoring"],
                "best_practices": ["use_prepared_statements", "implement_connection_pooling", "add_query_logging"]
            },
            "message_queue_integration": {
                "description": "Message queue integration template",
                "components": ["producer", "consumer", "error_handler", "monitoring"],
                "best_practices": ["use_persistent_queues", "implement_acknowledgment", "add_dead_letter_handling"]
            }
        }
    
    async def _load_existing_integrations(self) -> None:
        """Load existing integrations from storage"""
        # In a real implementation, this would load from a database or file
        pass
    
    async def _initialize_integration_graph(self) -> None:
        """Initialize the integration graph"""
        # In a real implementation, this would build the graph from existing data
        pass
    
    async def add_integration(self, integration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new integration"""
        try:
            integration = IntegrationPoint(
                id=integration_data.get("id", f"integration_{datetime.now().timestamp()}"),
                name=integration_data["name"],
                type=IntegrationType(integration_data["type"]),
                source_system=integration_data["source_system"],
                target_system=integration_data["target_system"],
                description=integration_data.get("description", ""),
                protocol=integration_data.get("protocol", "unknown"),
                data_format=integration_data.get("data_format", "unknown"),
                complexity_level=ComplexityLevel(integration_data.get("complexity_level", "medium")),
                status=IntegrationStatus(integration_data.get("status", "planned")),
                dependencies=integration_data.get("dependencies", []),
                risk_factors=integration_data.get("risk_factors", []),
                metadata=integration_data.get("metadata", {})
            )
            
            self.integrations[integration.id] = integration
            
            # Update integration graph
            self.integration_graph.add_node(integration.id, integration=integration)
            
            # Update metrics
            await self._calculate_complexity_metrics()
            
            return {
                "success": True,
                "integration_id": integration.id,
                "message": "Integration added successfully"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_integration_dashboard(self) -> Dict[str, Any]:
        """Get integration management dashboard"""
        return {
            "success": True,
            "dashboard": {
                "total_integrations": self.complexity_metrics["total_integrations"],
                "critical_integrations": self.complexity_metrics["critical_integrations"],
                "average_complexity": self.complexity_metrics["average_complexity"],
                "risk_score": self.complexity_metrics["risk_score"],
                "dependency_depth": self.complexity_metrics["dependency_depth"],
                "test_coverage": self.complexity_metrics["test_coverage"],
                "integrations_by_type": {
                    integration_type.value: len([i for i in self.integrations.values() if i.type == integration_type])
                    for integration_type in IntegrationType
                },
                "integrations_by_status": {
                    status.value: len([i for i in self.integrations.values() if i.status == status])
                    for status in IntegrationStatus
                },
                "recent_activity": [
                    {
                        "integration_id": integration.id,
                        "integration_name": integration.name,
                        "activity": "updated",
                        "timestamp": integration.updated_at
                    }
                    for integration in list(self.integrations.values())[-5:]
                ]
            }
        }
    async def stop(self) -> None:
        """Stop the integration complexity manager"""
        self.logger.info("Stopping Integration Complexity Manager...")
        
        # Save current state
        await self._save_integration_state()
        
        # Clear resources
        self.integrations.clear()
        self.dependencies.clear()
        self.risks.clear()
        self.tests.clear()
        self.integration_graph.clear()
        
        # Save historical data
        await self._save_historical_data()
        
        self.logger.info("Integration Complexity Manager stopped")
    
    async def _save_integration_state(self) -> None:
        """Save current integration state to persistent storage"""
        try:
            state = {
                "integrations": {
                    integration_id: {
                        "id": integration.id,
                        "name": integration.name,
                        "type": integration.type.value,
                        "source_system": integration.source_system,
                        "target_system": integration.target_system,
                        "description": integration.description,
                        "protocol": integration.protocol,
                        "data_format": integration.data_format,
                        "complexity_level": integration.complexity_level.value,
                        "status": integration.status.value,
                        "dependencies": integration.dependencies,
                        "risk_factors": integration.risk_factors,
                        "created_at": integration.created_at.isoformat(),
                        "updated_at": integration.updated_at.isoformat(),
                        "metadata": integration.metadata
                    }
                    for integration_id, integration in self.integrations.items()
                },
                "dependencies": [
                    {
                        "source_integration": dep.source_integration,
                        "target_integration": dep.target_integration,
                        "dependency_type": dep.dependency_type,
                        "strength": dep.strength,
                        "description": dep.description,
                        "critical_path": dep.critical_path
                    }
                    for dep in self.dependencies
                ],
                "risks": [
                    {
                        "id": risk.id,
                        "integration_id": risk.integration_id,
                        "risk_type": risk.risk_type,
                        "severity": risk.severity,
                        "probability": risk.probability,
                        "impact": risk.impact,
                        "mitigation_strategy": risk.mitigation_strategy,
                        "detected_at": risk.detected_at.isoformat()
                    }
                    for risk in self.risks
                ],
                "metrics": self.complexity_metrics,
                "saved_at": datetime.now().isoformat()
            }
            
            # Save to file
            save_path = Path(self.settings.workspace_dir) / "integration_state.json"
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Integration state saved to {save_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving integration state: {e}")
    
    async def _save_historical_data(self) -> None:
        """Save historical performance data"""
        try:
            historical_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": self.complexity_metrics,
                "integration_count": len(self.integrations),
                "risk_count": len(self.risks),
                "test_count": len(self.tests)
            }
            
            # Append to historical data
            if "integration_complexity" not in self.historical_performance:
                self.historical_performance["integration_complexity"] = []
            
            self.historical_performance["integration_complexity"].append(historical_data)
            
            # Keep only last 1000 entries
            if len(self.historical_performance["integration_complexity"]) > 1000:
                self.historical_performance["integration_complexity"] = self.historical_performance["integration_complexity"][-1000:]
            
            # Save to file
            save_path = Path(self.settings.workspace_dir) / "integration_history.json"
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(self.historical_performance, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Historical data saved to {save_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving historical data: {e}")
    
    async def get_integration_health_report(self) -> Dict[str, Any]:
        """Get comprehensive integration health report"""
        try:
            # Calculate health metrics
            health_metrics = await self._calculate_health_metrics()
            
            # Generate health recommendations
            health_recommendations = await self._generate_health_recommendations(health_metrics)
            
            return {
                "success": True,
                "health_report": {
                    "overall_health": health_metrics["overall_health"],
                    "health_score": health_metrics["health_score"],
                    "critical_issues": health_metrics["critical_issues"],
                    "warnings": health_metrics["warnings"],
                    "healthy_integrations": health_metrics["healthy_integrations"],
                    "at_risk_integrations": health_metrics["at_risk_integrations"],
                    "failed_integrations": health_metrics["failed_integrations"],
                    "health_trends": health_metrics["health_trends"],
                    "recommendations": health_recommendations,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating health report: {e}")
            return {"error": str(e)}
    
    async def _calculate_health_metrics(self) -> Dict[str, Any]:
        """Calculate integration health metrics"""
        try:
            # Count integrations by status
            status_counts = {}
            for status in IntegrationStatus:
                status_counts[status.value] = len([i for i in self.integrations.values() if i.status == status])
            
            # Calculate health score
            total_integrations = len(self.integrations)
            if total_integrations == 0:
                health_score = 100
            else:
                healthy_count = status_counts.get("deployed", 0) + status_counts.get("testing", 0)
                at_risk_count = status_counts.get("in_development", 0) + status_counts.get("planned", 0)
                failed_count = status_counts.get("failed", 0) + status_counts.get("deprecated", 0)
                
                health_score = (healthy_count / total_integrations) * 100 - (failed_count / total_integrations) * 50
            
            # Determine overall health
            if health_score >= 90:
                overall_health = "excellent"
            elif health_score >= 75:
                overall_health = "good"
            elif health_score >= 60:
                overall_health = "fair"
            else:
                overall_health = "poor"
            
            # Identify critical issues
            critical_issues = []
            for integration in self.integrations.values():
                if integration.status == IntegrationStatus.FAILED:
                    critical_issues.append({
                        "integration_id": integration.id,
                        "integration_name": integration.name,
                        "issue": "Integration failed",
                        "severity": "critical"
                    })
                elif integration.complexity_level == ComplexityLevel.CRITICAL and integration.status != IntegrationStatus.DEPLOYED:
                    critical_issues.append({
                        "integration_id": integration.id,
                        "integration_name": integration.name,
                        "issue": "Critical complexity integration not deployed",
                        "severity": "high"
                    })
            
            # Calculate trends
            trends = {}
            if "integration_complexity" in self.historical_performance and len(self.historical_performance["integration_complexity"]) > 1:
                recent_data = self.historical_performance["integration_complexity"][-10:]  # Last 10 entries
                if len(recent_data) >= 2:
                    old_score = recent_data[0]["metrics"].get("health_score", 75) if "metrics" in recent_data[0] else 75
                    new_score = recent_data[-1]["metrics"].get("health_score", health_score) if "metrics" in recent_data[-1] else health_score
                    
                    if new_score > old_score:
                        trends["health_score"] = "improving"
                    elif new_score < old_score:
                        trends["health_score"] = "declining"
                    else:
                        trends["health_score"] = "stable"
            
            return {
                "overall_health": overall_health,
                "health_score": round(health_score, 2),
                "critical_issues": critical_issues,
                "warnings": [r for r in self.risks if r.severity in ["high", "critical"]],
                "healthy_integrations": status_counts.get("deployed", 0),
                "at_risk_integrations": status_counts.get("in_development", 0) + status_counts.get("planned", 0),
                "failed_integrations": status_counts.get("failed", 0),
                "health_trends": trends
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating health metrics: {e}")
            return {"overall_health": "unknown", "health_score": 0}
    
    async def _generate_health_recommendations(self, health_metrics: Dict[str, Any]) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []
        
        try:
            # Overall health recommendations
            if health_metrics["overall_health"] == "poor":
                recommendations.append("Critical: Overall integration health is poor. Immediate attention required.")
            elif health_metrics["overall_health"] == "fair":
                recommendations.append("Warning: Integration health is fair. Consider improvements.")
            
            # Critical issues recommendations
            if health_metrics["critical_issues"]:
                recommendations.append(f"Address {len(health_metrics[\"critical_issues\"])} critical integration issues immediately.")
            
            # Failed integrations
            if health_metrics["failed_integrations"] > 0:
                recommendations.append(f"Fix {health_metrics[\"failed_integrations\"]} failed integrations.")
            
            # At-risk integrations
            if health_metrics["at_risk_integrations"] > 0:
                recommendations.append(f"Monitor and complete {health_metrics[\"at_risk_integrations\"]} at-risk integrations.")
            
            # Health trends
            if health_metrics["health_trends"].get("health_score") == "declining":
                recommendations.append("Health score is declining. Investigate root causes.")
            
            # Test coverage
            if self.complexity_metrics["test_coverage"] < 70:
                recommendations.append("Increase test coverage for better integration reliability.")
            
            # Risk management
            if health_metrics["warnings"]:
                recommendations.append(f"Address {len(health_metrics[\"warnings\"])} high-priority risks.")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating health recommendations: {e}")
            return ["Error generating recommendations"]

