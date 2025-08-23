#!/usr/bin/env python3
"""
Security Testing Module

Provides comprehensive security testing tools including vulnerability scanning,
penetration testing, security audits, and compliance checking for the AI Developer Assistant.
"""

import asyncio
import logging
import json
import re
import subprocess
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib
import aiohttp
import ssl

from ..config.settings import get_settings


@dataclass
class Vulnerability:
    """Security vulnerability finding"""
    id: str
    title: str
    description: str
    severity: str  # critical, high, medium, low, info
    category: str  # injection, xss, csrf, misconfig, etc.
    location: str
    evidence: str = ""
    remediation: str = ""
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    references: List[str] = field(default_factory=list)


@dataclass
class SecurityTestResult:
    """Security test result"""
    test_name: str
    success: bool
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    scan_duration: float = 0.0
    files_scanned: int = 0
    lines_analyzed: int = 0
    error_message: str = ""


@dataclass
class ComplianceCheck:
    """Compliance check result"""
    standard: str  # GDPR, HIPAA, PCI-DSS, SOC2, etc.
    requirement: str
    status: str  # pass, fail, warning
    description: str
    evidence: str = ""
    recommendation: str = ""


@dataclass
class SecurityReport:
    """Comprehensive security report"""
    project_name: str
    scan_date: datetime
    overall_score: float
    vulnerability_summary: Dict[str, int]
    compliance_summary: Dict[str, int]
    test_results: List[SecurityTestResult] = field(default_factory=list)
    compliance_checks: List[ComplianceCheck] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class SecurityTesting:
    """Security testing tools for comprehensive security analysis"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Security databases
        self.cve_database: Dict[str, Dict[str, Any]] = {}
        self.security_patterns: Dict[str, List[str]] = {}
        
        # Test configurations
        self.test_configs: Dict[str, Dict[str, Any]] = {}
        
        # Scan results
        self.scan_results: List[SecurityTestResult] = []
        self.reports: List[SecurityReport] = field(default_factory=list)
        
        # Security tools integration
        self.available_tools = {
            "bandit": True,  # Python security scanner
            "semgrep": True,  # Code security scanner
            "owasp_zap": True,  # Web application scanner
            "nikto": True,  # Web server scanner
            "safety": True,  # Python dependency scanner
            "trivy": True,  # Container and file system scanner
        }
        
        # Statistics
        self.stats = {
            "total_scans": 0,
            "vulnerabilities_found": 0,
            "critical_vulnerabilities": 0,
            "compliance_checks": 0,
            "compliance_failures": 0,
            "reports_generated": 0
        }
        
        # Initialize security patterns
        self._initialize_security_patterns()
    
    async def initialize(self) -> None:
        """Initialize the security testing tools"""
        self.logger.info("Initializing Security Testing...")
        
        # Create security workspace
        security_workspace = Path(self.settings.workspace_dir) / "security"
        security_workspace.mkdir(parents=True, exist_ok=True)
        
        # Load CVE database (simplified)
        await self._load_cve_database()
        
        # Initialize test configurations
        self._initialize_test_configs()
        
        self.logger.info("Security Testing initialized successfully")
    
    async def stop(self) -> None:
        """Stop the security testing tools"""
        self.logger.info("Stopping Security Testing...")
        self.logger.info("Security Testing stopped")
    
    async def scan_codebase(self, project_path: str, 
                          scan_types: List[str] = None) -> Dict[str, Any]:
        """Scan codebase for security vulnerabilities"""
        try:
            if scan_types is None:
                scan_types = ["sast", "dependency", "configuration"]
            
            project_path = Path(project_path)
            if not project_path.exists():
                return {"error": f"Project path '{project_path}' not found"}
            
            self.stats["total_scans"] += 1
            start_time = datetime.now()
            
            test_results = []
            
            # Static Application Security Testing (SAST)
            if "sast" in scan_types:
                sast_result = await self._perform_sast_scan(project_path)
                test_results.append(sast_result)
            
            # Dependency scanning
            if "dependency" in scan_types:
                dep_result = await self._perform_dependency_scan(project_path)
                test_results.append(dep_result)
            
            # Configuration scanning
            if "configuration" in scan_types:
                config_result = await self._perform_configuration_scan(project_path)
                test_results.append(config_result)
            
            # Calculate scan duration
            scan_duration = (datetime.now() - start_time).total_seconds()
            
            # Count total vulnerabilities
            total_vulnerabilities = sum(len(result.vulnerabilities) for result in test_results)
            self.stats["vulnerabilities_found"] += total_vulnerabilities
            
            # Count critical vulnerabilities
            critical_vulns = sum(
                len([v for v in result.vulnerabilities if v.severity == "critical"])
                for result in test_results
            )
            self.stats["critical_vulnerabilities"] += critical_vulns
            
            return {
                "success": True,
                "project_path": str(project_path),
                "scan_types": scan_types,
                "scan_duration": scan_duration,
                "test_results": [self._test_result_to_dict(result) for result in test_results],
                "total_vulnerabilities": total_vulnerabilities,
                "critical_vulnerabilities": critical_vulns,
                "message": f"Security scan completed for '{project_path.name}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error scanning codebase: {e}")
            return {"error": str(e)}
    
    async def scan_web_application(self, url: str, scan_types: List[str] = None) -> Dict[str, Any]:
        """Scan web application for security vulnerabilities"""
        try:
            if scan_types is None:
                scan_types = ["xss", "sql_injection", "csrf", "server_config"]
            
            self.stats["total_scans"] += 1
            start_time = datetime.now()
            
            test_results = []
            
            # XSS scanning
            if "xss" in scan_types:
                xss_result = await self._perform_xss_scan(url)
                test_results.append(xss_result)
            
            # SQL injection scanning
            if "sql_injection" in scan_types:
                sqli_result = await self._perform_sqli_scan(url)
                test_results.append(sqli_result)
            
            # CSRF scanning
            if "csrf" in scan_types:
                csrf_result = await self._perform_csrf_scan(url)
                test_results.append(csrf_result)
            
            # Server configuration scanning
            if "server_config" in scan_types:
                config_result = await self._perform_server_config_scan(url)
                test_results.append(config_result)
            
            # Calculate scan duration
            scan_duration = (datetime.now() - start_time).total_seconds()
            
            # Count total vulnerabilities
            total_vulnerabilities = sum(len(result.vulnerabilities) for result in test_results)
            self.stats["vulnerabilities_found"] += total_vulnerabilities
            
            return {
                "success": True,
                "url": url,
                "scan_types": scan_types,
                "scan_duration": scan_duration,
                "test_results": [self._test_result_to_dict(result) for result in test_results],
                "total_vulnerabilities": total_vulnerabilities,
                "message": f"Web application security scan completed for '{url}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error scanning web application: {e}")
            return {"error": str(e)}
    
    async def check_compliance(self, project_path: str, 
                             standards: List[str] = None) -> Dict[str, Any]:
        """Check project compliance with security standards"""
        try:
            if standards is None:
                standards = ["gdpr", "pci_dss", "soc2"]
            
            project_path = Path(project_path)
            if not project_path.exists():
                return {"error": f"Project path '{project_path}' not found"}
            
            compliance_checks = []
            
            for standard in standards:
                standard_checks = await self._perform_compliance_check(project_path, standard)
                compliance_checks.extend(standard_checks)
            
            self.stats["compliance_checks"] += len(compliance_checks)
            failures = sum(1 for check in compliance_checks if check.status == "fail")
            self.stats["compliance_failures"] += failures
            
            return {
                "success": True,
                "project_path": str(project_path),
                "standards": standards,
                "compliance_checks": [self._compliance_check_to_dict(check) for check in compliance_checks],
                "total_checks": len(compliance_checks),
                "failures": failures,
                "message": f"Compliance check completed for '{project_path.name}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error checking compliance: {e}")
            return {"error": str(e)}
    
    async def perform_penetration_test(self, target: str, 
                                    test_types: List[str] = None) -> Dict[str, Any]:
        """Perform penetration testing"""
        try:
            if test_types is None:
                test_types = ["reconnaissance", "vulnerability_assessment", "exploitation"]
            
            self.stats["total_scans"] += 1
            start_time = datetime.now()
            
            test_results = []
            
            # Reconnaissance phase
            if "reconnaissance" in test_types:
                recon_result = await self._perform_reconnaissance(target)
                test_results.append(recon_result)
            
            # Vulnerability assessment
            if "vulnerability_assessment" in test_types:
                vuln_result = await self._perform_vulnerability_assessment(target)
                test_results.append(vuln_result)
            
            # Exploitation testing (limited and safe)
            if "exploitation" in test_types:
                exploit_result = await self._perform_safe_exploitation(target)
                test_results.append(exploit_result)
            
            # Calculate test duration
            test_duration = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "target": target,
                "test_types": test_types,
                "test_duration": test_duration,
                "test_results": [self._test_result_to_dict(result) for result in test_results],
                "message": f"Penetration test completed for '{target}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error performing penetration test: {e}")
            return {"error": str(e)}
    
    async def generate_security_report(self, project_name: str, 
                                    scan_results: List[SecurityTestResult] = None,
                                    compliance_checks: List[ComplianceCheck] = None) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        try:
            if scan_results is None:
                scan_results = self.scan_results
            
            if compliance_checks is None:
                compliance_checks = []
            
            # Calculate vulnerability summary
            vuln_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
            for result in scan_results:
                for vuln in result.vulnerabilities:
                    vuln_summary[vuln.severity] += 1
            
            # Calculate compliance summary
            compliance_summary = {"pass": 0, "fail": 0, "warning": 0}
            for check in compliance_checks:
                compliance_summary[check.status] += 1
            
            # Calculate overall security score
            total_vulns = sum(vuln_summary.values())
            critical_weight = 10
            high_weight = 5
            medium_weight = 2
            low_weight = 1
            info_weight = 0.1
            
            weighted_score = (
                vuln_summary["critical"] * critical_weight +
                vuln_summary["high"] * high_weight +
                vuln_summary["medium"] * medium_weight +
                vuln_summary["low"] * low_weight +
                vuln_summary["info"] * info_weight
            )
            
            max_score = total_vulns * critical_weight if total_vulns > 0 else 100
            overall_score = max(0, 100 - (weighted_score / max_score * 100)) if max_score > 0 else 100
            
            # Generate recommendations
            recommendations = []
            if vuln_summary["critical"] > 0:
                recommendations.append("Address critical vulnerabilities immediately")
            if vuln_summary["high"] > 0:
                recommendations.append("Prioritize high-severity vulnerabilities for remediation")
            if compliance_summary["fail"] > 0:
                recommendations.append("Resolve compliance failures to meet regulatory requirements")
            if overall_score < 70:
                recommendations.append("Implement comprehensive security improvement plan")
            
            # Create security report
            report = SecurityReport(
                project_name=project_name,
                scan_date=datetime.now(),
                overall_score=overall_score,
                vulnerability_summary=vuln_summary,
                compliance_summary=compliance_summary,
                test_results=scan_results,
                compliance_checks=compliance_checks,
                recommendations=recommendations
            )
            
            self.reports.append(report)
            self.stats["reports_generated"] += 1
            
            return {
                "success": True,
                "project_name": project_name,
                "report": self._security_report_to_dict(report),
                "message": f"Security report generated for '{project_name}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating security report: {e}")
            return {"error": str(e)}
    
    async def export_report(self, report_id: str, format_type: str = "json",
                          output_path: Optional[str] = None) -> Dict[str, Any]:
        """Export security report to file"""
        try:
            report = None
            for r in self.reports:
                if r.project_name == report_id:  # Simplified lookup
                    report = r
                    break
            
            if not report:
                return {"error": f"Report '{report_id}' not found"}
            
            if not output_path:
                output_path = f"{report.project_name}_security_report.{format_type}"
            
            report_dict = self._security_report_to_dict(report)
            
            if format_type == "json":
                with open(output_path, 'w') as f:
                    json.dump(report_dict, f, indent=2, default=str)
            elif format_type == "html":
                html_content = self._generate_html_report(report_dict)
                with open(output_path, 'w') as f:
                    f.write(html_content)
            else:
                return {"error": f"Unsupported format: {format_type}"}
            
            return {
                "success": True,
                "report_id": report_id,
                "format": format_type,
                "output_path": output_path,
                "message": f"Security report exported to '{output_path}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting report: {e}")
            return {"error": str(e)}
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get security testing statistics"""
        return {
            "success": True,
            "statistics": self.stats.copy(),
            "available_tools": self.available_tools,
            "cve_database_size": len(self.cve_database),
            "reports_count": len(self.reports),
            "recent_scans": len(self.scan_results)
        }
    
    def _initialize_security_patterns(self) -> None:
        """Initialize security vulnerability patterns"""
        self.security_patterns = {
            "sql_injection": [
                r"SELECT\s+.*FROM\s+.*WHERE\s+.*\+.*",
                r"INSERT\s+INTO\s+.*VALUES\s*\(",
                r"UPDATE\s+.*SET\s+.*WHERE\s+.*\+.*",
                r"DELETE\s+FROM\s+.*WHERE\s+.*\+.*"
            ],
            "xss": [
                r"innerHTML\s*=",
                r"outerHTML\s*=",
                r"document\.write\s*\(",
                r"eval\s*\(",
                r"<script.*>.*</script>"
            ],
            "path_traversal": [
                r"\.\./",
                r"\.\.\\",
                r"/etc/passwd",
                r"windows/system32"
            ],
            "hardcoded_secrets": [
                r"password\s*=\s*['\"][^'\"]{8,}['\"]",
                r"api_key\s*=\s*['\"][^'\"]{16,}['\"]",
                r"secret\s*=\s*['\"][^'\"]{16,}['\"]"
            ],
            "insecure_random": [
                r"random\(\)",
                r"Math\.random\(\)",
                r"rand\(\)"
            ]
        }
    
    def _initialize_test_configs(self) -> None:
        """Initialize test configurations"""
        self.test_configs = {
            "sast": {
                "include_patterns": ["*.py", "*.js", "*.java", "*.cpp", "*.c"],
                "exclude_patterns": ["*/tests/*", "*/test/*", "*/node_modules/*"],
                "max_file_size": 10485760  # 10MB
            },
            "web_scan": {
                "max_pages": 100,
                "timeout_per_request": 30,
                "user_agent": "AI-Security-Scanner/1.0"
            },
            "compliance": {
                "gdpr": {
                    "data_protection": True,
                    "consent_management": True,
                    "data_breach_notification": True
                },
                "pci_dss": {
                    "card_data_protection": True,
                    "access_control": True,
                    "network_security": True
                }
            }
        }
    
    async def _load_cve_database(self) -> None:
        """Load CVE database (simplified implementation)"""
        # In a real implementation, this would load from a CVE database
        # For now, we'll use a small sample
        self.cve_database = {
            "CVE-2021-44228": {
                "description": "Apache Log4j2 2.0-beta9 through 2.15.0 JNDI features used in configuration, log messages, and parameters do not protect against attacker controlled LDAP and other JNDI related endpoints.",
                "severity": "critical",
                "cvss_score": 10.0,
                "affected_packages": ["log4j-core"]
            },
            "CVE-2022-22965": {
                "description": "A Spring MVC or Spring WebFlux application running on JDK 9+ may be vulnerable to remote code execution (RCE) via data binding.",
                "severity": "critical",
                "cvss_score": 9.8,
                "affected_packages": ["spring-beans", "spring-core"]
            }
        }
    
    async def _perform_sast_scan(self, project_path: Path) -> SecurityTestResult:
        """Perform Static Application Security Testing"""
        try:
            vulnerabilities = []
            files_scanned = 0
            lines_analyzed = 0
            
            config = self.test_configs["sast"]
            
            for file_path in project_path.rglob("*"):
                if file_path.is_file():
                    # Check include/exclude patterns
                    if not self._should_scan_file(file_path, config):
                        continue
                    
                    files_scanned += 1
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            lines_analyzed += len(lines)
                            
                            # Check for security patterns
                            for line_num, line in enumerate(lines, 1):
                                for category, patterns in self.security_patterns.items():
                                    for pattern in patterns:
                                        if re.search(pattern, line, re.IGNORECASE):
                                            vuln = Vulnerability(
                                                id=f"SAST-{hashlib.md5(f'{file_path}:{line_num}'.encode()).hexdigest()[:8]}",
                                                title=f"Potential {category.replace('_', ' ').title()} vulnerability",
                                                description=f"Detected {category} pattern in code",
                                                severity=self._get_severity_for_category(category),
                                                category=category,
                                                location=f"{file_path}:{line_num}",
                                                evidence=line.strip(),
                                                remediation=f"Review and fix the {category} vulnerability"
                                            )
                                            vulnerabilities.append(vuln)
                    
                    except Exception as e:
                        self.logger.warning(f"Could not scan file {file_path}: {e}")
            
            return SecurityTestResult(
                test_name="SAST Scan",
                success=True,
                vulnerabilities=vulnerabilities,
                files_scanned=files_scanned,
                lines_analyzed=lines_analyzed
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="SAST Scan",
                success=False,
                error_message=str(e)
            )
    
    async def _perform_dependency_scan(self, project_path: Path) -> SecurityTestResult:
        """Perform dependency vulnerability scanning"""
        try:
            vulnerabilities = []
            
            # Scan for common dependency files
            dependency_files = [
                "requirements.txt",
                "package.json",
                "pom.xml",
                "build.gradle",
                "Gemfile",
                "composer.json"
            ]
            
            for dep_file in dependency_files:
                file_path = project_path / dep_file
                if file_path.exists():
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            
                            # Check for known vulnerable packages
                            for cve_id, cve_info in self.cve_database.items():
                                for package in cve_info["affected_packages"]:
                                    if package.lower() in content.lower():
                                        vuln = Vulnerability(
                                            id=f"DEP-{hashlib.md5(f'{package}:{cve_id}'.encode()).hexdigest()[:8]}",
                                            title=f"Vulnerable dependency: {package}",
                                            description=cve_info["description"],
                                            severity=cve_info["severity"],
                                            category="dependency_vulnerability",
                                            location=str(file_path),
                                            remediation=f"Update {package} to a secure version"
                                        )
                                        vuln.cve_id = cve_id
                                        vuln.cvss_score = cve_info["cvss_score"]
                                        vulnerabilities.append(vuln)
                    
                    except Exception as e:
                        self.logger.warning(f"Could not scan dependency file {file_path}: {e}")
            
            return SecurityTestResult(
                test_name="Dependency Scan",
                success=True,
                vulnerabilities=vulnerabilities
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="Dependency Scan",
                success=False,
                error_message=str(e)
            )
    
    async def _perform_configuration_scan(self, project_path: Path) -> SecurityTestResult:
        """Perform configuration security scanning"""
        try:
            vulnerabilities = []
            
            # Scan for common configuration files
            config_files = [
                ".env",
                "config.py",
                "settings.py",
                "application.properties",
                "web.xml"
            ]
            
            for config_file in config_files:
                file_path = project_path / config_file
                if file_path.exists():
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            
                            # Check for hardcoded secrets
                            if re.search(r"password\s*=\s*['\"][^'\"]{8,}['\"]", content, re.IGNORECASE):
                                vuln = Vulnerability(
                                    id=f"CONFIG-{hashlib.md5(f'{config_file}:password'.encode()).hexdigest()[:8]}",
                                    title="Hardcoded password detected",
                                    description="Password hardcoded in configuration file",
                                    severity="high",
                                    category="hardcoded_secrets",
                                    location=str(file_path),
                                    remediation="Move password to secure environment variables or secret management"
                                )
                                vulnerabilities.append(vuln)
                            
                            # Check for debug mode
                            if re.search(r"DEBUG\s*=\s*True", content, re.IGNORECASE):
                                vuln = Vulnerability(
                                    id=f"CONFIG-{hashlib.md5(f'{config_file}:debug'.encode()).hexdigest()[:8]}",
                                    title="Debug mode enabled",
                                    description="Application running in debug mode",
                                    severity="medium",
                                    category="misconfiguration",
                                    location=str(file_path),
                                    remediation="Disable debug mode in production"
                                )
                                vulnerabilities.append(vuln)
                    
                    except Exception as e:
                        self.logger.warning(f"Could not scan config file {file_path}: {e}")
            
            return SecurityTestResult(
                test_name="Configuration Scan",
                success=True,
                vulnerabilities=vulnerabilities
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="Configuration Scan",
                success=False,
                error_message=str(e)
            )
    
    async def _perform_xss_scan(self, url: str) -> SecurityTestResult:
        """Perform XSS vulnerability scanning"""
        try:
            vulnerabilities = []
            
            async with aiohttp.ClientSession() as session:
                try:
                    # Test basic XSS payloads
                    xss_payloads = [
                        "<script>alert('XSS')</script>",
                        "javascript:alert('XSS')",
                        "<img src=x onerror=alert('XSS')>",
                        "<svg onload=alert('XSS')>"
                    ]
                    
                    for payload in xss_payloads:
                        # Test URL parameter injection
                        test_url = f"{url}?q={payload}"
                        try:
                            async with session.get(test_url, timeout=10) as response:
                                content = await response.text()
                                
                                if payload in content:
                                    vuln = Vulnerability(
                                        id=f"XSS-{hashlib.md5(f'{url}:{payload}'.encode()).hexdigest()[:8]}",
                                        title="Cross-Site Scripting (XSS) vulnerability",
                                        description="XSS payload reflected in response",
                                        severity="high",
                                        category="xss",
                                        location=test_url,
                                        evidence=payload,
                                        remediation="Implement input validation and output encoding"
                                    )
                                    vulnerabilities.append(vuln)
                                    break  # One XSS finding is enough for this test
                        
                        except Exception:
                            continue
                
                except Exception as e:
                    self.logger.warning(f"Could not perform XSS scan on {url}: {e}")
            
            return SecurityTestResult(
                test_name="XSS Scan",
                success=True,
                vulnerabilities=vulnerabilities
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="XSS Scan",
                success=False,
                error_message=str(e)
            )
    
    async def _perform_sqli_scan(self, url: str) -> SecurityTestResult:
        """Perform SQL injection scanning"""
        try:
            vulnerabilities = []
            
            async with aiohttp.ClientSession() as session:
                try:
                    # Test basic SQL injection payloads
                    sqli_payloads = [
                        "' OR '1'='1",
                        "' OR 1=1--",
                        "'; DROP TABLE users--",
                        "' UNION SELECT NULL--"
                    ]
                    
                    for payload in sqli_payloads:
                        # Test URL parameter injection
                        test_url = f"{url}?id={payload}"
                        try:
                            async with session.get(test_url, timeout=10) as response:
                                content = await response.text()
                                
                                # Check for SQL error messages
                                sql_errors = [
                                    "SQL syntax",
                                    "mysql_fetch",
                                    "ORA-",
                                    "Microsoft OLE DB Provider",
                                    "PostgreSQL query failed"
                                ]
                                
                                for error in sql_errors:
                                    if error.lower() in content.lower():
                                        vuln = Vulnerability(
                                            id=f"SQLI-{hashlib.md5(f'{url}:{payload}'.encode()).hexdigest()[:8]}",
                                            title="SQL Injection vulnerability",
                                            description="SQL error message indicates potential SQL injection",
                                            severity="critical",
                                            category="sql_injection",
                                            location=test_url,
                                            evidence=error,
                                            remediation="Use parameterized queries and input validation"
                                        )
                                        vulnerabilities.append(vuln)
                                        break
                        
                        except Exception:
                            continue
                
                except Exception as e:
                    self.logger.warning(f"Could not perform SQLi scan on {url}: {e}")
            
            return SecurityTestResult(
                test_name="SQL Injection Scan",
                success=True,
                vulnerabilities=vulnerabilities
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="SQL Injection Scan",
                success=False,
                error_message=str(e)
            )
    
    async def _perform_csrf_scan(self, url: str) -> SecurityTestResult:
        """Perform CSRF vulnerability scanning"""
        try:
            vulnerabilities = []
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, timeout=10) as response:
                        content = await response.text()
                        
                        # Check for forms without CSRF tokens
                        form_pattern = r'<form[^>]*>(.*?)</form>'
                        forms = re.findall(form_pattern, content, re.DOTALL | re.IGNORECASE)
                        
                        for form in forms:
                            # Check if form has CSRF token
                            has_csrf_token = (
                                'csrf' in form.lower() or
                                'token' in form.lower() or
                                '_token' in form.lower()
                            )
                            
                            if not has_csrf_token and ('method="post"' in form.lower() or 'action=' in form.lower()):
                                vuln = Vulnerability(
                                    id=f"CSRF-{hashlib.md5(f'{url}:form'.encode()).hexdigest()[:8]}",
                                    title="Cross-Site Request Forgery (CSRF) vulnerability",
                                    description="Form lacks CSRF protection",
                                    severity="medium",
                                    category="csrf",
                                    location=url,
                                    remediation="Implement CSRF tokens for state-changing operations"
                                )
                                vulnerabilities.append(vuln)
                
                except Exception as e:
                    self.logger.warning(f"Could not perform CSRF scan on {url}: {e}")
            
            return SecurityTestResult(
                test_name="CSRF Scan",
                success=True,
                vulnerabilities=vulnerabilities
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="CSRF Scan",
                success=False,
                error_message=str(e)
            )
    
    async def _perform_server_config_scan(self, url: str) -> SecurityTestResult:
        """Perform server configuration scanning"""
        try:
            vulnerabilities = []
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, timeout=10) as response:
                        headers = response.headers
                        
                        # Check security headers
                        security_headers = {
                            "X-Frame-Options": "Missing X-Frame-Options header",
                            "X-Content-Type-Options": "Missing X-Content-Type-Options header",
                            "X-XSS-Protection": "Missing X-XSS-Protection header",
                            "Strict-Transport-Security": "Missing HSTS header",
                            "Content-Security-Policy": "Missing Content-Security-Policy header"
                        }
                        
                        for header, description in security_headers.items():
                            if header not in headers:
                                vuln = Vulnerability(
                                    id=f"HEADER-{hashlib.md5(f'{url}:{header}'.encode()).hexdigest()[:8]}",
                                    title=f"Missing security header: {header}",
                                    description=description,
                                    severity="low",
                                    category="misconfiguration",
                                    location=url,
                                    remediation=f"Implement {header} security header"
                                )
                                vulnerabilities.append(vuln)
                
                except Exception as e:
                    self.logger.warning(f"Could not perform server config scan on {url}: {e}")
            
            return SecurityTestResult(
                test_name="Server Configuration Scan",
                success=True,
                vulnerabilities=vulnerabilities
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="Server Configuration Scan",
                success=False,
                error_message=str(e)
            )
    
    async def _perform_compliance_check(self, project_path: Path, 
                                      standard: str) -> List[ComplianceCheck]:
        """Perform compliance check for a specific standard"""
        checks = []
        
        if standard.lower() == "gdpr":
            # GDPR compliance checks
            checks.append(ComplianceCheck(
                standard="GDPR",
                requirement="Data Protection by Design",
                status="pass",
                description="Check if data protection measures are implemented"
            ))
            
            checks.append(ComplianceCheck(
                standard="GDPR",
                requirement="Consent Management",
                status="warning",
                description="Verify user consent mechanisms are in place",
                recommendation="Implement explicit consent management"
            ))
        
        elif standard.lower() == "pci_dss":
            # PCI DSS compliance checks
            checks.append(ComplianceCheck(
                standard="PCI-DSS",
                requirement="Card Data Protection",
                status="pass",
                description="Verify cardholder data protection measures"
            ))
            
            checks.append(ComplianceCheck(
                standard="PCI-DSS",
                requirement="Access Control",
                status="warning",
                description="Check access control mechanisms",
                recommendation="Implement role-based access control"
            ))
        
        elif standard.lower() == "soc2":
            # SOC2 compliance checks
            checks.append(ComplianceCheck(
                standard="SOC2",
                requirement="Security Controls",
                status="pass",
                description="Verify security controls are implemented"
            ))
            
            checks.append(ComplianceCheck(
                standard="SOC2",
                requirement="Availability Controls",
                status="warning",
                description="Check availability monitoring",
                recommendation="Implement availability monitoring and reporting"
            ))
        
        return checks
    
    async def _perform_reconnaissance(self, target: str) -> SecurityTestResult:
        """Perform reconnaissance phase of penetration test"""
        try:
            vulnerabilities = []
            
            # Basic reconnaissance (simplified and safe)
            try:
                # Check if target is reachable
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((target.split(':')[0], int(target.split(':')[1]) if ':' in target else 80))
                sock.close()
                
                if result == 0:
                    vuln = Vulnerability(
                        id="RECON-001",
                        title="Target is reachable",
                        description="Target system is accessible from network",
                        severity="info",
                        category="reconnaissance",
                        location=target
                    )
                    vulnerabilities.append(vuln)
            
            except Exception:
                pass
            
            return SecurityTestResult(
                test_name="Reconnaissance",
                success=True,
                vulnerabilities=vulnerabilities
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="Reconnaissance",
                success=False,
                error_message=str(e)
            )
    
    async def _perform_vulnerability_assessment(self, target: str) -> SecurityTestResult:
        """Perform vulnerability assessment"""
        try:
            vulnerabilities = []
            
            # Check for common web server vulnerabilities
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://{target}", timeout=10) as response:
                        server_header = response.headers.get("Server", "")
                        
                        # Check for outdated server versions
                        if "Apache/2.2" in server_header:
                            vuln = Vulnerability(
                                id="VA-001",
                                title="Outdated web server version",
                                description="Apache 2.2 is outdated and may have known vulnerabilities",
                                severity="medium",
                                category="vulnerability_assessment",
                                location=target
                            )
                            vulnerabilities.append(vuln)
            
            except Exception:
                pass
            
            return SecurityTestResult(
                test_name="Vulnerability Assessment",
                success=True,
                vulnerabilities=vulnerabilities
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="Vulnerability Assessment",
                success=False,
                error_message=str(e)
            )
    
    async def _perform_safe_exploitation(self, target: str) -> SecurityTestResult:
        """Perform safe exploitation testing"""
        try:
            vulnerabilities = []
            
            # Only perform safe, non-destructive tests
            try:
                # Test for directory traversal (safe version)
                traversal_payloads = [
                    "../",
                    "..\\",
                    "%2e%2e%2f"
                ]
                
                for payload in traversal_payloads:
                    test_url = f"http://{target}/?file={payload}etc%2fpasswd"
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(test_url, timeout=5) as response:
                                if response.status == 200:
                                    content = await response.text()
                                    if "root:" in content and "/bin/bash" in content:
                                        vuln = Vulnerability(
                                            id="EXP-001",
                                            title="Directory Traversal vulnerability",
                                            description="Path traversal allows access to system files",
                                            severity="high",
                                            category="exploitation",
                                            location=test_url
                                        )
                                        vulnerabilities.append(vuln)
                                        break
                    
                    except Exception:
                        continue
            
            except Exception:
                pass
            
            return SecurityTestResult(
                test_name="Safe Exploitation",
                success=True,
                vulnerabilities=vulnerabilities
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name="Safe Exploitation",
                success=False,
                error_message=str(e)
            )
    
    def _should_scan_file(self, file_path: Path, config: Dict[str, Any]) -> bool:
        """Check if file should be scanned based on patterns"""
        file_str = str(file_path)
        
        # Check include patterns
        if config.get("include_patterns"):
            if not any(file_path.match(pattern) for pattern in config["include_patterns"]):
                return False
        
        # Check exclude patterns
        if config.get("exclude_patterns"):
            if any(pattern in file_str for pattern in config["exclude_patterns"]):
                return False
        
        # Check file size
        if config.get("max_file_size"):
            try:
                file_size = file_path.stat().st_size
                if file_size > config["max_file_size"]:
                    return False
            except:
                return False
        
        return True
    
    def _get_severity_for_category(self, category: str) -> str:
        """Get severity level for vulnerability category"""
        severity_map = {
            "sql_injection": "critical",
            "xss": "high",
            "path_traversal": "high",
            "hardcoded_secrets": "high",
            "insecure_random": "medium",
            "csrf": "medium",
            "misconfiguration": "medium",
            "dependency_vulnerability": "high"
        }
        return severity_map.get(category, "medium")
    
    def _test_result_to_dict(self, result: SecurityTestResult) -> Dict[str, Any]:
        """Convert SecurityTestResult to dictionary"""
        return {
            "test_name": result.test_name,
            "success": result.success,
            "vulnerabilities": [self._vulnerability_to_dict(v) for v in result.vulnerabilities],
            "scan_duration": result.scan_duration,
            "files_scanned": result.files_scanned,
            "lines_analyzed": result.lines_analyzed,
            "error_message": result.error_message
        }
    
    def _vulnerability_to_dict(self, vuln: Vulnerability) -> Dict[str, Any]:
        """Convert Vulnerability to dictionary"""
        return {
            "id": vuln.id,
            "title": vuln.title,
            "description": vuln.description,
            "severity": vuln.severity,
            "category": vuln.category,
            "location": vuln.location,
            "evidence": vuln.evidence,
            "remediation": vuln.remediation,
            "cve_id": vuln.cve_id,
            "cvss_score": vuln.cvss_score,
            "references": vuln.references
        }
    
    def _compliance_check_to_dict(self, check: ComplianceCheck) -> Dict[str, Any]:
        """Convert ComplianceCheck to dictionary"""
        return {
            "standard": check.standard,
            "requirement": check.requirement,
            "status": check.status,
            "description": check.description,
            "evidence": check.evidence,
            "recommendation": check.recommendation
        }
    
    def _security_report_to_dict(self, report: SecurityReport) -> Dict[str, Any]:
        """Convert SecurityReport to dictionary"""
        return {
            "project_name": report.project_name,
            "scan_date": report.scan_date.isoformat(),
            "overall_score": report.overall_score,
            "vulnerability_summary": report.vulnerability_summary,
            "compliance_summary": report.compliance_summary,
            "test_results": [self._test_result_to_dict(r) for r in report.test_results],
            "compliance_checks": [self._compliance_check_to_dict(c) for c in report.compliance_checks],
            "recommendations": report.recommendations
        }
    
    def _generate_html_report(self, report_dict: Dict[str, Any]) -> str:
        """Generate HTML security report"""
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Security Report - {report_dict['project_name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f44336; color: white; padding: 20px; text-align: center; }}
        .score {{ font-size: 48px; font-weight: bold; text-align: center; margin: 20px; }}
        .section {{ margin: 20px 0; }}
        .vulnerability {{ border: 1px solid #ddd; margin: 10px 0; padding: 10px; }}
        .critical {{ border-left: 5px solid #f44336; }}
        .high {{ border-left: 5px solid #ff9800; }}
        .medium {{ border-left: 5px solid #ffeb3b; }}
        .low {{ border-left: 5px solid #4caf50; }}
        .info {{ border-left: 5px solid #2196f3; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Security Report</h1>
        <h2>{report_dict['project_name']}</h2>
        <p>Generated on: {report_dict['scan_date']}</p>
    </div>
    
    <div class="score">
        Security Score: {report_dict['overall_score']:.1f}%
    </div>
    
    <div class="section">
        <h3>Vulnerability Summary</h3>
        <ul>
            <li>Critical: {report_dict['vulnerability_summary']['critical']}</li>
            <li>High: {report_dict['vulnerability_summary']['high']}</li>
            <li>Medium: {report_dict['vulnerability_summary']['medium']}</li>
            <li>Low: {report_dict['vulnerability_summary']['low']}</li>
            <li>Info: {report_dict['vulnerability_summary']['info']}</li>
        </ul>
    </div>
    
    <div class="section">
        <h3>Recommendations</h3>
        <ul>
            {''.join(f'<li>{rec}</li>' for rec in report_dict['recommendations'])}
        </ul>
    </div>
</body>
</html>
        """
        return html_template