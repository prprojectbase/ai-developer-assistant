#!/usr/bin/env python3
"""
Performance Monitor Tests

Comprehensive tests for the performance monitoring system.
"""

import asyncio
import unittest
import tempfile
import os
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Add the src directory to the path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.performance_monitor import PerformanceMonitor, PerformanceMetric, PerformanceAlert


class TestPerformanceMonitor(unittest.TestCase):
    """Test cases for PerformanceMonitor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.monitor = PerformanceMonitor()
        
    def tearDown(self):
        """Clean up after tests"""
        if self.monitor.is_monitoring:
            asyncio.run(self.monitor.stop_monitoring())
    
    async def async_setUp(self):
        """Async set up for tests that need it"""
        await self.monitor.initialize()
        
    async def async_tear_down(self):
        """Async tear down for tests that need it"""
        await self.monitor.stop_monitoring()
    
    def test_initialization(self):
        """Test performance monitor initialization"""
        self.assertFalse(self.monitor.is_monitoring)
        self.assertEqual(len(self.monitor.metrics), 0)
        self.assertEqual(len(self.monitor.alerts), 0)
        self.assertEqual(len(self.monitor.thresholds), 6)  # Default thresholds
    
    async def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring"""
        await self.async_setUp()
        
        # Test starting monitoring
        await self.monitor.start_monitoring()
        self.assertTrue(self.monitor.is_monitoring)
        self.assertIsNotNone(self.monitor.monitoring_task)
        
        # Test stopping monitoring
        await self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.is_monitoring)
        
        await self.async_tear_down()
    
    async def test_record_metric(self):
        """Test recording performance metrics"""
        await self.async_setUp()
        
        # Record a simple metric
        await self.monitor.record_metric("test_metric", 42.0, "units")
        
        # Check metric was recorded
        self.assertIn("test_metric", self.monitor.metrics)
        self.assertEqual(len(self.monitor.metrics["test_metric"]), 1)
        
        metric = self.monitor.metrics["test_metric"][0]
        self.assertEqual(metric.name, "test_metric")
        self.assertEqual(metric.value, 42.0)
        self.assertEqual(metric.unit, "units")
        self.assertIsInstance(metric.timestamp, datetime)
        
        await self.async_tear_down()
    
    async def test_get_metrics(self):
        """Test retrieving metrics"""
        await self.async_setUp()
        
        # Record multiple metrics
        await self.monitor.record_metric("cpu_usage", 50.0, "%")
        await self.monitor.record_metric("memory_usage", 75.0, "%")
        await self.monitor.record_metric("cpu_usage", 60.0, "%")
        
        # Get all metrics
        all_metrics = await self.monitor.get_metrics()
        self.assertIn("cpu_usage", all_metrics)
        self.assertIn("memory_usage", all_metrics)
        self.assertEqual(len(all_metrics["cpu_usage"]), 2)
        self.assertEqual(len(all_metrics["memory_usage"]), 1)
        
        # Get specific metric
        cpu_metrics = await self.monitor.get_metrics("cpu_usage")
        self.assertIn("cpu_usage", cpu_metrics)
        self.assertEqual(len(cpu_metrics["cpu_usage"]), 2)
        self.assertNotIn("memory_usage", cpu_metrics)
        
        await self.async_tear_down()
    
    async def test_get_current_metrics(self):
        """Test getting current metric values"""
        await self.async_setUp()
        
        # Record metrics
        await self.monitor.record_metric("test_metric", 100.0, "units")
        await self.monitor.record_metric("test_metric", 200.0, "units")
        
        # Get current metrics
        current = await self.monitor.get_current_metrics()
        
        self.assertIn("test_metric", current)
        self.assertEqual(current["test_metric"]["value"], 200.0)  # Should be latest value
        self.assertEqual(current["test_metric"]["unit"], "units")
        
        await self.async_tear_down()
    
    async def test_alert_creation(self):
        """Test alert creation based on thresholds"""
        await self.async_setUp()
        
        # Set up alert callback
        alerts_received = []
        def alert_callback(alert):
            alerts_received.append(alert)
        
        self.monitor.register_alert_callback(alert_callback)
        
        # Record metric that exceeds warning threshold
        await self.monitor.record_metric("cpu_usage", 75.0, "%")  # Above warning (70)
        await self.monitor._check_alerts()
        
        # Check warning alert was created
        self.assertEqual(len(alerts_received), 1)
        self.assertEqual(alerts_received[0].severity, "warning")
        self.assertEqual(alerts_received[0].metric_name, "cpu_usage")
        
        # Record metric that exceeds critical threshold
        await self.monitor.record_metric("cpu_usage", 95.0, "%")  # Above critical (90)
        await self.monitor._check_alerts()
        
        # Check critical alert was created
        self.assertEqual(len(alerts_received), 2)
        self.assertEqual(alerts_received[1].severity, "critical")
        
        await self.async_tear_down()
    
    async def test_alert_resolution(self):
        """Test alert resolution"""
        await self.async_setUp()
        
        # Create an alert
        alert = PerformanceAlert(
            id="test_alert",
            metric_name="test_metric",
            message="Test alert",
            severity="warning"
        )
        self.monitor.alerts.append(alert)
        
        # Resolve the alert
        success = await self.monitor.resolve_alert("test_alert")
        self.assertTrue(success)
        self.assertTrue(alert.resolved)
        
        # Try to resolve non-existent alert
        success = await self.monitor.resolve_alert("nonexistent")
        self.assertFalse(success)
        
        await self.async_tear_down()
    
    async def test_get_alerts(self):
        """Test retrieving alerts"""
        await self.async_setUp()
        
        # Create alerts
        alert1 = PerformanceAlert(
            id="alert1",
            metric_name="cpu_usage",
            message="CPU high",
            severity="warning"
        )
        alert2 = PerformanceAlert(
            id="alert2",
            metric_name="memory_usage",
            message="Memory high",
            severity="critical",
            resolved=True
        )
        
        self.monitor.alerts.extend([alert1, alert2])
        
        # Get all alerts
        all_alerts = await self.monitor.get_alerts()
        self.assertEqual(len(all_alerts), 2)
        
        # Get unresolved alerts
        unresolved_alerts = await self.monitor.get_alerts(resolved=False)
        self.assertEqual(len(unresolved_alerts), 1)
        self.assertEqual(unresolved_alerts[0]["id"], "alert1")
        
        # Get resolved alerts
        resolved_alerts = await self.monitor.get_alerts(resolved=True)
        self.assertEqual(len(resolved_alerts), 1)
        self.assertEqual(resolved_alerts[0]["id"], "alert2")
        
        await self.async_tear_down()
    
    async def test_threshold_management(self):
        """Test threshold setting and management"""
        await self.async_setUp()
        
        # Set custom thresholds
        self.monitor.set_threshold("custom_metric", warning=50.0, critical=80.0)
        
        self.assertIn("custom_metric", self.monitor.thresholds)
        self.assertEqual(self.monitor.thresholds["custom_metric"]["warning"], 50.0)
        self.assertEqual(self.monitor.thresholds["custom_metric"]["critical"], 80.0)
        
        # Update only warning threshold
        self.monitor.set_threshold("custom_metric", warning=60.0)
        self.assertEqual(self.monitor.thresholds["custom_metric"]["warning"], 60.0)
        self.assertEqual(self.monitor.thresholds["custom_metric"]["critical"], 80.0)
        
        await self.async_tear_down()
    
    async def test_performance_summary(self):
        """Test performance summary generation"""
        await self.async_setUp()
        
        # Record some metrics
        await self.monitor.record_metric("cpu_usage", 45.0, "%")
        await self.monitor.record_metric("memory_usage", 60.0, "%")
        
        # Create an alert
        alert = PerformanceAlert(
            id="test_alert",
            metric_name="test_metric",
            message="Test alert",
            severity="warning"
        )
        self.monitor.alerts.append(alert)
        
        # Get performance summary
        summary = await self.monitor.get_performance_summary()
        
        self.assertIn("health_score", summary)
        self.assertIn("uptime_seconds", summary)
        self.assertIn("current_metrics", summary)
        self.assertIn("active_alerts", summary)
        self.assertIn("monitoring_status", summary)
        
        # Check health score calculation
        self.assertGreaterEqual(summary["health_score"], 0)
        self.assertLessEqual(summary["health_score"], 100)
        
        # Check active alerts count
        self.assertEqual(summary["active_alerts"], 1)
        
        await self.async_tear_down()
    
    async def test_module_collector_registration(self):
        """Test registering module statistics collectors"""
        await self.async_setUp()
        
        # Create a mock collector
        mock_collector = AsyncMock(return_value={
            "stat1": 100.0,
            "stat2": 200.0
        })
        
        # Register the collector
        self.monitor.register_module_collector("test_module", mock_collector)
        
        self.assertIn("test_module", self.monitor.module_collectors)
        
        # Test collection (simulate monitoring loop)
        await self.monitor._collect_module_statistics()
        
        # Check that metrics were collected
        self.assertIn("test_module_stat1", self.monitor.metrics)
        self.assertIn("test_module_stat2", self.monitor.metrics)
        
        await self.async_tear_down()
    
    async def test_metric_history(self):
        """Test metric history tracking"""
        await self.async_setUp()
        
        # Record multiple values for the same metric
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        for value in values:
            await self.monitor.record_metric("history_test", value, "units")
        
        # Get history
        history = await self.monitor.get_metric_history("history_test")
        
        self.assertEqual(len(history), len(values))
        self.assertEqual(history, values)
        
        # Get limited history
        limited_history = await self.monitor.get_metric_history("history_test", limit=3)
        self.assertEqual(len(limited_history), 3)
        self.assertEqual(limited_history, values[-3:])
        
        await self.async_tear_down()
    
    async def test_export_metrics(self):
        """Test exporting metrics to JSON"""
        await self.async_setUp()
        
        # Record some metrics and create alerts
        await self.monitor.record_metric("cpu_usage", 50.0, "%")
        await self.monitor.record_metric("memory_usage", 60.0, "%")
        
        alert = PerformanceAlert(
            id="export_test",
            metric_name="test_metric",
            message="Test alert for export",
            severity="info"
        )
        self.monitor.alerts.append(alert)
        
        # Export to JSON
        exported_data = await self.monitor.export_metrics("json")
        
        # Parse and validate JSON
        parsed = json.loads(exported_data)
        
        self.assertIn("timestamp", parsed)
        self.assertIn("metrics", parsed)
        self.assertIn("alerts", parsed)
        self.assertIn("summary", parsed)
        self.assertIn("system_info", parsed)
        
        # Check metrics are included
        self.assertIn("cpu_usage", parsed["metrics"])
        self.assertIn("memory_usage", parsed["metrics"])
        
        # Check alerts are included
        self.assertEqual(len(parsed["alerts"]), 1)
        self.assertEqual(parsed["alerts"][0]["id"], "export_test")
        
        await self.async_tear_down()
    
    async def test_cleanup_old_data(self):
        """Test cleanup of old metrics and alerts"""
        await self.async_setUp()
        
        # Set small limits for testing
        self.monitor.max_metrics_per_key = 3
        self.monitor.max_alerts = 2
        
        # Record many metrics
        for i in range(10):
            await self.monitor.record_metric("cleanup_test", float(i), "units")
        
        # Create many alerts
        for i in range(5):
            alert = PerformanceAlert(
                id=f"alert_{i}",
                metric_name="test",
                message=f"Alert {i}",
                severity="info"
            )
            self.monitor.alerts.append(alert)
        
        # Run cleanup
        self.monitor._cleanup_old_data()
        
        # Check limits are enforced
        self.assertLessEqual(len(self.monitor.metrics["cleanup_test"]), 3)
        self.assertLessEqual(len(self.monitor.alerts), 2)
        
        await self.async_tear_down()
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    async def test_system_metrics_collection(self, mock_disk, mock_memory, mock_cpu):
        """Test system metrics collection"""
        await self.async_setUp()
        
        # Mock psutil responses
        mock_cpu.return_value = 45.5
        mock_memory.return_value = Mock(percent=67.8, available=8*1024**3, used=4*1024**3)
        mock_disk.return_value = Mock(percent=82.1, free=100*1024**3, used=400*1024**3)
        
        # Collect system metrics
        await self.monitor._collect_system_metrics()
        
        # Check metrics were recorded
        self.assertIn("cpu_usage", self.monitor.metrics)
        self.assertIn("memory_usage", self.monitor.metrics)
        self.assertIn("disk_usage", self.monitor.metrics)
        
        # Check values
        self.assertEqual(self.monitor.metrics["cpu_usage"][-1].value, 45.5)
        self.assertEqual(self.monitor.metrics["memory_usage"][-1].value, 67.8)
        self.assertEqual(self.monitor.metrics["disk_usage"][-1].value, 82.1)
        
        await self.async_tear_down()
    
    def test_unit_inference(self):
        """Test unit inference from metric names"""
        self.assertEqual(self.monitor._infer_unit("cpu_percent"), "%")
        self.assertEqual(self.monitor._infer_unit("memory_usage"), "%")
        self.assertEqual(self.monitor._infer_unit("response_time"), "seconds")
        self.assertEqual(self.monitor._infer_unit("thread_count"), "count")
        self.assertEqual(self.monitor._infer_unit("unknown_metric"), "units")
    
    def test_uptime_formatting(self):
        """Test uptime formatting"""
        self.assertEqual(self.monitor._format_uptime(30), "30s")
        self.assertEqual(self.monitor._format_uptime(90), "1m 30s")
        self.assertEqual(self.monitor._format_uptime(3661), "1h 1m 1s")
        self.assertEqual(self.monitor._format_uptime(90061), "1d 1h 1m 1s")


class TestPerformanceMetric(unittest.TestCase):
    """Test cases for PerformanceMetric dataclass"""
    
    def test_metric_creation(self):
        """Test PerformanceMetric creation"""
        metric = PerformanceMetric(
            name="test_metric",
            value=42.0,
            unit="units",
            tags={"env": "test"}
        )
        
        self.assertEqual(metric.name, "test_metric")
        self.assertEqual(metric.value, 42.0)
        self.assertEqual(metric.unit, "units")
        self.assertEqual(metric.tags, {"env": "test"})
        self.assertIsInstance(metric.timestamp, datetime)


class TestPerformanceAlert(unittest.TestCase):
    """Test cases for PerformanceAlert dataclass"""
    
    def test_alert_creation(self):
        """Test PerformanceAlert creation"""
        alert = PerformanceAlert(
            id="test_alert",
            metric_name="test_metric",
            message="Test alert message",
            severity="warning",
            value=85.0,
            threshold=80.0
        )
        
        self.assertEqual(alert.id, "test_alert")
        self.assertEqual(alert.metric_name, "test_metric")
        self.assertEqual(alert.message, "Test alert message")
        self.assertEqual(alert.severity, "warning")
        self.assertEqual(alert.value, 85.0)
        self.assertEqual(alert.threshold, 80.0)
        self.assertFalse(alert.resolved)
        self.assertIsInstance(alert.timestamp, datetime)


if __name__ == '__main__':
    # Run the tests
    unittest.main()