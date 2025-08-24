import asyncio
import logging
import json
import os
import psutil
import time
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import re
from enum import Enum
import statistics
from collections import defaultdict, deque
import threading
import queue
import multiprocessing

from ..config.settings import get_settings


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Metric representation"""
    name: str
    type: MetricType
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LogEntry:
    """Log entry representation"""
    timestamp: datetime
    level: LogLevel
    message: str
    source: str
    thread_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Trace:
    """Trace representation"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[float]
    status: str
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Alert:
    """Alert representation"""
    id: str
    name: str
    severity: AlertSeverity
    description: str
    condition: str
    triggered_at: datetime
    resolved_at: Optional[datetime]
    metric_name: str
    threshold: float
    current_value: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Health check representation"""
    name: str
    status: str
    duration: float
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MonitoringObservabilitySystem:
    """Comprehensive monitoring and observability system"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Metrics storage
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        self.metrics_retention = 86400  # 24 hours in seconds
        
        # Logs storage
        self.logs: deque[LogEntry] = deque(maxlen=10000)
        self.log_levels = defaultdict(int)
        
        # Traces storage
        self.traces: Dict[str, Trace] = {}
        self.active_spans: Dict[str, Trace] = {}
        
        # Alerts storage
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.alert_history: List[Alert] = []
        
        # Health checks
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_check_history: List[HealthCheck] = []
        
        # System metrics
        self.system_metrics = {
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_usage": 0,
            "network_io": {"bytes_sent": 0, "bytes_recv": 0},
            "process_count": 0,
            "thread_count": 0
        }
        
        # Application metrics
        self.application_metrics = {
            "request_count": 0,
            "error_count": 0,
            "response_time": 0,
            "active_connections": 0,
            "queue_size": 0
        }
        
        # Monitoring configuration
        self.monitoring_config = {
            "collection_interval": 10,  # seconds
            "retention_period": 86400,  # 24 hours
            "alert_check_interval": 30,  # seconds
            "health_check_interval": 60,  # seconds
            "max_log_size": 10000,
            "max_trace_age": 3600  # 1 hour
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            "cpu_usage": 80,
            "memory_usage": 85,
            "disk_usage": 90,
            "error_rate": 0.05,  # 5%
            "response_time": 5000,  # 5 seconds
            "active_connections": 1000
        }
        
        # Data processors
        self.metric_processors = self._initialize_metric_processors()
        self.log_processors = self._initialize_log_processors()
        self.trace_processors = self._initialize_trace_processors()
        
        # Exporters
        self.exporters = self._initialize_exporters()
        
        # Background tasks
        self.collection_task: Optional[asyncio.Task] = None
        self.alert_task: Optional[asyncio.Task] = None
        self.health_check_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Event queues
        self.metric_queue = asyncio.Queue()
        self.log_queue = asyncio.Queue()
        self.alert_queue = asyncio.Queue()
        
        # Statistics
        self.statistics = {
            "metrics_collected": 0,
            "logs_processed": 0,
            "traces_processed": 0,
            "alerts_triggered": 0,
            "health_checks_performed": 0,
            "export_operations": 0
        }
        
        # Dashboards
        self.dashboards = self._initialize_dashboards()
    
    async def initialize(self) -> None:
        """Initialize the monitoring system"""
        self.logger.info("Initializing Monitoring and Observability System...")
        
        # Load alert rules
        await self._load_alert_rules()
        
        # Start background tasks
        await self._start_background_tasks()
        
        # Setup default health checks
        await self._setup_default_health_checks()
        
        self.logger.info("Monitoring and Observability System initialized")
    
    async def start_monitoring(self) -> None:
        """Start monitoring activities"""
        self.logger.info("Starting monitoring activities...")
        
        # Start collection if not already running
        if not self.collection_task or self.collection_task.done():
            self.collection_task = asyncio.create_task(self._collect_metrics_loop())
        
        # Start alert checking if not already running
        if not self.alert_task or self.alert_task.done():
            self.alert_task = asyncio.create_task(self._check_alerts_loop())
        
        # Start health checks if not already running
        if not self.health_check_task or self.health_check_task.done():
            self.health_check_task = asyncio.create_task(self._perform_health_checks_loop())
        
        # Start cleanup if not already running
        if not self.cleanup_task or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_old_data_loop())
        
        self.logger.info("Monitoring activities started")
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring activities"""
        self.logger.info("Stopping monitoring activities...")
        
        # Stop background tasks
        if self.collection_task and not self.collection_task.done():
            self.collection_task.cancel()
        
        if self.alert_task and not self.alert_task.done():
            self.alert_task.cancel()
        
        if self.health_check_task and not self.health_check_task.done():
            self.health_check_task.cancel()
        
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
        
        self.logger.info("Monitoring activities stopped")
    
    async def record_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE, 
                          tags: Optional[Dict[str, str]] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record a metric"""
        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {},
            metadata=metadata or {}
        )
        
        # Add to metrics storage
        self.metrics[name].append(metric)
        
        # Add to processing queue
        await self.metric_queue.put(metric)
        
        # Update statistics
        self.statistics["metrics_collected"] += 1
    
    async def log(self, level: LogLevel, message: str, source: str, 
                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record a log entry"""
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            source=source,
            thread_id=threading.current_thread().ident,
            metadata=metadata or {}
        )
        
        # Add to logs storage
        self.logs.append(log_entry)
        self.log_levels[level] += 1
        
        # Add to processing queue
        await self.log_queue.put(log_entry)
        
        # Update statistics
        self.statistics["logs_processed"] += 1
        
        # Also log to standard logger
        log_level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        
        self.logger.log(log_level_map[level], f"[{source}] {message}")
    
    async def start_trace(self, trace_id: str, span_id: str, operation_name: str, 
                         parent_span_id: Optional[str] = None, tags: Optional[Dict[str, str]] = None) -> str:
        """Start a new trace span"""
        trace = Trace(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.now(),
            end_time=None,
            duration=None,
            status="started",
            tags=tags or {}
        )
        
        self.active_spans[span_id] = trace
        self.traces[trace_id] = trace
        
        return span_id
    
    async def finish_trace(self, span_id: str, status: str = "completed", 
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """Finish a trace span"""
        if span_id not in self.active_spans:
            return
        
        trace = self.active_spans[span_id]
        trace.end_time = datetime.now()
        trace.duration = (trace.end_time - trace.start_time).total_seconds()
        trace.status = status
        
        if metadata:
            trace.metadata.update(metadata)
        
        # Move from active to completed traces
        del self.active_spans[span_id]
        
        # Update statistics
        self.statistics["traces_processed"] += 1
    
    async def add_health_check(self, name: str, check_func: callable, 
                             interval: int = 60) -> None:
        """Add a health check"""
        self.health_checks[name] = {
            "function": check_func,
            "interval": interval,
            "last_check": None
        }
    
    async def perform_health_check(self, name: str) -> HealthCheck:
        """Perform a specific health check"""
        if name not in self.health_checks:
            raise ValueError(f"Health check not found: {name}")
        
        check_info = self.health_checks[name]
        start_time = time.time()
        
        try:
            result = check_info["function"]()
            duration = time.time() - start_time
            
            health_check = HealthCheck(
                name=name,
                status=result.get("status", "unknown"),
                duration=duration,
                timestamp=datetime.now(),
                details=result.get("details", {}),
                metadata=result.get("metadata", {})
            )
            
        except Exception as e:
            duration = time.time() - start_time
            health_check = HealthCheck(
                name=name,
                status="error",
                duration=duration,
                timestamp=datetime.now(),
                details={"error": str(e)},
                metadata={}
            )
        
        # Store in history
        self.health_check_history.append(health_check)
        
        # Update statistics
        self.statistics["health_checks_performed"] += 1
        
        return health_check
    
    async def add_alert_rule(self, rule_name: str, condition: str, threshold: float, 
                           severity: AlertSeverity, description: str, 
                           metric_name: str, tags: Optional[Dict[str, str]] = None) -> None:
        """Add an alert rule"""
        self.alert_rules[rule_name] = {
            "condition": condition,
            "threshold": threshold,
            "severity": severity,
            "description": description,
            "metric_name": metric_name,
            "tags": tags or {},
            "enabled": True,
            "last_triggered": None,
            "cooldown_period": 300  # 5 minutes
        }
    
    async def check_alerts(self) -> List[Alert]:
        """Check all alert rules and return triggered alerts"""
        triggered_alerts = []
        
        for rule_name, rule in self.alert_rules.items():
            if not rule["enabled"]:
                continue
            
            # Check cooldown period
            if rule["last_triggered"] and (datetime.now() - rule["last_triggered"]).total_seconds() < rule["cooldown_period"]:
                continue
            
            # Get current metric value
            metric_name = rule["metric_name"]
            if metric_name not in self.metrics or not self.metrics[metric_name]:
                continue
            
            current_metric = self.metrics[metric_name][-1] if self.metrics[metric_name] else None
            if not current_metric:
                continue
            
            current_value = current_metric.value
            threshold = rule["threshold"]
            
            # Check condition
            triggered = False
            if rule["condition"] == "greater_than":
                triggered = current_value > threshold
            elif rule["condition"] == "less_than":
                triggered = current_value < threshold
            elif rule["condition"] == "equals":
                triggered = current_value == threshold
            
            if triggered:
                alert = Alert(
                    id=f"alert_{rule_name}_{int(datetime.now().timestamp())}",
                    name=rule_name,
                    severity=rule["severity"],
                    description=rule["description"],
                    condition=rule["condition"],
                    triggered_at=datetime.now(),
                    resolved_at=None,
                    metric_name=metric_name,
                    threshold=threshold,
                    current_value=current_value,
                    tags=rule["tags"]
                )
                
                self.alerts[alert.id] = alert
                self.alert_history.append(alert)
                triggered_alerts.append(alert)
                
                # Update rule
                rule["last_triggered"] = datetime.now()
                
                # Add to alert queue
                await self.alert_queue.put(alert)
                
                # Update statistics
                self.statistics["alerts_triggered"] += 1
                
                # Log alert
                await self.log(
                    LogLevel.WARNING,
                    f"Alert triggered: {rule_name} - {rule['description']}",
                    "monitoring_system",
                    {"alert_id": alert.id, "current_value": current_value, "threshold": threshold}
                )
        
        return triggered_alerts
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv
            }
            
            # Process count
            process_count = len(psutil.pids())
            
            # Thread count (current process)
            current_process = psutil.Process()
            thread_count = current_process.num_threads()
            
            self.system_metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_usage": disk_usage,
                "network_io": network_io,
                "process_count": process_count,
                "thread_count": thread_count,
                "timestamp": datetime.now()
            }
            
            # Record metrics
            await self.record_metric("system_cpu_percent", cpu_percent, MetricType.GAUGE)
            await self.record_metric("system_memory_percent", memory_percent, MetricType.GAUGE)
            await self.record_metric("system_disk_usage", disk_usage, MetricType.GAUGE)
            await self.record_metric("system_process_count", process_count, MetricType.GAUGE)
            await self.record_metric("system_thread_count", thread_count, MetricType.GAUGE)
            
        except Exception as e:
            await self.log(LogLevel.ERROR, f"Error collecting system metrics: {e}", "monitoring_system")
        
        return self.system_metrics
    
    async def get_application_metrics(self) -> Dict[str, Any]:
        """Get current application metrics"""
        return self.application_metrics
    
    async def get_metrics_summary(self, metric_name: Optional[str] = None, 
                               time_range: Optional[int] = None) -> Dict[str, Any]:
        """Get metrics summary"""
        summary = {
            "total_metrics": len(self.metrics),
            "metric_names": list(self.metrics.keys()),
            "metrics_summary": {}
        }
        
        if metric_name and metric_name in self.metrics:
            metrics_data = self.metrics[metric_name]
            
            # Filter by time range if specified
            if time_range:
                cutoff_time = datetime.now() - timedelta(seconds=time_range)
                metrics_data = [m for m in metrics_data if m.timestamp >= cutoff_time]
            
            if metrics_data:
                values = [m.value for m in metrics_data]
                summary["metrics_summary"][metric_name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": statistics.mean(values),
                    "median": statistics.median(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                    "latest": values[-1] if values else None
                }
        else:
            # Summary for all metrics
            for name, metrics_data in self.metrics.items():
                if time_range:
                    cutoff_time = datetime.now() - timedelta(seconds=time_range)
                    metrics_data = [m for m in metrics_data if m.timestamp >= cutoff_time]
                
                if metrics_data:
                    values = [m.value for m in metrics_data]
                    summary["metrics_summary"][name] = {
                        "count": len(values),
                        "latest": values[-1] if values else None,
                        "avg": statistics.mean(values)
                    }
        
        return summary
    
    async def get_logs(self, level: Optional[LogLevel] = None, 
                     source: Optional[str] = None, 
                     time_range: Optional[int] = None,
                     limit: Optional[int] = None) -> List[LogEntry]:
        """Get log entries with filtering"""
        filtered_logs = list(self.logs)
        
        # Filter by level
        if level:
            filtered_logs = [log for log in filtered_logs if log.level == level]
        
        # Filter by source
        if source:
            filtered_logs = [log for log in filtered_logs if log.source == source]
        
        # Filter by time range
        if time_range:
            cutoff_time = datetime.now() - timedelta(seconds=time_range)
            filtered_logs = [log for log in filtered_logs if log.timestamp >= cutoff_time]
        
        # Limit results
        if limit:
            filtered_logs = filtered_logs[-limit:]
        
        return filtered_logs
    
    async def get_traces(self, trace_id: Optional[str] = None, 
                        operation_name: Optional[str] = None,
                        time_range: Optional[int] = None,
                        limit: Optional[int] = None) -> List[Trace]:
        """Get traces with filtering"""
        filtered_traces = list(self.traces.values())
        
        # Filter by trace_id
        if trace_id:
            filtered_traces = [trace for trace in filtered_traces if trace.trace_id == trace_id]
        
        # Filter by operation_name
        if operation_name:
            filtered_traces = [trace for trace in filtered_traces if trace.operation_name == operation_name]
        
        # Filter by time range
        if time_range:
            cutoff_time = datetime.now() - timedelta(seconds=time_range)
            filtered_traces = [trace for trace in filtered_traces if trace.start_time >= cutoff_time]
        
        # Limit results
        if limit:
            filtered_traces = filtered_traces[-limit:]
        
        return filtered_traces
    
    async def get_alerts(self, severity: Optional[AlertSeverity] = None, 
                       resolved: Optional[bool] = None,
                       time_range: Optional[int] = None,
                       limit: Optional[int] = None) -> List[Alert]:
        """Get alerts with filtering"""
        filtered_alerts = list(self.alerts.values())
        
        # Filter by severity
        if severity:
            filtered_alerts = [alert for alert in filtered_alerts if alert.severity == severity]
        
        # Filter by resolved status
        if resolved is not None:
            if resolved:
                filtered_alerts = [alert for alert in filtered_alerts if alert.resolved_at is not None]
            else:
                filtered_alerts = [alert for alert in filtered_alerts if alert.resolved_at is None]
        
        # Filter by time range
        if time_range:
            cutoff_time = datetime.now() - timedelta(seconds=time_range)
            filtered_alerts = [alert for alert in filtered_alerts if alert.triggered_at >= cutoff_time]
        
        # Limit results
        if limit:
            filtered_alerts = filtered_alerts[-limit:]
        
        return filtered_alerts
    
    async def get_health_checks(self, name: Optional[str] = None, 
                             status: Optional[str] = None,
                             time_range: Optional[int] = None,
                             limit: Optional[int] = None) -> List[HealthCheck]:
        """Get health check results with filtering"""
        filtered_checks = list(self.health_check_history)
        
        # Filter by name
        if name:
            filtered_checks = [check for check in filtered_checks if check.name == name]
        
        # Filter by status
        if status:
            filtered_checks = [check for check in filtered_checks if check.status == status]
        
        # Filter by time range
        if time_range:
            cutoff_time = datetime.now() - timedelta(seconds=time_range)
            filtered_checks = [check for check in filtered_checks if check.timestamp >= cutoff_time]
        
        # Limit results
        if limit:
            filtered_checks = filtered_checks[-limit:]
        
        return filtered_checks
    
    async def get_dashboard(self, dashboard_name: str = "default") -> Dict[str, Any]:
        """Get dashboard data"""
        if dashboard_name not in self.dashboards:
            return {"error": f"Dashboard not found: {dashboard_name}"}
        
        dashboard = self.dashboards[dashboard_name]
        
        # Get current metrics for dashboard
        dashboard_data = {
            "name": dashboard_name,
            "generated_at": datetime.now(),
            "panels": []
        }
        
        for panel in dashboard["panels"]:
            panel_data = await self._get_panel_data(panel)
            dashboard_data["panels"].append(panel_data)
        
        return dashboard_data
    
    async def _get_panel_data(self, panel: Dict[str, Any]) -> Dict[str, Any]:
        """Get data for a dashboard panel"""
        panel_type = panel["type"]
        
        if panel_type == "metric":
            metric_name = panel["metric"]
            summary = await self.get_metrics_summary(metric_name, time_range=3600)
            return {
                "type": "metric",
                "title": panel["title"],
                "data": summary.get("metrics_summary", {}).get(metric_name, {})
            }
        
        elif panel_type == "chart":
            metric_name = panel["metric"]
            if metric_name in self.metrics:
                metrics_data = self.metrics[metric_name][-100:]  # Last 100 data points
                return {
                    "type": "chart",
                    "title": panel["title"],
                    "data": [
                        {
                            "timestamp": m.timestamp.isoformat(),
                            "value": m.value
                        }
                        for m in metrics_data
                    ]
                }
        
        elif panel_type == "log":
            logs = await self.get_logs(level=LogLevel.ERROR, limit=10)
            return {
                "type": "log",
                "title": panel["title"],
                "data": [
                    {
                        "timestamp": log.timestamp.isoformat(),
                        "level": log.level.value,
                        "message": log.message,
                        "source": log.source
                    }
                    for log in logs
                ]
            }
        
        elif panel_type == "alert":
            alerts = await self.get_alerts(resolved=False, limit=5)
            return {
                "type": "alert",
                "title": panel["title"],
                "data": [
                    {
                        "id": alert.id,
                        "name": alert.name,
                        "severity": alert.severity.value,
                        "description": alert.description,
                        "triggered_at": alert.triggered_at.isoformat()
                    }
                    for alert in alerts
                ]
            }
        
        return {"type": panel_type, "title": panel["title"], "data": []}
    
    async def export_metrics(self, format_type: str = "json", 
                           metric_names: Optional[List[str]] = None,
                           time_range: Optional[int] = None) -> str:
        """Export metrics in specified format"""
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "metrics": {}
        }
        
        # Filter metrics
        metrics_to_export = metric_names if metric_names else list(self.metrics.keys())
        
        for metric_name in metrics_to_export:
            if metric_name in self.metrics:
                metrics_data = self.metrics[metric_name]
                
                # Filter by time range
                if time_range:
                    cutoff_time = datetime.now() - timedelta(seconds=time_range)
                    metrics_data = [m for m in metrics_data if m.timestamp >= cutoff_time]
                
                export_data["metrics"][metric_name] = [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "value": m.value,
                        "type": m.type.value,
                        "tags": m.tags,
                        "metadata": m.metadata
                    }
                    for m in metrics_data
                ]
        
        if format_type == "json":
            return json.dumps(export_data, indent=2)
        elif format_type == "csv":
            # Convert to CSV format
            csv_lines = ["timestamp,metric_name,value,type,tags"]
            for metric_name, metrics in export_data["metrics"].items():
                for metric in metrics:
                    tags_str = ",".join([f"{k}={v}" for k, v in metric["tags"].items()])
                    csv_lines.append(f"{metric['timestamp']},{metric_name},{metric['value']},{metric['type']},{tags_str}")
            return "\n".join(csv_lines)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    async def _collect_metrics_loop(self) -> None:
        """Background task to collect metrics"""
        while True:
            try:
                # Collect system metrics
                await self.get_system_metrics()
                
                # Collect application metrics
                await self._collect_application_metrics()
                
                # Wait for next collection
                await asyncio.sleep(self.monitoring_config["collection_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.log(LogLevel.ERROR, f"Error in metrics collection: {e}", "monitoring_system")
                await asyncio.sleep(self.monitoring_config["collection_interval"])
    
    async def _collect_application_metrics(self) -> None:
        """Collect application-specific metrics"""
        # This would be customized based on the application
        # For now, we'll simulate some application metrics
        
        # Simulate request count
        request_count = self.application_metrics["request_count"] + 1
        self.application_metrics["request_count"] = request_count
        await self.record_metric("app_request_count", request_count, MetricType.COUNTER)
        
        # Simulate response time
        response_time = 100 + (50 * (0.5 - (hash(str(datetime.now())) % 100) / 100))  # Random around 100ms
        self.application_metrics["response_time"] = response_time
        await self.record_metric("app_response_time", response_time, MetricType.GAUGE)
        
        # Simulate active connections
        active_connections = 10 + (hash(str(datetime.now())) % 20)
        self.application_metrics["active_connections"] = active_connections
        await self.record_metric("app_active_connections", active_connections, MetricType.GAUGE)
    
    async def _check_alerts_loop(self) -> None:
        """Background task to check alerts"""
        while True:
            try:
                # Check alerts
                triggered_alerts = await self.check_alerts()
                
                # Process triggered alerts
                for alert in triggered_alerts:
                    await self._process_alert(alert)
                
                # Wait for next check
                await asyncio.sleep(self.monitoring_config["alert_check_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.log(LogLevel.ERROR, f"Error in alert checking: {e}", "monitoring_system")
                await asyncio.sleep(self.monitoring_config["alert_check_interval"])
    
    async def _perform_health_checks_loop(self) -> None:
        """Background task to perform health checks"""
        while True:
            try:
                # Perform health checks
                for name, check_info in self.health_checks.items():
                    # Check if it's time to perform this health check
                    if (not check_info["last_check"] or 
                        (datetime.now() - check_info["last_check"]).total_seconds() >= check_info["interval"]):
                        
                        health_check = await self.perform_health_check(name)
                        check_info["last_check"] = datetime.now()
                        
                        # Check if health check failed
                        if health_check.status != "healthy":
                            await self.log(
                                LogLevel.WARNING,
                                f"Health check failed: {name} - {health_check.status}",
                                "monitoring_system",
                                {"duration": health_check.duration, "details": health_check.details}
                            )
                
                # Wait for next check
                await asyncio.sleep(self.monitoring_config["health_check_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.log(LogLevel.ERROR, f"Error in health checks: {e}", "monitoring_system")
                await asyncio.sleep(self.monitoring_config["health_check_interval"])
    
    async def _cleanup_old_data_loop(self) -> None:
        """Background task to clean up old data"""
        while True:
            try:
                cutoff_time = datetime.now() - timedelta(seconds=self.monitoring_config["retention_period"])
                
                # Clean up old metrics
                for metric_name in list(self.metrics.keys()):
                    self.metrics[metric_name] = [
                        m for m in self.metrics[metric_name] 
                        if m.timestamp >= cutoff_time
                    ]
                    
                    # Remove empty metric lists
                    if not self.metrics[metric_name]:
                        del self.metrics[metric_name]
                
                # Clean up old traces
                for trace_id in list(self.traces.keys()):
                    trace = self.traces[trace_id]
                    if trace.start_time < cutoff_time:
                        del self.traces[trace_id]
                
                # Clean up old health check history
                self.health_check_history = [
                    check for check in self.health_check_history 
                    if check.timestamp >= cutoff_time
                ]
                
                # Wait for next cleanup
                await asyncio.sleep(3600)  # Clean up every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.log(LogLevel.ERROR, f"Error in data cleanup: {e}", "monitoring_system")
                await asyncio.sleep(3600)
    
    async def _process_alert(self, alert: Alert) -> None:
        """Process a triggered alert"""
        # Log the alert
        await self.log(
            LogLevel.WARNING,
            f"Alert processed: {alert.name} - {alert.description}",
            "alert_processor",
            {"alert_id": alert.id, "severity": alert.severity.value}
        )
        
        # Send notifications (in a real implementation, this would send to various channels)
        await self._send_alert_notification(alert)
    
    async def _send_alert_notification(self, alert: Alert) -> None:
        """Send alert notification"""
        # In a real implementation, this would send to email, Slack, PagerDuty, etc.
        # For now, we'll just log it
        await self.log(
            LogLevel.INFO,
            f"Alert notification sent for: {alert.name}",
            "notification_system",
            {"alert_id": alert.id, "severity": alert.severity.value}
        )
    
    async def _start_background_tasks(self) -> None:
        """Start background monitoring tasks"""
        self.collection_task = asyncio.create_task(self._collect_metrics_loop())
        self.alert_task = asyncio.create_task(self._check_alerts_loop())
        self.health_check_task = asyncio.create_task(self._perform_health_checks_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_old_data_loop())
    
    async def _load_alert_rules(self) -> None:
        """Load default alert rules"""
        # System alert rules
        await self.add_alert_rule(
            "high_cpu_usage",
            "greater_than",
            self.alert_thresholds["cpu_usage"],
            AlertSeverity.HIGH,
            "High CPU usage detected",
            "system_cpu_percent"
        )
        
        await self.add_alert_rule(
            "high_memory_usage",
            "greater_than",
            self.alert_thresholds["memory_usage"],
            AlertSeverity.HIGH,
            "High memory usage detected",
            "system_memory_percent"
        )
        
        await self.add_alert_rule(
            "high_disk_usage",
            "greater_than",
            self.alert_thresholds["disk_usage"],
            AlertSeverity.CRITICAL,
            "High disk usage detected",
            "system_disk_usage"
        )
        
        # Application alert rules
        await self.add_alert_rule(
            "high_error_rate",
            "greater_than",
            self.alert_thresholds["error_rate"],
            AlertSeverity.HIGH,
            "High error rate detected",
            "app_error_rate"
        )
        
        await self.add_alert_rule(
            "slow_response_time",
            "greater_than",
            self.alert_thresholds["response_time"],
            AlertSeverity.MEDIUM,
            "Slow response time detected",
            "app_response_time"
        )
        
        await self.add_alert_rule(
            "high_active_connections",
            "greater_than",
            self.alert_thresholds["active_connections"],
            AlertSeverity.MEDIUM,
            "High active connections detected",
            "app_active_connections"
        )
    
    async def _initialize_exporters(self) -> Dict[str, Any]:
        """Initialize metric exporters"""
        return {
            "file": self._export_to_file,
            "console": self._export_to_console,
            "http": self._export_to_http,
            "database": self._export_to_database,
            "prometheus": self._export_to_prometheus,
            "json": self._export_to_json
        }
    
    async def _setup_default_health_checks(self) -> None:
        """Setup default health checks"""
        # Database health check
        await self.add_health_check("database", self._check_database_health)
        
        # API health check
        await self.add_health_check("api", self._check_api_health)
        
        # Storage health check
        await self.add_health_check("storage", self._check_storage_health)
        
        # Memory health check
        await self.add_health_check("memory", self._check_memory_health)
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        # In a real implementation, this would actually check database connectivity
        return {
            "status": "healthy",
            "details": {
                "connection_time": 0.001,
                "query_time": 0.0005
            }
        }
    
    def _check_api_health(self) -> Dict[str, Any]:
        """Check API health"""
        # In a real implementation, this would actually check API endpoints
        return {
            "status": "healthy",
            "details": {
                "response_time": 0.002,
                "status_code": 200
            }
        }
    
    def _check_storage_health(self) -> Dict[str, Any]:
        """Check storage health"""
        # In a real implementation, this would actually check storage systems
        return {
            "status": "healthy",
            "details": {
                "available_space": 1000000000,  # 1GB
                "write_speed": 1000000  # 1MB/s
            }
        }
    
    def _check_memory_health(self) -> Dict[str, Any]:
        """Check memory health"""
        try:
            memory = psutil.virtual_memory()
            return {
                "status": "healthy" if memory.percent < 90 else "warning",
                "details": {
                    "available_memory": memory.available,
                    "memory_percent": memory.percent
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "details": {"error": str(e)}
            }
    
    def _initialize_metric_processors(self) -> Dict[str, Any]:
        """Initialize metric processors"""
        return {
            "aggregator": self._aggregate_metrics,
            "anomaly_detector": self._detect_anomalies,
            "trend_analyzer": self._analyze_trends
        }
    
    def _initialize_log_processors(self) -> Dict[str, Any]:
        """Initialize log processors"""
        return {
            "parser": self._parse_logs,
            "aggregator": self._aggregate_logs,
            "anomaly_detector": self._detect_log_anomalies
        }
    
    def _initialize_trace_processors(self) -> Dict[str, Any]:
        """Initialize trace processors"""
        return {
            "aggregator": self._aggregate_traces,
            "analyzer": self._analyze_traces,
            "optimizer": self._optimize_traces
        }
    
    def _initialize_dashboards(self) -> Dict[str, Any]:
        """Initialize dashboards"""
        return {
            "default": {
                "title": "System Overview",
                "panels": [
                    {
                        "type": "metric",
                        "title": "CPU Usage",
                        "metric": "system_cpu_percent"
                    },
                    {
                        "type": "metric",
                        "title": "Memory Usage",
                        "metric": "system_memory_percent"
                    },
                    {
                        "type": "chart",
                        "title": "Response Time",
                        "metric": "app_response_time"
                    },
                    {
                        "type": "log",
                        "title": "Recent Errors",
                        "metric": "error_logs"
                    },
                    {
                        "type": "alert",
                        "title": "Active Alerts",
                        "metric": "alerts"
                    }
                ]
            },
            "application": {
                "title": "Application Metrics",
                "panels": [
                    {
                        "type": "metric",
                        "title": "Request Count",
                        "metric": "app_request_count"
                    },
                    {
                        "type": "chart",
                        "title": "Response Time Trend",
                        "metric": "app_response_time"
                    },
                    {
                        "type": "metric",
                        "title": "Active Connections",
                        "metric": "app_active_connections"
                    }
                ]
            }
        }
    
    def _aggregate_metrics(self, metrics: List[Metric]) -> Dict[str, Any]:
        """Aggregate metrics"""
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0
        }
    
    def _detect_anomalies(self, metrics: List[Metric]) -> List[Dict[str, Any]]:
        """Detect anomalies in metrics"""
        # Simplified anomaly detection
        anomalies = []
        
        if len(metrics) < 10:
            return anomalies
        
        values = [m.value for m in metrics[-100:]]  # Last 100 values
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        if std_dev > 0:
            # Check for values more than 2 standard deviations from mean
            for i, metric in enumerate(metrics[-10:]):
                z_score = abs(metric.value - mean) / std_dev
                if z_score > 2:
                    anomalies.append({
                        "timestamp": metric.timestamp,
                        "value": metric.value,
                        "z_score": z_score,
                        "severity": "high" if z_score > 3 else "medium"
                    })
        
        return anomalies
    
    def _analyze_trends(self, metrics: List[Metric]) -> Dict[str, Any]:
        """Analyze trends in metrics"""
        if len(metrics) < 2:
            return {}
        
        values = [m.value for m in metrics[-100:]]  # Last 100 values
        
        # Calculate trend using simple linear regression
        n = len(values)
        x = list(range(n))
        
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        return {
            "slope": slope,
            "trend": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
            "strength": abs(slope)
        }
    
    def _parse_logs(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """Parse log entries"""
        parsed_logs = []
        
        for log in logs:
            parsed_log = {
                "timestamp": log.timestamp,
                "level": log.level.value,
                "message": log.message,
                "source": log.source,
                "thread_id": log.thread_id
            }
            
            # Try to extract structured data from message
            try:
                # Look for JSON in log message
                if log.message.startswith("{") and log.message.endswith("}"):
                    structured_data = json.loads(log.message)
                    parsed_log["structured_data"] = structured_data
            except:
                pass
            
            parsed_logs.append(parsed_log)
        
        return parsed_logs
    
    def _aggregate_logs(self, logs: List[LogEntry]) -> Dict[str, Any]:
        """Aggregate log entries"""
        if not logs:
            return {}
        
        # Count by level
        level_counts = defaultdict(int)
        for log in logs:
            level_counts[log.level.value] += 1
        
        # Count by source
        source_counts = defaultdict(int)
        for log in logs:
            source_counts[log.source] += 1
        
        return {
            "total_logs": len(logs),
            "level_counts": dict(level_counts),
            "source_counts": dict(source_counts),
            "time_range": {
                "start": logs[0].timestamp.isoformat(),
                "end": logs[-1].timestamp.isoformat()
            }
        }
    
    def _detect_log_anomalies(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect anomalies in log entries"""
        anomalies = []
        
        # Look for sudden spikes in error logs
        error_logs = [log for log in logs if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        
        if len(error_logs) > len(logs) * 0.1:  # More than 10% errors
            anomalies.append({
                "type": "error_spike",
                "description": f"Sudden spike in error logs: {len(error_logs)} errors out of {len(logs)} logs",
                "severity": "high"
            })
        
        return anomalies
    
    def _aggregate_traces(self, traces: List[Trace]) -> Dict[str, Any]:
        """Aggregate trace data"""
        if not traces:
            return {}
        
        # Calculate statistics
        durations = [t.duration for t in traces if t.duration is not None]
        
        return {
            "total_traces": len(traces),
            "completed_traces": len([t for t in traces if t.status == "completed"]),
            "failed_traces": len([t for t in traces if t.status == "failed"]),
            "avg_duration": statistics.mean(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0
        }
    
    def _analyze_traces(self, traces: List[Trace]) -> Dict[str, Any]:
        """Analyze trace data"""
        if not traces:
            return {}
        
        # Group by operation name
        operations = defaultdict(list)
        for trace in traces:
            operations[trace.operation_name].append(trace)
        
        operation_stats = {}
        for op_name, op_traces in operations.items():
            durations = [t.duration for t in op_traces if t.duration is not None]
            operation_stats[op_name] = {
                "count": len(op_traces),
                "avg_duration": statistics.mean(durations) if durations else 0,
                "success_rate": len([t for t in op_traces if t.status == "completed"]) / len(op_traces)
            }
        
        return {
            "operations": operation_stats,
            "total_operations": len(operations)
        }
    
    def _optimize_traces(self, traces: List[Trace]) -> List[Dict[str, Any]]:
        """Optimize trace data"""
        # Identify slow operations
        optimizations = []
        
        if traces:
            avg_duration = statistics.mean([t.duration for t in traces if t.duration is not None])
            
            slow_operations = [
                {
                    "operation": trace.operation_name,
                    "duration": trace.duration,
                    "slowness_factor": trace.duration / avg_duration if avg_duration > 0 else 1
                }
                for trace in traces
                if trace.duration and trace.duration > avg_duration * 2
            ]
            
            optimizations.extend(slow_operations)
        
        return optimizations
    
    async def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary"""
        return {
            "system_metrics": self.system_metrics,
            "application_metrics": self.application_metrics,
            "statistics": self.statistics,
            "active_alerts": len([a for a in self.alerts.values() if a.resolved_at is None]),
            "health_checks": {
                name: check["last_check"] for name, check in self.health_checks.items()
            },
            "recent_logs": len([log for log in self.logs if (datetime.now() - log.timestamp).total_seconds() < 3600]),
            "uptime": (datetime.now() - min([trace.start_time for trace in self.traces.values()], default=datetime.now())).total_seconds() if self.traces else 0
        }
    
    async def _export_to_file(self, filepath: str, format_type: str = "json") -> None:
        """Export metrics to file"""
        try:
            export_data = await self.export_metrics(format_type)
            
            # Create directory if it doesn't exist
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w') as f:
                if format_type == "json":
                    json.dump(export_data, f, indent=2)
                else:
                    f.write(str(export_data))
            
            self.statistics["export_operations"] += 1
            self.logger.info(f"Metrics exported to file: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to export metrics to file: {e}")
    
    async def _export_to_console(self, format_type: str = "json") -> None:
        """Export metrics to console"""
        try:
            export_data = await self.export_metrics(format_type)
            
            if format_type == "json":
                print(json.dumps(export_data, indent=2))
            else:
                print(export_data)
            
            self.statistics["export_operations"] += 1
            self.logger.info("Metrics exported to console")
            
        except Exception as e:
            self.logger.error(f"Failed to export metrics to console: {e}")
    
    async def _export_to_http(self, url: str, format_type: str = "json", headers: Optional[Dict[str, str]] = None) -> None:
        """Export metrics to HTTP endpoint"""
        try:
            import aiohttp
            
            export_data = await self.export_metrics(format_type)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=export_data if format_type == "json" else {"data": str(export_data)},
                    headers=headers or {}
                ) as response:
                    if response.status == 200:
                        self.statistics["export_operations"] += 1
                        self.logger.info(f"Metrics exported to HTTP: {url}")
                    else:
                        self.logger.error(f"HTTP export failed with status: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Failed to export metrics to HTTP: {e}")
    
    async def _export_to_database(self, connection_string: str, table_name: str = "metrics") -> None:
        """Export metrics to database"""
        try:
            # This would typically use a database driver like asyncpg, aiomysql, etc.
            # For now, we'll simulate the export
            export_data = await self.export_metrics("json")
            
            # Simulate database insertion
            self.logger.info(f"Simulating database export to table: {table_name}")
            self.logger.debug(f"Export data: {len(export_data['metrics'])} metrics")
            
            self.statistics["export_operations"] += 1
            self.logger.info("Metrics exported to database")
            
        except Exception as e:
            self.logger.error(f"Failed to export metrics to database: {e}")
    
    async def _export_to_prometheus(self, endpoint: str = "/metrics", port: int = 9090) -> None:
        """Export metrics in Prometheus format"""
        try:
            prometheus_data = []
            
            # Convert metrics to Prometheus format
            for metric_name, metric_list in self.metrics.items():
                if metric_list:
                    latest_metric = metric_list[-1]
                    
                    # Sanitize metric name for Prometheus
                    sanitized_name = re.sub(r'[^a-zA-Z0-9_]', '_', metric_name)
                    
                    # Create Prometheus metric line
                    tags_str = ",".join([f'{k}="{v}"' for k, v in latest_metric.tags.items()])
                    metric_line = f"{sanitized_name}{f'{{{tags_str}}}' if tags_str else ''} {latest_metric.value} {int(latest_metric.timestamp.timestamp() * 1000)}"
                    prometheus_data.append(metric_line)
            
            prometheus_output = "\n".join(prometheus_data)
            
            # In a real implementation, this would expose the metrics on a Prometheus endpoint
            self.logger.info(f"Prometheus metrics prepared ({len(prometheus_data)} metrics)")
            self.logger.debug(f"Prometheus data: {prometheus_output[:200]}...")
            
            self.statistics["export_operations"] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to export metrics to Prometheus: {e}")
    
    async def _export_to_json(self, filepath: Optional[str] = None, pretty: bool = True) -> str:
        """Export metrics to JSON format"""
        try:
            export_data = await self.export_metrics("json")
            
            if pretty:
                json_output = json.dumps(export_data, indent=2)
            else:
                json_output = json.dumps(export_data)
            
            if filepath:
                with open(filepath, 'w') as f:
                    f.write(json_output)
                self.statistics["export_operations"] += 1
                self.logger.info(f"Metrics exported to JSON file: {filepath}")
            
            return json_output
            
        except Exception as e:
            self.logger.error(f"Failed to export metrics to JSON: {e}")
            return "{}"