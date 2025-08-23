#!/usr/bin/env python3
"""
Performance Monitoring Example

This example demonstrates how to use the performance monitoring system
to track system and application metrics.
"""

import asyncio
import logging
import json
from datetime import datetime

# Add the src directory to the path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.main_agent import AIDeveloperAssistant
from utils.performance_monitor import PerformanceMonitor


async def main():
    """Main example function"""
    print("🚀 AI Developer Assistant - Performance Monitoring Example")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize the assistant
    assistant = AIDeveloperAssistant()
    
    try:
        # Initialize the assistant
        print("📋 Initializing AI Developer Assistant...")
        await assistant.initialize()
        
        # Start the assistant
        print("▶️  Starting AI Developer Assistant...")
        await assistant.start()
        
        # Let it run for a while to collect metrics
        print("⏳ Collecting performance metrics for 30 seconds...")
        await asyncio.sleep(30)
        
        # Get performance summary
        print("\n📊 Performance Summary:")
        print("-" * 30)
        summary = await assistant.get_system_performance()
        
        if "error" not in summary:
            # Display summary information
            print(f"Health Score: {summary['summary']['health_score']}/100")
            print(f"Uptime: {summary['summary']['uptime_formatted']}")
            print(f"Active Alerts: {summary['summary']['active_alerts']}")
            print(f"Monitoring Status: {'✅ Active' if summary['summary']['monitoring_status']['is_monitoring'] else '❌ Inactive'}")
            
            # Display current metrics
            print("\n📈 Current System Metrics:")
            print("-" * 30)
            current_metrics = summary['current_metrics']
            
            # Display key metrics
            key_metrics = ['cpu_usage', 'memory_usage', 'disk_usage', 'uptime']
            for metric in key_metrics:
                if metric in current_metrics:
                    value = current_metrics[metric]['value']
                    unit = current_metrics[metric]['unit']
                    print(f"{metric.replace('_', ' ').title()}: {value:.2f} {unit}")
            
            # Display module statistics
            print("\n🔧 Module Statistics:")
            print("-" * 30)
            module_stats = {}
            for metric_name, metric_data in current_metrics.items():
                if '_' in metric_name:
                    module, stat = metric_name.split('_', 1)
                    if module not in module_stats:
                        module_stats[module] = {}
                    module_stats[module][stat] = f"{metric_data['value']:.2f} {metric_data['unit']}"
            
            for module, stats in module_stats.items():
                print(f"{module.title()}:")
                for stat, value in stats.items():
                    print(f"  {stat.replace('_', ' ')}: {value}")
            
            # Display system information
            print("\n🖥️  System Information:")
            print("-" * 30)
            sys_info = summary['system_info']
            if "error" not in sys_info:
                print(f"CPU Cores: {sys_info.get('cpu_count', 'N/A')}")
                print(f"Memory Total: {sys_info.get('memory_total_gb', 'N/A'):.2f} GB")
                print(f"Disk Total: {sys_info.get('disk_total_gb', 'N/A'):.2f} GB")
                print(f"Platform: {sys_info.get('platform', 'N/A')}")
                print(f"Python Version: {sys_info.get('python_version', 'N/A')[:20]}...")
            
            # Display active alerts
            if summary['active_alerts']:
                print("\n🚨 Active Alerts:")
                print("-" * 30)
                for alert in summary['active_alerts']:
                    severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(alert['severity'], "⚪")
                    print(f"{severity_icon} {alert['severity'].upper()}: {alert['message']}")
            else:
                print("\n✅ No active alerts")
            
            # Export metrics to JSON
            print("\n💾 Exporting metrics...")
            export_result = await assistant.performance_monitor.export_metrics("json")
            
            # Save to file
            export_file = f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(export_file, 'w') as f:
                f.write(export_result)
            
            print(f"✅ Metrics exported to: {export_file}")
            
            # Demonstrate threshold setting
            print("\n⚙️  Demonstrating threshold configuration...")
            await assistant.set_performance_threshold("cpu_usage", warning=60.0, critical=85.0)
            await assistant.set_performance_threshold("memory_usage", warning=75.0, critical=90.0)
            print("✅ Updated CPU and Memory thresholds")
            
        else:
            print(f"❌ Error getting performance data: {summary['error']}")
        
        print("\n🎯 Performance monitoring demonstration completed!")
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.exception("Error in performance monitoring example")
    finally:
        # Stop the assistant
        print("\n🛑 Stopping AI Developer Assistant...")
        await assistant.stop()
        print("✅ Assistant stopped")


if __name__ == "__main__":
    asyncio.run(main())