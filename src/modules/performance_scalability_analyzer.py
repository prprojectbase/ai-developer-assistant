import asyncio
import logging
import json
import os
import re
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import ast
import networkx as nx
from collections import defaultdict, deque
import statistics
import time

from ..config.settings import get_settings


@dataclass
class PerformanceMetric:
    """Performance metric representation"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    threshold: Optional[float] = None
    category: str = "general"


@dataclass
class Bottleneck:
    """Performance bottleneck representation"""
    id: str
    type: str
    severity: str
    description: str
    file_path: str
    line_number: int
    impact_score: float
    estimated_fix_time: str
    recommendations: List[str]
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class ScalabilityIssue:
    """Scalability issue representation"""
    id: str
    component: str
    issue_type: str
    current_capacity: float
    projected_limit: float
    growth_rate: float
    time_to_limit: timedelta
    severity: str
    recommendations: List[str]


@dataclass
class ResourceUsage:
    """Resource usage statistics"""
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    network_io: Dict[str, float]
    process_count: int
    thread_count: int
    timestamp: datetime


class PerformanceScalabilityAnalyzer:
    """Comprehensive Performance and Scalability Analyzer"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Performance data storage
        self.performance_metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self.bottlenecks: List[Bottleneck] = []
        self.scalability_issues: List[ScalabilityIssue] = []
        self.resource_usage_history: List[ResourceUsage] = []
        
        # Analysis configuration
        self.analysis_config = {
            "performance_thresholds": {
                "response_time": 1000,  # ms
                "cpu_usage": 80,  # %
                "memory_usage": 85,  # %
                "database_query_time": 500,  # ms
                "api_call_time": 2000,  # ms
                "throughput": 1000  # requests/second
            },
            "scalability_factors": {
                "user_growth_rate": 0.1,  # 10% monthly
                "data_growth_rate": 0.2,  # 20% monthly
                "resource_efficiency": 0.7  # 70% efficiency target
            }
        }
        
        # Performance patterns
        self.performance_patterns = {
            "n_plus_one_queries": {
                "indicators": [r"for.*in.*:", r"\.get\(", r"\.filter\("],
                "severity": "high",
                "impact": "database"
            },
            "inefficient_loops": {
                "indicators": [r"for.*range\(len\(", r"while.*:", r"\.append\(.*\)"],
                "severity": "medium",
                "impact": "cpu"
            },
            "memory_leaks": {
                "indicators": [r"global\s+\w+", r"__del__", r"weakref"],
                "severity": "high",
                "impact": "memory"
            },
            "blocking_operations": {
                "indicators": [r"time\.sleep\(", r"socket\.", r"subprocess\.call"],
                "severity": "medium",
                "impact": "responsiveness"
            }
        }
        
        # Scalability models
        self.scalability_models = {
            "vertical_scaling": {
                "max_cpu": 32,
                "max_memory": 128,  # GB
                "cost_factor": 1.5
            },
            "horizontal_scaling": {
                "max_nodes": 100,
                "load_balancer_efficiency": 0.95,
                "cost_factor": 1.2
            },
            "database_scaling": {
                "max_connections": 1000,
                "read_replicas": 5,
                "sharding_factor": 10
            }
        }
        
        # Performance baselines
        self.performance_baselines = {
            "response_time": {"p50": 100, "p90": 500, "p95": 1000, "p99": 2000},
            "throughput": {"baseline": 100, "peak": 1000},
            "error_rate": {"acceptable": 0.01, "critical": 0.05}
        }
        
        # Analysis cache
        self.analysis_cache: Dict[str, Any] = {}
        self.cache_ttl = 1800  # 30 minutes
        
        # Monitoring configuration
        self.monitoring_config = {
            "sampling_interval": 60,  # seconds
            "retention_period": 86400,  # 24 hours
            "alert_thresholds": {
                "cpu": 90,
                "memory": 95,
                "disk": 90,
                "response_time": 5000
            }
        }
    
    async def initialize(self) -> None:
        """Initialize the performance analyzer"""
        self.logger.info("Initializing Performance and Scalability Analyzer...")
        
        # Load performance baselines if available
        await self._load_performance_baselines()
        
        # Initialize monitoring
        await self._initialize_monitoring()
        
        self.logger.info("Performance and Scalability Analyzer initialized")
    
    async def analyze_performance(self, project_path: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Perform comprehensive performance analysis"""
        self.logger.info(f"Performing {analysis_type} performance analysis on: {project_path}")
        
        try:
            analysis_results = {
                "analysis_id": f"perf_{int(time.time())}",
                "analysis_type": analysis_type,
                "project_path": project_path,
                "started_at": datetime.now(),
                "performance_score": 0,
                "bottlenecks": [],
                "scalability_assessment": {},
                "resource_analysis": {},
                "recommendations": []
            }
            
            # Perform different types of analysis
            if analysis_type in ["comprehensive", "code"]:
                code_analysis = await self._analyze_code_performance(project_path)
                analysis_results["bottlenecks"].extend(code_analysis["bottlenecks"])
            
            if analysis_type in ["comprehensive", "database"]:
                db_analysis = await self._analyze_database_performance(project_path)
                analysis_results["bottlenecks"].extend(db_analysis["bottlenecks"])
            
            if analysis_type in ["comprehensive", "architecture"]:
                arch_analysis = await self._analyze_architecture_performance(project_path)
                analysis_results["scalability_assessment"] = arch_analysis
            
            if analysis_type in ["comprehensive", "resource"]:
                resource_analysis = await self._analyze_resource_usage(project_path)
                analysis_results["resource_analysis"] = resource_analysis
            
            # Calculate overall performance score
            analysis_results["performance_score"] = self._calculate_performance_score(
                analysis_results["bottlenecks"],
                analysis_results.get("scalability_assessment", {}),
                analysis_results.get("resource_analysis", {})
            )
            
            # Generate recommendations
            analysis_results["recommendations"] = self._generate_performance_recommendations(
                analysis_results["bottlenecks"],
                analysis_results.get("scalability_assessment", {}),
                analysis_results.get("resource_analysis", {})
            )
            
            # Store analysis results
            self.analysis_cache[analysis_results["analysis_id"]] = analysis_results
            
            return {
                "success": True,
                "analysis_results": analysis_results,
                "summary": {
                    "performance_score": analysis_results["performance_score"],
                    "bottlenecks_found": len(analysis_results["bottlenecks"]),
                    "critical_issues": len([b for b in analysis_results["bottlenecks"] if b.severity == "critical"]),
                    "analysis_duration": (datetime.now() - analysis_results["started_at"]).total_seconds()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error performing performance analysis: {e}")
            return {"error": str(e)}
    
    async def _analyze_code_performance(self, project_path: str) -> Dict[str, Any]:
        """Analyze code-level performance issues"""
        self.logger.info("Analyzing code performance...")
        
        bottlenecks = []
        project_root = Path(project_path)
        
        # Code files to analyze
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs'}
        
        for root, dirs, files in os.walk(project_root):
            # Skip certain directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', 'env', 'build', 'dist']]
            
            for file in files:
                if any(file.endswith(ext) for ext in code_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # Analyze for performance patterns
                            file_bottlenecks = await self._analyze_file_performance(
                                file_path, content, Path(file_path).suffix[1:].lower()
                            )
                            bottlenecks.extend(file_bottlenecks)
                            
                    except Exception as e:
                        self.logger.warning(f"Error analyzing {file_path}: {e}")
        
        return {"bottlenecks": bottlenecks}
    
    async def _analyze_file_performance(self, file_path: str, content: str, language: str) -> List[Bottleneck]:
        """Analyze performance issues in a single file"""
        bottlenecks = []
        lines = content.split('\n')
        
        # Analyze for different performance patterns
        for pattern_name, pattern_config in self.performance_patterns.items():
            for indicator in pattern_config["indicators"]:
                matches = re.finditer(indicator, content, re.IGNORECASE)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    line_content = lines[line_number - 1].strip()
                    
                    # Calculate impact score based on pattern and context
                    impact_score = self._calculate_impact_score(
                        pattern_name, line_content, line_number, content
                    )
                    
                    if impact_score > 0.3:  # Only report significant issues
                        bottleneck = Bottleneck(
                            id=f"{file_path}_{line_number}_{pattern_name}",
                            type=pattern_name,
                            severity=self._get_severity_from_impact(impact_score),
                            description=self._generate_bottleneck_description(pattern_name, line_content),
                            file_path=file_path,
                            line_number=line_number,
                            impact_score=impact_score,
                            estimated_fix_time=self._estimate_fix_time(pattern_name),
                            recommendations=self._get_pattern_recommendations(pattern_name)
                        )
                        bottlenecks.append(bottleneck)
        
        # Language-specific performance analysis
        if language == 'python':
            bottlenecks.extend(await self._analyze_python_performance(file_path, content))
        elif language in ['javascript', 'typescript']:
            bottlenecks.extend(await self._analyze_js_performance(file_path, content))
        
        return bottlenecks
    
    async def _analyze_python_performance(self, file_path: str, content: str) -> List[Bottleneck]:
        """Analyze Python-specific performance issues"""
        bottlenecks = []
        
        try:
            tree = ast.parse(content)
            
            # Analyze function complexity
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_function_complexity(node)
                    if complexity > 10:
                        bottleneck = Bottleneck(
                            id=f"{file_path}_{node.lineno}_complex_function",
                            type="high_complexity",
                            severity="medium",
                            description=f"Function '{node.name}' has high complexity ({complexity})",
                            file_path=file_path,
                            line_number=node.lineno,
                            impact_score=min(complexity / 20, 1.0),
                            estimated_fix_time="2-4 hours",
                            recommendations=[
                                "Break down complex function into smaller functions",
                                "Extract helper methods",
                                "Consider using design patterns to simplify logic"
                            ]
                        )
                        bottlenecks.append(bottleneck)
                
                # Check for inefficient list operations
                elif isinstance(node, ast.For):
                    if self._is_inefficient_loop(node):
                        bottleneck = Bottleneck(
                            id=f"{file_path}_{node.lineno}_inefficient_loop",
                            type="inefficient_loop",
                            severity="medium",
                            description="Inefficient loop detected - consider using list comprehensions or built-in functions",
                            file_path=file_path,
                            line_number=node.lineno,
                            impact_score=0.6,
                            estimated_fix_time="30 minutes",
                            recommendations=[
                                "Use list comprehensions instead of loops",
                                "Consider using built-in functions like map() or filter()",
                                "Use generator expressions for large datasets"
                            ]
                        )
                        bottlenecks.append(bottleneck)
                
                # Check for global variables
                elif isinstance(node, ast.Global):
                    bottleneck = Bottleneck(
                        id=f"{file_path}_{node.lineno}_global_variable",
                        type="global_variable",
                        severity="low",
                        description="Global variable usage detected - can impact performance and maintainability",
                        file_path=file_path,
                        line_number=node.lineno,
                        impact_score=0.3,
                        estimated_fix_time="15 minutes",
                        recommendations=[
                            "Consider using dependency injection",
                            "Pass variables as parameters",
                            "Use class instances instead of global state"
                        ]
                    )
                    bottlenecks.append(bottleneck)
                    
        except Exception as e:
            self.logger.warning(f"Error parsing Python file {file_path}: {e}")
        
        return bottlenecks
    
    async def _analyze_js_performance(self, file_path: str, content: str) -> List[Bottleneck]:
        """Analyze JavaScript/TypeScript performance issues"""
        bottlenecks = []
        
        # Check for common JavaScript performance issues
        js_patterns = [
            (r'document\.getElementById', "dom_query", "medium", 
             "Direct DOM query detected - consider caching DOM elements"),
            (r'console\.log', "debug_code", "low",
             "Debug code detected - remove in production"),
            (r'setTimeout\([^,]+,\s*0\)', "blocking_timeout", "medium",
             "Zero timeout detected - can cause performance issues"),
            (r'new\s+Date\(\)', "date_creation", "low",
             "Date object creation in loop - consider creating once outside")
        ]
        
        for pattern, issue_type, severity, description in js_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                
                bottleneck = Bottleneck(
                    id=f"{file_path}_{line_number}_{issue_type}",
                    type=issue_type,
                    severity=severity,
                    description=description,
                    file_path=file_path,
                    line_number=line_number,
                    impact_score=0.4,
                    estimated_fix_time="15 minutes",
                    recommendations=[f"Optimize {issue_type} usage"]
                )
                bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    async def _analyze_database_performance(self, project_path: str) -> Dict[str, Any]:
        """Analyze database performance issues"""
        self.logger.info("Analyzing database performance...")
        
        bottlenecks = []
        project_root = Path(project_path)
        
        # Look for database-related files
        db_files = []
        db_patterns = ["*.sql", "models/*.py", "repositories/*.py", "dao/*.py"]
        
        for pattern in db_patterns:
            db_files.extend(project_root.rglob(pattern))
        
        for db_file in db_files:
            try:
                with open(db_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Analyze SQL queries
                    sql_bottlenecks = await self._analyze_sql_performance(
                        str(db_file), content
                    )
                    bottlenecks.extend(sql_bottlenecks)
                    
                    # Analyze ORM usage
                    if db_file.suffix == '.py':
                        orm_bottlenecks = await self._analyze_orm_performance(
                            str(db_file), content
                        )
                        bottlenecks.extend(orm_bottlenecks)
                        
            except Exception as e:
                self.logger.warning(f"Error analyzing {db_file}: {e}")
        
        return {"bottlenecks": bottlenecks}
    
    async def _analyze_sql_performance(self, file_path: str, content: str) -> List[Bottleneck]:
        """Analyze SQL query performance"""
        bottlenecks = []
        
        # Extract SQL queries
        sql_queries = re.findall(r'SELECT.*?(?:;|$)', content, re.IGNORECASE | re.DOTALL)
        
        for i, query in enumerate(sql_queries):
            query = query.strip()
            if not query:
                continue
            
            # Check for common performance issues
            issues = []
            
            # Check for SELECT *
            if 'select *' in query.lower():
                issues.append("Using SELECT * - specify only needed columns")
            
            # Check for missing WHERE clause
            if 'where' not in query.lower() and 'join' not in query.lower():
                issues.append("Missing WHERE clause - may return too many rows")
            
            # Check for ORDER BY without LIMIT
            if 'order by' in query.lower() and 'limit' not in query.lower():
                issues.append("ORDER BY without LIMIT - may be inefficient on large datasets")
            
            # Check for subqueries
            if 'select' in query.lower().count('select') > 1:
                issues.append("Complex subquery detected - consider optimization")
            
            if issues:
                line_number = content[:content.find(query)].count('\n') + 1
                
                bottleneck = Bottleneck(
                    id=f"{file_path}_{line_number}_sql_{i}",
                    type="sql_performance",
                    severity="high",
                    description=f"SQL query performance issues: {'; '.join(issues)}",
                    file_path=file_path,
                    line_number=line_number,
                    impact_score=0.8,
                    estimated_fix_time="1-2 hours",
                    recommendations=[
                        "Specify only needed columns instead of SELECT *",
                        "Add appropriate WHERE clauses",
                        "Use LIMIT with ORDER BY",
                        "Consider using indexes",
                        "Optimize complex subqueries"
                    ]
                )
                bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    async def _analyze_orm_performance(self, file_path: str, content: str) -> List[Bottleneck]:
        """Analyze ORM usage performance"""
        bottlenecks = []
        
        # Common ORM performance issues
        orm_patterns = [
            (r'for\s+\w+\s+in\s+\w+\.all\(\)', "n_plus_one_query", "high",
             "Potential N+1 query problem - use select_related/prefetch_related"),
            (r'\.get\(.+\)\s+in\s+for', "n_plus_one_query", "high",
             "N+1 query in loop - use bulk operations"),
            (r'\.filter\(.+\)\s+in\s+for', "n_plus_one_query", "high",
             "Query in loop - use bulk operations"),
            (r'\.save\(\)\s+in\s+for', "bulk_save", "medium",
             "Individual save() in loop - use bulk_create or bulk_update")
        ]
        
        for pattern, issue_type, severity, description in orm_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                
                bottleneck = Bottleneck(
                    id=f"{file_path}_{line_number}_{issue_type}",
                    type=issue_type,
                    severity=severity,
                    description=description,
                    file_path=file_path,
                    line_number=line_number,
                    impact_score=0.9 if severity == "high" else 0.6,
                    estimated_fix_time="1-3 hours",
                    recommendations=[
                        "Use select_related() or prefetch_related() for related objects",
                        "Use bulk operations instead of individual queries",
                        "Consider using prefetch() or select() optimizations",
                        "Use bulk_create() for multiple object creation"
                    ]
                )
                bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    async def _analyze_architecture_performance(self, project_path: str) -> Dict[str, Any]:
        """Analyze architecture-level performance and scalability"""
        self.logger.info("Analyzing architecture performance...")
        
        assessment = {
            "scalability_score": 0,
            "bottlenecks": [],
            "scaling_recommendations": [],
            "capacity_planning": {},
            "load_balancing": {},
            "caching_strategy": {}
        }
        
        # Analyze project structure for scalability
        project_root = Path(project_path)
        
        # Check for microservices architecture
        service_files = list(project_root.rglob("docker-compose.yml")) + list(project_root.rglob("service*.py"))
        if len(service_files) > 1:
            assessment["architecture_type"] = "microservices"
            assessment["scalability_score"] = 80
        else:
            assessment["architecture_type"] = "monolithic"
            assessment["scalability_score"] = 60
        
        # Check for caching implementation
        cache_files = list(project_root.rglob("*cache*")) + list(project_root.rglob("*redis*"))
        if cache_files:
            assessment["caching_strategy"] = {
                "implemented": True,
                "type": "redis" if any("redis" in str(f) for f in cache_files) else "custom",
                "effectiveness": "high"
            }
        else:
            assessment["caching_strategy"] = {
                "implemented": False,
                "recommendation": "Implement caching layer for frequently accessed data"
            }
        
        # Analyze database scaling
        db_files = list(project_root.rglob("*.sql")) + list(project_root.rglob("models*"))
        if db_files:
            assessment["database_scaling"] = {
                "current_setup": "single_instance",
                "scaling_options": ["read_replicas", "sharding", "partitioning"],
                "recommended": "read_replicas"
            }
        
        # Generate scaling recommendations
        assessment["scaling_recommendations"] = self._generate_scaling_recommendations(assessment)
        
        # Capacity planning
        assessment["capacity_planning"] = await self._generate_capacity_plan(assessment)
        
        return assessment
    
    async def _analyze_resource_usage(self, project_path: str) -> Dict[str, Any]:
        """Analyze resource usage patterns"""
        self.logger.info("Analyzing resource usage...")
        
        # In a real implementation, this would collect actual resource metrics
        # For now, we'll simulate resource analysis
        
        resource_analysis = {
            "cpu_usage": {
                "current": 45,
                "peak": 78,
                "trend": "stable",
                "recommendations": ["Monitor for spikes", "Consider auto-scaling"]
            },
            "memory_usage": {
                "current": 62,
                "peak": 85,
                "trend": "increasing",
                "recommendations": ["Investigate memory leaks", "Consider memory optimization"]
            },
            "disk_usage": {
                "current": 34,
                "peak": 45,
                "trend": "stable",
                "recommendations": ["Monitor growth", "Plan for expansion"]
            },
            "network_io": {
                "incoming": 150,  # MB/s
                "outgoing": 200,  # MB/s
                "trend": "increasing",
                "recommendations": ["Monitor bandwidth usage", "Consider CDN implementation"]
            }
        }
        
        return resource_analysis
    
    def _calculate_impact_score(self, pattern_name: str, line_content: str, line_number: int, content: str) -> float:
        """Calculate impact score for a performance issue"""
        base_scores = {
            "n_plus_one_queries": 0.9,
            "inefficient_loops": 0.6,
            "memory_leaks": 0.8,
            "blocking_operations": 0.7,
            "high_complexity": 0.5,
            "global_variable": 0.3,
            "dom_query": 0.4,
            "debug_code": 0.2,
            "sql_performance": 0.8
        }
        
        base_score = base_scores.get(pattern_name, 0.5)
        
        # Adjust based on context
        context_multiplier = 1.0
        
        # Check if it's in a critical path (e.g., main execution, frequently called functions)
        if "def main" in content[:line_number * 50] or "if __name__" in content[:line_number * 50]:
            context_multiplier *= 1.2
        
        # Check if it's in a loop
        if "for " in line_content or "while " in line_content:
            context_multiplier *= 1.3
        
        # Check if it's in a frequently called area (heuristic)
        if any(keyword in line_content.lower() for keyword in ["request", "query", "process", "handle"]):
            context_multiplier *= 1.1
        
        return min(base_score * context_multiplier, 1.0)
    
    def _get_severity_from_impact(self, impact_score: float) -> str:
        """Convert impact score to severity level"""
        if impact_score >= 0.8:
            return "critical"
        elif impact_score >= 0.6:
            return "high"
        elif impact_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _generate_bottleneck_description(self, pattern_name: str, line_content: str) -> str:
        """Generate description for performance bottleneck"""
        descriptions = {
            "n_plus_one_queries": f"N+1 query pattern detected: {line_content}",
            "inefficient_loops": f"Inefficient loop detected: {line_content}",
            "memory_leaks": f"Potential memory leak: {line_content}",
            "blocking_operations": f"Blocking operation detected: {line_content}",
            "high_complexity": f"High complexity code: {line_content}",
            "global_variable": f"Global variable usage: {line_content}",
            "sql_performance": f"SQL performance issue: {line_content}"
        }
        
        return descriptions.get(pattern_name, f"Performance issue detected: {line_content}")
    
    def _estimate_fix_time(self, pattern_name: str) -> str:
        """Estimate time required to fix a performance issue"""
        fix_times = {
            "n_plus_one_queries": "2-4 hours",
            "inefficient_loops": "30 minutes - 2 hours",
            "memory_leaks": "4-8 hours",
            "blocking_operations": "1-3 hours",
            "high_complexity": "4-16 hours",
            "global_variable": "15-30 minutes",
            "sql_performance": "1-4 hours",
            "dom_query": "15-30 minutes",
            "debug_code": "5 minutes"
        }
        
        return fix_times.get(pattern_name, "1-2 hours")
    
    def _get_pattern_recommendations(self, pattern_name: str) -> List[str]:
        """Get recommendations for a specific performance pattern"""
        recommendations = {
            "n_plus_one_queries": [
                "Use select_related() or prefetch_related() for related objects",
                "Implement batch loading of data",
                "Use bulk operations instead of individual queries",
                "Consider using prefetch() or select() optimizations"
            ],
            "inefficient_loops": [
                "Use list comprehensions instead of loops",
                "Consider using built-in functions like map() or filter()",
                "Use generator expressions for large datasets",
                "Optimize loop conditions and invariants"
            ],
            "memory_leaks": [
                "Use weak references for circular dependencies",
                "Implement proper cleanup in __del__ methods",
                "Use context managers for resource management",
                "Monitor memory usage with profiling tools"
            ],
            "blocking_operations": [
                "Use asynchronous operations instead of blocking calls",
                "Implement timeouts for blocking operations",
                "Consider using thread pools for CPU-bound operations",
                "Use non-blocking I/O operations"
            ],
            "high_complexity": [
                "Break down complex functions into smaller ones",
                "Extract helper methods and utilities",
                "Use design patterns to simplify logic",
                "Consider refactoring for better maintainability"
            ],
            "global_variable": [
                "Consider using dependency injection",
                "Pass variables as parameters",
                "Use class instances instead of global state",
                "Implement proper encapsulation"
            ],
            "sql_performance": [
                "Specify only needed columns instead of SELECT *",
                "Add appropriate WHERE clauses",
                "Use LIMIT with ORDER BY",
                "Consider using indexes",
                "Optimize complex subqueries"
            ]
        }
        
        return recommendations.get(pattern_name, ["Optimize the identified performance issue"])
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def _is_inefficient_loop(self, node: ast.For) -> bool:
        """Check if a for loop is inefficient"""
        # Look for patterns like: for i in range(len(some_list))
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
            if node.iter.func.id == 'range':
                if len(node.iter.args) == 1 and isinstance(node.iter.args[0], ast.Call):
                    if isinstance(node.iter.args[0].func, ast.Name) and node.iter.args[0].func.id == 'len':
                        return True
        return False
    
    def _calculate_performance_score(self, bottlenecks: List[Bottleneck], 
                                   scalability_assessment: Dict[str, Any],
                                   resource_analysis: Dict[str, Any]) -> float:
        """Calculate overall performance score"""
        # Score based on bottlenecks
        bottleneck_penalty = 0
        for bottleneck in bottlenecks:
            severity_weights = {"critical": 20, "high": 10, "medium": 5, "low": 2}
            bottleneck_penalty += severity_weights.get(bottleneck.severity, 2)
        
        # Score based on scalability
        scalability_score = scalability_assessment.get("scalability_score", 50)
        
        # Score based on resource usage
        resource_score = 100
        if resource_analysis:
            cpu_usage = resource_analysis.get("cpu_usage", {}).get("current", 0)
            memory_usage = resource_analysis.get("memory_usage", {}).get("current", 0)
            
            if cpu_usage > 80:
                resource_score -= 20
            elif cpu_usage > 60:
                resource_score -= 10
            
            if memory_usage > 85:
                resource_score -= 20
            elif memory_usage > 70:
                resource_score -= 10
        
        # Calculate final score
        final_score = max(0, 100 - bottleneck_penalty + (scalability_score - 50) * 0.5 + (resource_score - 100) * 0.3)
        
        return round(final_score, 2)
    
    def _generate_performance_recommendations(self, bottlenecks: List[Bottleneck],
                                           scalability_assessment: Dict[str, Any],
                                           resource_analysis: Dict[str, Any]) -> List[str]:
        """Generate comprehensive performance recommendations"""
        recommendations = []
        
        # Recommendations based on bottlenecks
        bottleneck_types = defaultdict(int)
        for bottleneck in bottlenecks:
            bottleneck_types[bottleneck.type] += 1
        
        if bottleneck_types["n_plus_one_queries"] > 0:
            recommendations.append("Address N+1 query issues by implementing proper ORM optimizations")
        
        if bottleneck_types["inefficient_loops"] > 0:
            recommendations.append("Optimize inefficient loops using built-in functions and comprehensions")
        
        if bottleneck_types["memory_leaks"] > 0:
            recommendations.append("Investigate and fix memory leaks using profiling tools")
        
        if bottleneck_types["sql_performance"] > 0:
            recommendations.append("Optimize SQL queries and ensure proper indexing")
        
        # Recommendations based on scalability
        if scalability_assessment.get("scalability_score", 0) < 70:
            recommendations.append("Improve architecture scalability - consider microservices or better separation of concerns")
        
        if not scalability_assessment.get("caching_strategy", {}).get("implemented", False):
            recommendations.append("Implement caching strategy to improve performance")
        
        # Recommendations based on resource usage
        if resource_analysis:
            cpu_trend = resource_analysis.get("cpu_usage", {}).get("trend", "")
            memory_trend = resource_analysis.get("memory_usage", {}).get("trend", "")
            
            if cpu_trend == "increasing":
                recommendations.append("Monitor increasing CPU usage and consider optimization")
            
            if memory_trend == "increasing":
                recommendations.append("Investigate increasing memory usage and potential leaks")
        
        # General recommendations
        if len(bottlenecks) > 10:
            recommendations.append("Consider implementing comprehensive performance monitoring and alerting")
        
        if any(b.severity == "critical" for b in bottlenecks):
            recommendations.append("Address critical performance issues immediately")
        
        return recommendations
    
    def _generate_scaling_recommendations(self, assessment: Dict[str, Any]) -> List[str]:
        """Generate scaling recommendations"""
        recommendations = []
        
        architecture_type = assessment.get("architecture_type", "unknown")
        
        if architecture_type == "monolithic":
            recommendations.extend([
                "Consider migrating to microservices for better scalability",
                "Implement horizontal scaling with load balancers",
                "Use containerization for easier deployment and scaling"
            ])
        else:
            recommendations.extend([
                "Optimize inter-service communication",
                "Implement service mesh for better traffic management",
                "Consider auto-scaling based on load metrics"
            ])
        
        if not assessment.get("caching_strategy", {}).get("implemented", False):
            recommendations.append("Implement distributed caching for better performance")
        
        return recommendations
    
    async def _generate_capacity_plan(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate capacity planning recommendations"""
        capacity_plan = {
            "current_capacity": {
                "users": 1000,
                "requests_per_second": 100,
                "data_size": "10GB"
            },
            "projected_growth": {
                "user_growth_rate": "10% monthly",
                "data_growth_rate": "20% monthly"
            },
            "scaling_points": [
                {
                    "metric": "users",
                    "current": 1000,
                    "limit": 10000,
                    "time_to_limit": "8 months",
                    "action": "Add application servers"
                },
                {
                    "metric": "data_size",
                    "current": "10GB",
                    "limit": "100GB",
                    "time_to_limit": "6 months",
                    "action": "Implement database sharding"
                }
            ],
            "recommendations": [
                "Monitor growth metrics regularly",
                "Plan for infrastructure scaling",
                "Consider cloud auto-scaling solutions"
            ]
        }
        
        return capacity_plan
    
    async def _load_performance_baselines(self) -> None:
        """Load performance baselines from configuration or historical data"""
        # In a real implementation, this would load from a configuration file
        # or historical performance data
        pass
    
    async def _initialize_monitoring(self) -> None:
        """Initialize performance monitoring"""
        # In a real implementation, this would set up monitoring agents
        # and configure alerting
        pass
    
    async def generate_performance_report(self, analysis_id: str) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if analysis_id not in self.analysis_cache:
            return {"error": "Analysis ID not found"}
        
        analysis_data = self.analysis_cache[analysis_id]
        
        report = {
            "analysis_id": analysis_id,
            "generated_at": datetime.now(),
            "executive_summary": self._generate_performance_summary(analysis_data),
            "detailed_findings": analysis_data["bottlenecks"],
            "scalability_assessment": analysis_data.get("scalability_assessment", {}),
            "resource_analysis": analysis_data.get("resource_analysis", {}),
            "performance_score": analysis_data["performance_score"],
            "recommendations": analysis_data["recommendations"],
            "action_plan": self._generate_performance_action_plan(analysis_data["bottlenecks"])
        }
        
        return {
            "success": True,
            "performance_report": report
        }
    
    def _generate_performance_summary(self, analysis_data: Dict[str, Any]) -> str:
        """Generate executive performance summary"""
        bottlenecks = analysis_data["bottlenecks"]
        performance_score = analysis_data["performance_score"]
        
        critical_count = len([b for b in bottlenecks if b.severity == "critical"])
        high_count = len([b for b in bottlenecks if b.severity == "high"])
        medium_count = len([b for b in bottlenecks if b.severity == "medium"])
        low_count = len([b for b in bottlenecks if b.severity == "low"])
        
        summary = f"""
Performance Analysis Executive Summary
=====================================

Analysis ID: {analysis_data["analysis_id"]}
Date: {analysis_data["started_at"].strftime('%Y-%m-%d %H:%M:%S')}

Overall Performance Score: {performance_score}/100

Performance Issues Found: {len(bottlenecks)}
- Critical: {critical_count}
- High: {high_count}
- Medium: {medium_count}
- Low: {low_count}

Performance Posture: {'Excellent' if performance_score >= 90 else 'Good' if performance_score >= 70 else 'Fair' if performance_score >= 50 else 'Poor'}
"""
        
        return summary
    
    def _generate_performance_action_plan(self, bottlenecks: List[Bottleneck]) -> Dict[str, Any]:
        """Generate performance improvement action plan"""
        action_plan = {
            "immediate_actions": [],
            "short_term_actions": [],
            "long_term_actions": [],
            "estimated_benefits": {},
            "resource_requirements": {}
        }
        
        # Categorize bottlenecks by severity and impact
        critical_bottlenecks = [b for b in bottlenecks if b.severity == "critical"]
        high_bottlenecks = [b for b in bottlenecks if b.severity == "high"]
        medium_bottlenecks = [b for b in bottlenecks if b.severity == "medium"]
        low_bottlenecks = [b for b in bottlenecks if b.severity == "low"]
        
        # Immediate actions (critical bottlenecks)
        for bottleneck in critical_bottlenecks:
            action_plan["immediate_actions"].append({
                "bottleneck": bottleneck.description,
                "file": bottleneck.file_path,
                "action": bottleneck.recommendations[0] if bottleneck.recommendations else "Optimize",
                "priority": "immediate",
                "estimated_effort": bottleneck.estimated_fix_time,
                "expected_improvement": f"{int(bottleneck.impact_score * 100)}% performance gain"
            })
        
        # Short term actions (high bottlenecks)
        for bottleneck in high_bottlenecks:
            action_plan["short_term_actions"].append({
                "bottleneck": bottleneck.description,
                "file": bottleneck.file_path,
                "action": bottleneck.recommendations[0] if bottleneck.recommendations else "Optimize",
                "priority": "high",
                "estimated_effort": bottleneck.estimated_fix_time,
                "expected_improvement": f"{int(bottleneck.impact_score * 50)}% performance gain"
            })
        
        # Long term actions (medium and low bottlenecks)
        for bottleneck in medium_bottlenecks + low_bottlenecks:
            action_plan["long_term_actions"].append({
                "bottleneck": bottleneck.description,
                "file": bottleneck.file_path,
                "action": bottleneck.recommendations[0] if bottleneck.recommendations else "Optimize",
                "priority": "medium",
                "estimated_effort": bottleneck.estimated_fix_time,
                "expected_improvement": f"{int(bottleneck.impact_score * 25)}% performance gain"
            })
        
        # Estimated benefits
        total_impact = sum(b.impact_score for b in bottlenecks)
        action_plan["estimated_benefits"] = {
            "performance_improvement": f"{int(total_impact * 30)}%",
            "scalability_improvement": f"{int(total_impact * 20)}%",
            "resource_efficiency": f"{int(total_impact * 15)}%"
        }
        
        # Resource requirements
        action_plan["resource_requirements"] = {
            "developers": 2,
            "performance_experts": 1,
            "testing_resources": "moderate",
            "tools": "profiling_tools, monitoring_tools, load_testing_tools"
        }
        
        return action_plan
    
    async def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get performance dashboard data"""
        return {
            "success": True,
            "dashboard": {
                "recent_analyses": [
                    {
                        "analysis_id": analysis_id,
                        "date": analysis_data["started_at"],
                        "score": analysis_data["performance_score"],
                        "bottlenecks": len(analysis_data["bottlenecks"])
                    }
                    for analysis_id, analysis_data in list(self.analysis_cache.items())[-5:]
                ],
                "performance_trends": {
                    "scores": [data["performance_score"] for data in self.analysis_cache.values()[-10:]],
                    "bottleneck_counts": [len(data["bottlenecks"]) for data in self.analysis_cache.values()[-10:]]
                },
                "top_bottlenecks": [
                    {
                        "type": b.type,
                        "severity": b.severity,
                        "file": b.file_path,
                        "impact": b.impact_score
                    }
                    for b in sorted(self.bottlenecks, key=lambda x: x.impact_score, reverse=True)[:5]
                ],
                "scalability_metrics": {
                    "current_capacity": "1000 users",
                    "projected_limit": "10000 users",
                    "time_to_limit": "8 months"
                }
            }
        }