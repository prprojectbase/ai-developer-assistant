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
from collections import defaultdict

from ..config.settings import get_settings


@dataclass
class SystemContext:
    """System context information"""
    project_root: str
    architecture_patterns: List[str]
    frameworks: List[str]
    dependencies: Dict[str, str]
    configuration_files: List[str]
    deployment_environment: str
    external_services: List[str]
    database_schemas: Dict[str, Any]
    api_endpoints: List[Dict[str, Any]]
    security_policies: Dict[str, Any]


@dataclass
class CodeContext:
    """Code context information"""
    file_path: str
    language: str
    imports: List[str]
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    dependencies: List[str]
    complexity_metrics: Dict[str, float]
    test_coverage: float
    security_issues: List[Dict[str, Any]]


@dataclass
class OperationalContext:
    """Operational context information"""
    deployment_config: Dict[str, Any]
    monitoring_setup: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    error_rates: Dict[str, float]
    resource_usage: Dict[str, float]
    uptime_stats: Dict[str, Any]
    log_patterns: List[Dict[str, Any]]


@dataclass
class BusinessContext:
    """Business context information"""
    requirements: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    stakeholders: List[Dict[str, Any]]
    timeline: Dict[str, Any]
    budget: Dict[str, Any]
    risk_factors: List[Dict[str, Any]]


class AdvancedAIContext:
    """Advanced AI Context Awareness System"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Context stores
        self.system_context: Optional[SystemContext] = None
        self.code_contexts: Dict[str, CodeContext] = {}
        self.operational_context: Optional[OperationalContext] = None
        self.business_context: Optional[BusinessContext] = None
        
        # Dependency graph
        self.dependency_graph = nx.DiGraph()
        
        # Context analysis cache
        self.context_cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Pattern recognition
        self.code_patterns: Dict[str, List[Dict[str, Any]]] = {}
        self.architecture_patterns: Dict[str, List[str]] = {}
        
        # Context awareness flags
        self.context_awareness_level = 0
        self.max_awareness_level = 5
        
        # Analysis statistics
        self.analysis_stats = {
            "files_analyzed": 0,
            "dependencies_mapped": 0,
            "patterns_identified": 0,
            "security_issues_found": 0,
            "performance_bottlenecks": 0,
            "last_analysis_time": None
        }
    
    async def initialize(self) -> None:
        """Initialize the context awareness system"""
        self.logger.info("Initializing Advanced AI Context Awareness...")
        
        # Load existing context if available
        await self._load_context_cache()
        
        # Initialize pattern databases
        await self._initialize_pattern_databases()
        
        self.logger.info("Advanced AI Context Awareness initialized")
    
    async def analyze_project_context(self, project_path: str) -> Dict[str, Any]:
        """Analyze complete project context"""
        self.logger.info(f"Analyzing project context: {project_path}")
        
        try:
            # Analyze system context
            self.system_context = await self._analyze_system_context(project_path)
            
            # Analyze code contexts
            await self._analyze_all_code_contexts(project_path)
            
            # Analyze operational context
            self.operational_context = await self._analyze_operational_context(project_path)
            
            # Analyze business context
            self.business_context = await self._analyze_business_context(project_path)
            
            # Build dependency graph
            await self._build_dependency_graph()
            
            # Update awareness level
            self._update_awareness_level()
            
            # Cache results
            await self._cache_context_analysis()
            
            # Update statistics
            self.analysis_stats["last_analysis_time"] = datetime.now()
            
            return {
                "success": True,
                "awareness_level": self.context_awareness_level,
                "system_context": self._context_to_dict(self.system_context),
                "code_files_analyzed": len(self.code_contexts),
                "operational_context": self._context_to_dict(self.operational_context),
                "business_context": self._context_to_dict(self.business_context),
                "dependencies_mapped": self.dependency_graph.number_of_edges(),
                "statistics": self.analysis_stats
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing project context: {e}")
            return {"error": str(e)}
    
    async def _analyze_system_context(self, project_path: str) -> SystemContext:
        """Analyze system-level context"""
        self.logger.info("Analyzing system context...")
        
        # Detect project structure
        project_root = Path(project_path).resolve()
        
        # Identify architecture patterns
        architecture_patterns = await self._identify_architecture_patterns(project_root)
        
        # Detect frameworks and technologies
        frameworks = await self._detect_frameworks(project_root)
        
        # Analyze dependencies
        dependencies = await self._analyze_dependencies(project_root)
        
        # Find configuration files
        config_files = await self._find_configuration_files(project_root)
        
        # Determine deployment environment
        deployment_env = await self._determine_deployment_environment(project_root)
        
        # Identify external services
        external_services = await self._identify_external_services(project_root)
        
        # Analyze database schemas
        database_schemas = await self._analyze_database_schemas(project_root)
        
        # Extract API endpoints
        api_endpoints = await self._extract_api_endpoints(project_root)
        
        # Analyze security policies
        security_policies = await self._analyze_security_policies(project_root)
        
        return SystemContext(
            project_root=str(project_root),
            architecture_patterns=architecture_patterns,
            frameworks=frameworks,
            dependencies=dependencies,
            configuration_files=config_files,
            deployment_environment=deployment_env,
            external_services=external_services,
            database_schemas=database_schemas,
            api_endpoints=api_endpoints,
            security_policies=security_policies
        )
    
    async def _analyze_all_code_contexts(self, project_path: str) -> None:
        """Analyze context for all code files"""
        self.logger.info("Analyzing code contexts...")
        
        project_root = Path(project_path)
        
        # Supported code file extensions
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.php', '.rb'}
        
        # Find all code files
        code_files = []
        for root, dirs, files in os.walk(project_root):
            # Skip virtual environments and build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', 'env', 'build', 'dist']]
            
            for file in files:
                if any(file.endswith(ext) for ext in code_extensions):
                    code_files.append(os.path.join(root, file))
        
        # Analyze each file
        for file_path in code_files:
            try:
                code_context = await self._analyze_code_context(file_path)
                self.code_contexts[file_path] = code_context
                self.analysis_stats["files_analyzed"] += 1
            except Exception as e:
                self.logger.warning(f"Error analyzing {file_path}: {e}")
    
    async def _analyze_code_context(self, file_path: str) -> CodeContext:
        """Analyze context for a single code file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determine language
            language = self._detect_language(file_path)
            
            # Parse imports
            imports = self._parse_imports(content, language)
            
            # Extract functions and classes
            functions, classes = self._parse_code_structure(content, language)
            
            # Analyze dependencies
            dependencies = self._analyze_file_dependencies(content, language)
            
            # Calculate complexity metrics
            complexity_metrics = self._calculate_complexity_metrics(content, language)
            
            # Estimate test coverage
            test_coverage = self._estimate_test_coverage(file_path, content)
            
            # Identify security issues
            security_issues = self._identify_security_issues(content, language)
            
            return CodeContext(
                file_path=file_path,
                language=language,
                imports=imports,
                functions=functions,
                classes=classes,
                dependencies=dependencies,
                complexity_metrics=complexity_metrics,
                test_coverage=test_coverage,
                security_issues=security_issues
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing code context for {file_path}: {e}")
            raise
    
    async def _analyze_operational_context(self, project_path: str) -> OperationalContext:
        """Analyze operational context"""
        self.logger.info("Analyzing operational context...")
        
        # Analyze deployment configuration
        deployment_config = await self._analyze_deployment_config(project_path)
        
        # Analyze monitoring setup
        monitoring_setup = await self._analyze_monitoring_setup(project_path)
        
        # Collect performance metrics
        performance_metrics = await self._collect_performance_metrics(project_path)
        
        # Analyze error rates
        error_rates = await self._analyze_error_rates(project_path)
        
        # Analyze resource usage
        resource_usage = await self._analyze_resource_usage(project_path)
        
        # Analyze uptime statistics
        uptime_stats = await self._analyze_uptime_stats(project_path)
        
        # Analyze log patterns
        log_patterns = await self._analyze_log_patterns(project_path)
        
        return OperationalContext(
            deployment_config=deployment_config,
            monitoring_setup=monitoring_setup,
            performance_metrics=performance_metrics,
            error_rates=error_rates,
            resource_usage=resource_usage,
            uptime_stats=uptime_stats,
            log_patterns=log_patterns
        )
    
    async def _analyze_business_context(self, project_path: str) -> BusinessContext:
        """Analyze business context"""
        self.logger.info("Analyzing business context...")
        
        # Extract requirements
        requirements = await self._extract_requirements(project_path)
        
        # Identify constraints
        constraints = await self._identify_constraints(project_path)
        
        # Identify stakeholders
        stakeholders = await self._identify_stakeholders(project_path)
        
        # Analyze timeline
        timeline = await self._analyze_timeline(project_path)
        
        # Analyze budget
        budget = await self._analyze_budget(project_path)
        
        # Identify risk factors
        risk_factors = await self._identify_risk_factors(project_path)
        
        return BusinessContext(
            requirements=requirements,
            constraints=constraints,
            stakeholders=stakeholders,
            timeline=timeline,
            budget=budget,
            risk_factors=risk_factors
        )
    
    async def _build_dependency_graph(self) -> None:
        """Build comprehensive dependency graph"""
        self.logger.info("Building dependency graph...")
        
        # Add nodes for all code files
        for file_path, code_context in self.code_contexts.items():
            self.dependency_graph.add_node(file_path, context=code_context)
        
        # Add edges for dependencies
        for file_path, code_context in self.code_contexts.items():
            for dep in code_context.dependencies:
                # Find the actual file that provides this dependency
                dep_file = await self._find_dependency_file(dep)
                if dep_file and dep_file in self.code_contexts:
                    self.dependency_graph.add_edge(file_path, dep_file, type="import")
        
        # Add system-level dependencies
        if self.system_context:
            for framework in self.system_context.frameworks:
                self.dependency_graph.add_node(f"framework:{framework}", type="framework")
                # Connect files using this framework
                for file_path, code_context in self.code_contexts.items():
                    if framework.lower() in code_context.file_path.lower():
                        self.dependency_graph.add_edge(file_path, f"framework:{framework}", type="uses")
        
        self.analysis_stats["dependencies_mapped"] = self.dependency_graph.number_of_edges()
    
    async def _identify_architecture_patterns(self, project_root: Path) -> List[str]:
        """Identify architecture patterns used in the project"""
        patterns = []
        
        # Check for MVC pattern
        if (project_root / "controllers").exists() or (project_root / "views").exists() or (project_root / "models").exists():
            patterns.append("MVC")
        
        # Check for microservices pattern
        if (project_root / "docker-compose.yml").exists() or len(list(project_root.glob("*/Dockerfile"))) > 1:
            patterns.append("Microservices")
        
        # Check for serverless pattern
        if (project_root / "serverless.yml").exists() or (project_root / "functions").exists():
            patterns.append("Serverless")
        
        # Check for monolithic pattern
        if len(list(project_root.rglob("*.py"))) > 50 and not any(p in patterns for p in ["Microservices", "Serverless"]):
            patterns.append("Monolithic")
        
        # Check for layered architecture
        if (project_root / "src" / "layers").exists() or (project_root / "layers").exists():
            patterns.append("Layered")
        
        return patterns
    
    async def _detect_frameworks(self, project_root: Path) -> List[str]:
        """Detect frameworks and technologies used"""
        frameworks = []
        
        # Check package.json for Node.js frameworks
        package_json = project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                    dependencies = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}
                    
                    if "express" in dependencies:
                        frameworks.append("Express.js")
                    if "react" in dependencies:
                        frameworks.append("React")
                    if "vue" in dependencies:
                        frameworks.append("Vue.js")
                    if "angular" in dependencies:
                        frameworks.append("Angular")
                    if "next" in dependencies:
                        frameworks.append("Next.js")
            except Exception as e:
                self.logger.warning(f"Error reading package.json: {e}")
        
        # Check requirements.txt for Python frameworks
        requirements_txt = project_root / "requirements.txt"
        if requirements_txt.exists():
            try:
                with open(requirements_txt, 'r') as f:
                    content = f.read().lower()
                    if "django" in content:
                        frameworks.append("Django")
                    if "flask" in content:
                        frameworks.append("Flask")
                    if "fastapi" in content:
                        frameworks.append("FastAPI")
                    if "sqlalchemy" in content:
                        frameworks.append("SQLAlchemy")
            except Exception as e:
                self.logger.warning(f"Error reading requirements.txt: {e}")
        
        return frameworks
    
    async def _analyze_dependencies(self, project_root: Path) -> Dict[str, str]:
        """Analyze project dependencies"""
        dependencies = {}
        
        # Python dependencies
        requirements_files = list(project_root.rglob("requirements*.txt"))
        for req_file in requirements_files:
            try:
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '==' in line:
                                name, version = line.split('==', 1)
                                dependencies[name.strip()] = version.strip()
                            else:
                                dependencies[line.strip()] = "latest"
            except Exception as e:
                self.logger.warning(f"Error reading {req_file}: {e}")
        
        # Node.js dependencies
        package_json = project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                    all_deps = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}
                    for name, version in all_deps.items():
                        dependencies[name] = version
            except Exception as e:
                self.logger.warning(f"Error reading package.json: {e}")
        
        return dependencies
    
    async def _find_configuration_files(self, project_root: Path) -> List[str]:
        """Find configuration files"""
        config_patterns = [
            "*.json", "*.yaml", "*.yml", "*.toml", "*.ini", "*.cfg",
            "*.conf", "*.config", ".env*", "Dockerfile", "docker-compose*"
        ]
        
        config_files = []
        for pattern in config_patterns:
            config_files.extend(str(f) for f in project_root.rglob(pattern))
        
        return config_files
    
    async def _determine_deployment_environment(self, project_root: Path) -> str:
        """Determine deployment environment"""
        # Check for cloud-specific files
        if (project_root / "serverless.yml").exists():
            return "serverless"
        if (project_root / "terraform").exists():
            return "terraform"
        if (project_root / "kubernetes").exists() or (project_root / "k8s").exists():
            return "kubernetes"
        if (project_root / "docker-compose.yml").exists():
            return "docker"
        
        # Check for traditional deployment
        if (project_root / "deploy").exists() or (project_root / "deployment").exists():
            return "traditional"
        
        return "local"
    
    async def _identify_external_services(self, project_root: Path) -> List[str]:
        """Identify external services used"""
        services = []
        
        # Check configuration files for external service references
        config_files = await self._find_configuration_files(project_root)
        
        for config_file in config_files:
            try:
                with open(config_file, 'r') as f:
                    content = f.read().lower()
                    
                    # Common external services
                    service_patterns = [
                        ("database", ["mysql", "postgresql", "mongodb", "redis", "elasticsearch"]),
                        ("storage", ["aws", "s3", "azure", "gcs", "blob"]),
                        ("messaging", ["rabbitmq", "kafka", "sns", "sqs"]),
                        ("auth", ["auth0", "okta", "firebase", "cognito"]),
                        ("monitoring", ["datadog", "newrelic", "prometheus", "grafana"])
                    ]
                    
                    for service_type, patterns in service_patterns:
                        for pattern in patterns:
                            if pattern in content:
                                services.append(f"{service_type}:{pattern}")
            except Exception as e:
                self.logger.warning(f"Error reading {config_file}: {e}")
        
        return list(set(services))
    
    async def _analyze_database_schemas(self, project_root: Path) -> Dict[str, Any]:
        """Analyze database schemas"""
        schemas = {}
        
        # Look for migration files
        migration_dirs = ["migrations", "schema", "db", "database"]
        for migration_dir in migration_dirs:
            migration_path = project_root / migration_dir
            if migration_path.exists():
                schemas[migration_dir] = {
                    "type": "migration_files",
                    "files": [str(f) for f in migration_path.rglob("*.sql")] + 
                            [str(f) for f in migration_path.rglob("*.py")]
                }
        
        # Look for ORM models
        for file_path, code_context in self.code_contexts.items():
            if "model" in file_path.lower() or "entity" in file_path.lower():
                schemas[file_path] = {
                    "type": "orm_models",
                    "classes": [cls["name"] for cls in code_context.classes]
                }
        
        return schemas
    
    async def _extract_api_endpoints(self, project_root: Path) -> List[Dict[str, Any]]:
        """Extract API endpoints from code"""
        endpoints = []
        
        for file_path, code_context in self.code_contexts.items():
            # Look for route definitions
            if any(keyword in file_path.lower() for keyword in ["route", "api", "controller", "view"]):
                for func in code_context.functions:
                    # Check for common route patterns
                    func_content = func.get("content", "").lower()
                    if any(pattern in func_content for pattern in ["@route", "@app.route", "router.", "fastapi.", "get(", "post("]):
                        endpoints.append({
                            "file": file_path,
                            "function": func["name"],
                            "type": "api_endpoint",
                            "complexity": code_context.complexity_metrics.get("cyclomatic_complexity", 0)
                        })
        
        return endpoints
    
    async def _analyze_security_policies(self, project_root: Path) -> Dict[str, Any]:
        """Analyze security policies"""
        policies = {
            "authentication": [],
            "authorization": [],
            "encryption": [],
            "validation": [],
            "headers": []
        }
        
        # Check for security-related files
        security_files = list(project_root.rglob("*security*")) + list(project_root.rglob("*auth*"))
        
        for security_file in security_files:
            try:
                with open(security_file, 'r') as f:
                    content = f.read().lower()
                    
                    if "auth" in content:
                        policies["authentication"].append(str(security_file))
                    if "permission" in content or "role" in content:
                        policies["authorization"].append(str(security_file))
                    if "encrypt" in content or "hash" in content:
                        policies["encryption"].append(str(security_file))
                    if "validate" in content or "sanitize" in content:
                        policies["validation"].append(str(security_file))
                    if "header" in content or "cors" in content:
                        policies["headers"].append(str(security_file))
            except Exception as e:
                self.logger.warning(f"Error reading {security_file}: {e}")
        
        return policies
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby'
        }
        return language_map.get(ext, 'unknown')
    
    def _parse_imports(self, content: str, language: str) -> List[str]:
        """Parse import statements"""
        imports = []
        
        if language == 'python':
            # Python imports
            import_patterns = [
                r'import\s+(\w+(?:\.\w+)*)',
                r'from\s+(\w+(?:\.\w+)*)\s+import',
                r'from\s+(\w+(?:\.\w+)*)\s+import\s+.*'
            ]
        elif language in ['javascript', 'typescript']:
            # JS/TS imports
            import_patterns = [
                r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'require\([\'"]([^\'"]+)[\'"]\)'
            ]
        else:
            return imports
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)
        
        return list(set(imports))
    
    def _parse_code_structure(self, content: str, language: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Parse code structure to extract functions and classes"""
        functions = []
        classes = []
        
        if language == 'python':
            try:
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        functions.append({
                            "name": node.name,
                            "args": [arg.arg for arg in node.args.args],
                            "line_number": node.lineno,
                            "docstring": ast.get_docstring(node),
                            "decorators": [dec.id if isinstance(dec, ast.Name) else str(dec) for dec in node.decorator_list]
                        })
                    elif isinstance(node, ast.ClassDef):
                        classes.append({
                            "name": node.name,
                            "line_number": node.lineno,
                            "docstring": ast.get_docstring(node),
                            "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                            "bases": [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]
                        })
            except Exception as e:
                self.logger.warning(f"Error parsing Python code: {e}")
        
        return functions, classes
    
    def _analyze_file_dependencies(self, content: str, language: str) -> List[str]:
        """Analyze file-level dependencies"""
        dependencies = []
        
        # Extract module imports
        imports = self._parse_imports(content, language)
        dependencies.extend(imports)
        
        # Look for external API calls
        api_patterns = [
            r'fetch\([\'"]([^\'"]+)[\'"]\)',
            r'axios\.(get|post|put|delete)\([\'"]([^\'"]+)[\'"]\)',
            r'requests\.(get|post|put|delete)\([\'"]([^\'"]+)[\'"]\)'
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    dependencies.append(match[-1])
                else:
                    dependencies.append(match)
        
        return list(set(dependencies))
    
    def _calculate_complexity_metrics(self, content: str, language: str) -> Dict[str, float]:
        """Calculate code complexity metrics"""
        metrics = {
            "cyclomatic_complexity": 0,
            "lines_of_code": len(content.splitlines()),
            "comment_ratio": 0,
            "function_count": 0,
            "class_count": 0
        }
        
        # Count lines of code (excluding comments and empty lines)
        lines = content.splitlines()
        code_lines = 0
        comment_lines = 0
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                code_lines += 1
            elif line.startswith('#') or line.startswith('//'):
                comment_lines += 1
        
        metrics["lines_of_code"] = code_lines
        metrics["comment_ratio"] = comment_lines / max(len(lines), 1)
        
        # Estimate cyclomatic complexity (simplified)
        decision_points = len(re.findall(r'\bif\b|\bwhile\b|\bfor\b|\belse\b|\belif\b|\btry\b|\bexcept\b', content, re.IGNORECASE))
        metrics["cyclomatic_complexity"] = decision_points + 1
        
        return metrics
    
    def _estimate_test_coverage(self, file_path: str, content: str) -> float:
        """Estimate test coverage for a file"""
        # Look for test files
        if "test" in file_path.lower():
            return 100.0
        
        # Check if there are corresponding test files
        file_path_obj = Path(file_path)
        test_patterns = [
            file_path_obj.parent / f"test_{file_path_obj.name}",
            file_path_obj.parent / f"{file_path_obj.stem}_test.py",
            file_path_obj.parent / "tests" / file_path_obj.name
        ]
        
        for pattern in test_patterns:
            if pattern.exists():
                return 75.0  # Estimated coverage if test file exists
        
        return 0.0  # No test coverage estimated
    
    def _identify_security_issues(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Identify potential security issues"""
        issues = []
        
        # Common security patterns to check
        security_patterns = [
            (r'password\s*=\s*[\'"][^\'"]+[\'"]', "hardcoded_password", "High"),
            (r'api_key\s*=\s*[\'"][^\'"]+[\'"]', "hardcoded_api_key", "High"),
            (r'eval\(', "use_of_eval", "High"),
            (r'exec\(', "use_of_exec", "High"),
            (r'sql\s*=\s*[\'"].*\+.*[\'"]', "sql_injection", "High"),
            (r'innerHTML\s*=', "xss_vulnerability", "Medium"),
            (r'document\.write', "xss_vulnerability", "Medium")
        ]
        
        for pattern, issue_type, severity in security_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append({
                    "type": issue_type,
                    "severity": severity,
                    "line_number": content[:match.start()].count('\n') + 1,
                    "snippet": match.group()
                })
        
        return issues
    
    async def _find_dependency_file(self, dependency: str) -> Optional[str]:
        """Find the file that provides a given dependency"""
        # Simple heuristic - look for files with matching names
        for file_path in self.code_contexts.keys():
            file_name = Path(file_path).stem.lower()
            if dependency.lower().replace('.', '_') == file_name or dependency.split('.')[-1].lower() == file_name:
                return file_path
        
        return None
    
    def _update_awareness_level(self) -> None:
        """Update context awareness level based on analysis completeness"""
        level = 0
        
        # Check system context
        if self.system_context:
            level += 1
        
        # Check code contexts
        if len(self.code_contexts) > 0:
            level += 1
        
        # Check operational context
        if self.operational_context:
            level += 1
        
        # Check business context
        if self.business_context:
            level += 1
        
        # Check dependency graph
        if self.dependency_graph.number_of_nodes() > 0:
            level += 1
        
        self.context_awareness_level = min(level, self.max_awareness_level)
    
    def _context_to_dict(self, context: Any) -> Dict[str, Any]:
        """Convert context object to dictionary"""
        if context is None:
            return {}
        
        if isinstance(context, SystemContext):
            return {
                "project_root": context.project_root,
                "architecture_patterns": context.architecture_patterns,
                "frameworks": context.frameworks,
                "dependencies_count": len(context.dependencies),
                "configuration_files_count": len(context.configuration_files),
                "deployment_environment": context.deployment_environment,
                "external_services": context.external_services,
                "database_schemas_count": len(context.database_schemas),
                "api_endpoints_count": len(context.api_endpoints),
                "security_policies_count": sum(len(v) for v in context.security_policies.values())
            }
        elif isinstance(context, OperationalContext):
            return {
                "deployment_config": context.deployment_config,
                "monitoring_setup": context.monitoring_setup,
                "performance_metrics": context.performance_metrics,
                "error_rates": context.error_rates,
                "resource_usage": context.resource_usage,
                "uptime_stats": context.uptime_stats,
                "log_patterns_count": len(context.log_patterns)
            }
        elif isinstance(context, BusinessContext):
            return {
                "requirements_count": len(context.requirements),
                "constraints_count": len(context.constraints),
                "stakeholders_count": len(context.stakeholders),
                "timeline": context.timeline,
                "budget": context.budget,
                "risk_factors_count": len(context.risk_factors)
            }
        else:
            return {}
    
    async def _cache_context_analysis(self) -> None:
        """Cache context analysis results"""
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "system_context": self._context_to_dict(self.system_context),
            "code_contexts_count": len(self.code_contexts),
            "operational_context": self._context_to_dict(self.operational_context),
            "business_context": self._context_to_dict(self.business_context),
            "awareness_level": self.context_awareness_level,
            "analysis_stats": self.analysis_stats
        }
        
        self.context_cache["latest_analysis"] = cache_data
    
    async def _load_context_cache(self) -> None:
        """Load context analysis cache"""
        # Implementation for loading cached context
        pass
    
    async def _initialize_pattern_databases(self) -> None:
        """Initialize pattern recognition databases"""
        # Initialize common code patterns
        self.code_patterns = {
            "design_patterns": [
                {"name": "singleton", "indicators": ["__new__", "instance", "_instance"]},
                {"name": "factory", "indicators": ["factory", "create_", "build_"]},
                {"name": "observer", "indicators": ["observer", "subscribe", "notify"]},
                {"name": "strategy", "indicators": ["strategy", "algorithm", "context"]}
            ],
            "architecture_patterns": [
                {"name": "mvc", "indicators": ["model", "view", "controller"]},
                {"name": "repository", "indicators": ["repository", "dao", "data access"]},
                {"name": "service", "indicators": ["service", "business logic"]},
                {"name": "middleware", "indicators": ["middleware", "interceptor"]}
            ]
        }
    
    async def get_context_aware_suggestions(self, task_description: str) -> Dict[str, Any]:
        """Get context-aware suggestions for a given task"""
        if self.context_awareness_level < 3:
            return {
                "success": False,
                "message": "Insufficient context awareness. Please run project context analysis first."
            }
        
        suggestions = {
            "contextual_recommendations": [],
            "potential_issues": [],
            "optimization_opportunities": [],
            "security_considerations": [],
            "performance_implications": []
        }
        
        # Analyze task in context of project structure
        task_lower = task_description.lower()
        
        # Provide contextual recommendations
        if "database" in task_lower:
            if self.system_context and self.system_context.database_schemas:
                suggestions["contextual_recommendations"].append(
                    f"Consider existing database schemas: {list(self.system_context.database_schemas.keys())}"
                )
        
        if "api" in task_lower:
            if self.system_context and self.system_context.api_endpoints:
                suggestions["contextual_recommendations"].append(
                    f"Existing API endpoints found: {len(self.system_context.api_endpoints)}"
                )
        
        # Identify potential issues
        if "security" not in task_lower and "auth" not in task_lower:
            suggestions["potential_issues"].append(
                "Task may require security considerations not mentioned in description"
            )
        
        # Suggest optimizations
        if self.operational_context:
            if self.operational_context.performance_metrics.get("response_time", 0) > 1000:
                suggestions["optimization_opportunities"].append(
                    "Consider performance optimization - current response times are high"
                )
        
        # Security considerations
        if self.system_context and self.system_context.security_policies:
            suggestions["security_considerations"].extend(
                [f"Consider {policy_type} policies" for policy_type in self.system_context.security_policies.keys()]
            )
        
        return {
            "success": True,
            "awareness_level": self.context_awareness_level,
            "suggestions": suggestions,
            "confidence": min(self.context_awareness_level / self.max_awareness_level, 1.0)
        }
    
    async def get_dependency_analysis(self, file_path: str) -> Dict[str, Any]:
        """Get detailed dependency analysis for a specific file"""
        if file_path not in self.code_contexts:
            return {"error": f"File not found in context: {file_path}"}
        
        code_context = self.code_contexts[file_path]
        
        # Get dependencies from graph
        dependencies = list(self.dependency_graph.successors(file_path))
        dependents = list(self.dependency_graph.predecessors(file_path))
        
        # Analyze dependency impact
        impact_score = len(dependents) * 10 + len(dependencies) * 5
        
        # Identify circular dependencies
        circular_deps = []
        for dep in dependencies:
            if nx.has_path(self.dependency_graph, dep, file_path):
                circular_deps.append(dep)
        
        return {
            "success": True,
            "file_path": file_path,
            "dependencies": dependencies,
            "dependents": dependents,
            "impact_score": impact_score,
            "circular_dependencies": circular_deps,
            "complexity_metrics": code_context.complexity_metrics,
            "security_issues": code_context.security_issues
        }
    
    async def get_architecture_insights(self) -> Dict[str, Any]:
        """Get architecture-level insights"""
        if not self.system_context:
            return {"error": "System context not available"}
        
        insights = {
            "architecture_patterns": self.system_context.architecture_patterns,
            "framework_analysis": {},
            "dependency_analysis": {},
            "scalability_assessment": {},
            "maintainability_score": 0
        }
        
        # Analyze frameworks
        for framework in self.system_context.frameworks:
            insights["framework_analysis"][framework] = {
                "adoption_level": "high" if framework.lower() in ["react", "django", "fastapi"] else "medium",
                "complexity": "medium",
                "community_support": "high"
            }
        
        # Analyze dependency graph
        if self.dependency_graph.number_of_nodes() > 0:
            # Calculate graph metrics
            density = nx.density(self.dependency_graph)
            avg_degree = sum(dict(self.dependency_graph.degree()).values()) / self.dependency_graph.number_of_nodes()
            
            insights["dependency_analysis"] = {
                "total_components": self.dependency_graph.number_of_nodes(),
                "total_dependencies": self.dependency_graph.number_of_edges(),
                "density": density,
                "average_degree": avg_degree,
                "highly_coupled_components": [
                    node for node, degree in self.dependency_graph.degree() if degree > 10
                ]
            }
        
        # Assess scalability
        if self.system_context.deployment_environment == "microservices":
            insights["scalability_assessment"] = {
                "horizontal_scaling": "excellent",
                "independent_deployment": "excellent",
                "complexity": "high"
            }
        elif self.system_context.deployment_environment == "monolithic":
            insights["scalability_assessment"] = {
                "horizontal_scaling": "limited",
                "independent_deployment": "poor",
                "complexity": "medium"
            }
        
        # Calculate maintainability score
        maintainability_factors = {
            "code_organization": 0.3,
            "documentation": 0.2,
            "test_coverage": 0.2,
            "complexity": 0.3
        }
        
        # Estimate test coverage
        total_files = len(self.code_contexts)
        test_files = sum(1 for ctx in self.code_contexts.values() if ctx.test_coverage > 0)
        test_coverage_ratio = test_files / max(total_files, 1)
        
        # Estimate complexity
        avg_complexity = sum(
            ctx.complexity_metrics.get("cyclomatic_complexity", 0) 
            for ctx in self.code_contexts.values()
        ) / max(total_files, 1)
        
        complexity_score = max(0, 1 - (avg_complexity / 20))  # Normalize to 0-1
        
        # Calculate overall maintainability
        insights["maintainability_score"] = (
            maintainability_factors["code_organization"] * 0.7 +  # Assumed good organization
            maintainability_factors["documentation"] * 0.5 +    # Assumed moderate documentation
            maintainability_factors["test_coverage"] * test_coverage_ratio +
            maintainability_factors["complexity"] * complexity_score
        ) * 100
        
        return {
            "success": True,
            "insights": insights,
            "awareness_level": self.context_awareness_level
        }
    
    async def get_security_assessment(self) -> Dict[str, Any]:
        """Get comprehensive security assessment"""
        security_assessment = {
            "overall_score": 0,
            "issues_found": 0,
            "critical_issues": 0,
            "recommendations": [],
            "policy_compliance": {},
            "vulnerability_scan": {}
        }
        
        # Analyze security issues across all files
        all_issues = []
        for file_path, code_context in self.code_contexts.items():
            all_issues.extend([
                {**issue, "file": file_path} 
                for issue in code_context.security_issues
            ])
        
        security_assessment["issues_found"] = len(all_issues)
        security_assessment["critical_issues"] = len([
            issue for issue in all_issues if issue.get("severity") == "High"
        ])
        
        # Calculate security score
        max_possible_issues = len(self.code_contexts) * 2  # Assume 2 issues per file max
        security_assessment["overall_score"] = max(0, 100 - (len(all_issues) / max_possible_issues * 100))
        
        # Generate recommendations
        if security_assessment["critical_issues"] > 0:
            security_assessment["recommendations"].append(
                "Address critical security issues immediately"
            )
        
        if self.system_context and not self.system_context.security_policies.get("authentication"):
            security_assessment["recommendations"].append(
                "Implement authentication policies"
            )
        
        # Policy compliance
        if self.system_context:
            security_assessment["policy_compliance"] = {
                policy_type: len(policies) > 0
                for policy_type, policies in self.system_context.security_policies.items()
            }
        
        return {
            "success": True,
            "security_assessment": security_assessment,
            "awareness_level": self.context_awareness_level
        }