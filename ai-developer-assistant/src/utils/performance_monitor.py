import asyncio
import logging
import time
import psutil
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """Performance alert data structure"""
    id: str
    metric_name: str
    message: str
    severity: str  # 'info', 'warning', 'error', 'critical'
    timestamp: datetime = field(default_factory=datetime.now)
    value: Optional[float] = None
    threshold: Optional[float] = None
    resolved: bool = False


class PerformanceMonitor:
    """Comprehensive performance monitoring system for AI Developer Assistant"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Performance metrics storage
        self.metrics: Dict[str, List[PerformanceMetric]] = {}
        self.max_metrics_per_key = 1000
        
        # Alerts storage
        self.alerts: List[PerformanceAlert] = []
        self.max_alerts = 100
        
        # Thresholds for alerts
        self.thresholds = {
            "cpu_usage": {"warning": 70, "critical": 90},
            "memory_usage": {"warning": 80, "critical": 95},
            "disk_usage": {"warning": 85, "critical": 95},
            "response_time": {"warning": 5.0, "critical": 10.0},
            "error_rate": {"warning": 0.1, "critical": 0.2},
            "connection_pool_usage": {"warning": 0.8, "critical": 0.95}
        }
        
        # System monitoring
        self.is_monitoring = False
        self.monitoring_interval = 5  # seconds
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Performance callbacks
        self.alert_callbacks: List[Callable] = []
        
        # Module statistics collectors
        self.module_collectors: Dict[str, Callable] = {}
        
        # Performance history
        self.performance_history: Dict[str, List[float]] = {}
        self.history_size = 100
        
        # Start time for uptime calculation
        self.start_time = time.time()
        
    async def initialize(self) -> None:
        """Initialize the performance monitor"""
        self.logger.info("Initializing performance monitor...")
        
        # Initialize metrics storage
        self.metrics = {}
        self.alerts = []
        self.performance_history = {}
        
        self.logger.info("Performance monitor initialized successfully")
    
    async def start_monitoring(self) -> None:
        """Start performance monitoring"""
        if self.is_monitoring:
            self.logger.warning("Performance monitoring is already running")
            return
        
        self.logger.info("Starting performance monitoring...")
        self.is_monitoring = True
        
        # Start background monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        self.logger.info("Performance monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        if not self.is_monitoring:
            return
        
        self.logger.info("Stopping performance monitoring...")
        self.is_monitoring = False
        
        # Cancel monitoring task
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Collect module statistics
                await self._collect_module_statistics()
                
                # Check for performance alerts
                await self._check_alerts()
                
                # Cleanup old data
                self._cleanup_old_data()
                
                # Wait for next interval
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(1)
    
    async def _collect_system_metrics(self) -> None:
        """Collect system-level performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            await self.record_metric("cpu_usage", cpu_percent, "%")
            
            # Memory usage
            memory = psutil.virtual_memory()
            await self.record_metric("memory_usage", memory.percent, "%")
            await self.record_metric("memory_available", memory.available / (1024**3), "GB")
            await self.record_metric("memory_used", memory.used / (1024**3), "GB")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            await self.record_metric("disk_usage", disk.percent, "%")
            await self.record_metric("disk_free", disk.free / (1024**3), "GB")
            await self.record_metric("disk_used", disk.used / (1024**3), "GB")
            
            # Network I/O
            network = psutil.net_io_counters()
            await self.record_metric("network_bytes_sent", network.bytes_sent, "bytes")
            await self.record_metric("network_bytes_recv", network.bytes_recv, "bytes")
            
            # Process-specific metrics
            process = psutil.Process()
            await self.record_metric("process_cpu_percent", process.cpu_percent(), "%")
            await self.record_metric("process_memory_percent", process.memory_percent(), "%")
            await self.record_metric("process_memory_rss", process.memory_info().rss / (1024**2), "MB")
            
            # Thread count
            await self.record_metric("thread_count", process.num_threads(), "count")
            
            # Uptime
            uptime = time.time() - self.start_time
            await self.record_metric("uptime", uptime, "seconds")
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    async def _collect_module_statistics(self) -> None:
        """Collect statistics from registered modules"""
        for module_name, collector in self.module_collectors.items():
            try:
                stats = await collector() if asyncio.iscoroutinefunction(collector) else collector()
                if isinstance(stats, dict):
                    for key, value in stats.items():
                        if isinstance(value, (int, float)):
                            await self.record_metric(
                                f"{module_name}_{key}", 
                                value, 
                                self._infer_unit(key)
                            )
            except Exception as e:
                self.logger.error(f"Error collecting statistics from {module_name}: {e}")
    
    async def _check_alerts(self) -> None:
        """Check for performance alerts based on thresholds"""
        current_metrics = {}
        
        # Get current metric values
        for metric_name, metric_list in self.metrics.items():
            if metric_list:
                current_metrics[metric_name] = metric_list[-1].value
        
        # Check each threshold
        for metric_name, thresholds in self.thresholds.items():
            if metric_name in current_metrics:
                value = current_metrics[metric_name]
                
                # Check critical threshold
                if "critical" in thresholds and value >= thresholds["critical"]:
                    await self._create_alert(
                        metric_name,
                        f"Critical: {metric_name} is {value:.2f} (threshold: {thresholds['critical']})",
                        "critical",
                        value,
                        thresholds["critical"]
                    )
                
                # Check warning threshold
                elif "warning" in thresholds and value >= thresholds["warning"]:
                    await self._create_alert(
                        metric_name,
                        f"Warning: {metric_name} is {value:.2f} (threshold: {thresholds['warning']})",
                        "warning",
                        value,
                        thresholds["warning"]
                    )
    
    async def _create_alert(self, metric_name: str, message: str, severity: str, 
                           value: Optional[float] = None, threshold: Optional[float] = None) -> None:
        """Create a performance alert"""
        # Check if similar alert already exists and is unresolved
        for alert in self.alerts:
            if (alert.metric_name == metric_name and 
                not alert.resolved and 
                alert.severity == severity):
                return  # Don't duplicate alerts
        
        alert = PerformanceAlert(
            id=f"alert_{int(time.time())}_{metric_name}",
            metric_name=metric_name,
            message=message,
            severity=severity,
            value=value,
            threshold=threshold
        )
        
        self.alerts.append(alert)
        
        # Keep only recent alerts
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        self.logger.warning(f"Performance alert: {message}")
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")
    
    def _cleanup_old_data(self) -> None:
        """Clean up old metrics and alerts"""
        # Clean up old metrics
        for metric_name in self.metrics:
            if len(self.metrics[metric_name]) > self.max_metrics_per_key:
                self.metrics[metric_name] = self.metrics[metric_name][-self.max_metrics_per_key:]
        
        # Clean up resolved alerts older than 1 hour
        now = datetime.now()
        self.alerts = [
            alert for alert in self.alerts 
            if not alert.resolved or (now - alert.timestamp) < timedelta(hours=1)
        ]
    
    def _infer_unit(self, metric_name: str) -> str:
        """Infer unit from metric name"""
        if "percent" in metric_name or "usage" in metric_name:
            return "%"
        elif "time" in metric_name or "response" in metric_name:
            return "seconds"
        elif "memory" in metric_name or "disk" in metric_name:
            return "bytes"
        elif "count" in metric_name or "threads" in metric_name:
            return "count"
        elif "cpu" in metric_name:
            return "%"
        else:
            return "units"
    
    async def record_metric(self, name: str, value: float, unit: str, 
                          tags: Optional[Dict[str, str]] = None) -> None:
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            tags=tags or {}
        )
        
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append(metric)
        
        # Add to performance history
        if name not in self.performance_history:
            self.performance_history[name] = []
        
        self.performance_history[name].append(value)
        if len(self.performance_history[name]) > self.history_size:
            self.performance_history[name] = self.performance_history[name][-self.history_size:]
    
    def register_module_collector(self, module_name: str, collector: Callable) -> None:
        """Register a module statistics collector"""
        self.module_collectors[module_name] = collector
        self.logger.info(f"Registered module collector: {module_name}")
    
    def register_alert_callback(self, callback: Callable) -> None:
        """Register an alert callback"""
        self.alert_callbacks.append(callback)
        self.logger.info("Registered alert callback")
    
    def set_threshold(self, metric_name: str, warning: Optional[float] = None, 
                     critical: Optional[float] = None) -> None:
        """Set alert thresholds for a metric"""
        if metric_name not in self.thresholds:
            self.thresholds[metric_name] = {}
        
        if warning is not None:
            self.thresholds[metric_name]["warning"] = warning
        if critical is not None:
            self.thresholds[metric_name]["critical"] = critical
        
        self.logger.info(f"Updated thresholds for {metric_name}: warning={warning}, critical={critical}")
    
    async def get_metrics(self, metric_name: Optional[str] = None, 
                         limit: int = 100) -> Dict[str, List[Dict[str, Any]]]:
        """Get performance metrics"""
        result = {}
        
        if metric_name:
            if metric_name in self.metrics:
                metrics = self.metrics[metric_name][-limit:]
                result[metric_name] = [
                    {
                        "value": m.value,
                        "unit": m.unit,
                        "timestamp": m.timestamp.isoformat(),
                        "tags": m.tags
                    }
                    for m in metrics
                ]
        else:
            for name, metric_list in self.metrics.items():
                metrics = metric_list[-limit:]
                result[name] = [
                    {
                        "value": m.value,
                        "unit": m.unit,
                        "timestamp": m.timestamp.isoformat(),
                        "tags": m.tags
                    }
                    for m in metrics
                ]
        
        return result
    
    async def get_current_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get current metric values"""
        result = {}
        
        for metric_name, metric_list in self.metrics.items():
            if metric_list:
                latest = metric_list[-1]
                result[metric_name] = {
                    "value": latest.value,
                    "unit": latest.unit,
                    "timestamp": latest.timestamp.isoformat(),
                    "tags": latest.tags
                }
        
        return result
    
    async def get_alerts(self, resolved: Optional[bool] = None, 
                        limit: int = 50) -> List[Dict[str, Any]]:
        """Get performance alerts"""
        alerts = self.alerts
        
        if resolved is not None:
            alerts = [alert for alert in alerts if alert.resolved == resolved]
        
        alerts = alerts[-limit:]
        
        return [
            {
                "id": alert.id,
                "metric_name": alert.metric_name,
                "message": alert.message,
                "severity": alert.severity,
                "timestamp": alert.timestamp.isoformat(),
                "value": alert.value,
                "threshold": alert.threshold,
                "resolved": alert.resolved
            }
            for alert in alerts
        ]
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve a performance alert"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                self.logger.info(f"Resolved alert: {alert_id}")
                return True
        return False
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        current_metrics = await self.get_current_metrics()
        alerts = await self.get_alerts(resolved=False)
        
        # Calculate system health score
        health_score = 100
        critical_alerts = len([a for a in alerts if a["severity"] == "critical"])
        warning_alerts = len([a for a in alerts if a["severity"] == "warning"])
        
        health_score -= (critical_alerts * 20)  # Each critical alert reduces score by 20
        health_score -= (warning_alerts * 5)    # Each warning alert reduces score by 5
        health_score = max(0, health_score)      # Minimum score is 0
        
        # Get uptime
        uptime = time.time() - self.start_time
        
        return {
            "health_score": health_score,
            "uptime_seconds": uptime,
            "uptime_formatted": self._format_uptime(uptime),
            "current_metrics": current_metrics,
            "active_alerts": len(alerts),
            "alert_summary": {
                "critical": critical_alerts,
                "warning": warning_alerts,
                "info": len([a for a in alerts if a["severity"] == "info"])
            },
            "monitoring_status": {
                "is_monitoring": self.is_monitoring,
                "monitoring_interval": self.monitoring_interval,
                "registered_modules": len(self.module_collectors),
                "registered_callbacks": len(self.alert_callbacks)
            },
            "thresholds": self.thresholds
        }
    
    def _format_uptime(self, uptime_seconds: float) -> str:
        """Format uptime in human readable format"""
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    async def get_metric_history(self, metric_name: str, limit: int = 100) -> List[float]:
        """Get historical values for a metric"""
        if metric_name in self.performance_history:
            return self.performance_history[metric_name][-limit:]
        return []
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "memory_total": psutil.virtual_memory().total,
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "disk_total": psutil.disk_usage('/').total,
                "disk_total_gb": psutil.disk_usage('/').total / (1024**3),
                "platform": psutil.os.name,
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                "python_version": psutil.sys.version
            }
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return {"error": str(e)}
    
    async def export_metrics(self, format: str = "json") -> str:
        """Export metrics in various formats"""
        if format.lower() == "json":
            data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": await self.get_metrics(),
                "alerts": await self.get_alerts(),
                "summary": await self.get_performance_summary(),
                "system_info": await self.get_system_info()
            }
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")