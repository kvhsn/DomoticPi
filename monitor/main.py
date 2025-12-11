#!/usr/bin/env python3
"""
Main monitoring script for Raspberry Pi.
Collects system metrics and sends them to InfluxDB.
"""
import time
import signal
import sys
from config import InfluxDBConfig, MonitoringConfig
from metrics_collector import MetricsCollector
from influxdb_client import InfluxDBWriter


class MonitoringService:
    """Main monitoring service that collects and sends metrics."""

    def __init__(self):
        self.running = True
        self.influxdb_config = InfluxDBConfig()
        self.monitoring_config = MonitoringConfig()
        self.metrics_collector = MetricsCollector(self.monitoring_config)
        self.influxdb_writer = InfluxDBWriter(self.influxdb_config)

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\nReceived signal {signum}, shutting down...")
        self.running = False

    def run(self):
        """Main monitoring loop."""
        print("Starting Raspberry Pi monitoring service...")
        print(f"Collection interval: {self.monitoring_config.collection_interval} seconds")
        print(f"InfluxDB URL: {self.influxdb_config.url}")
        print(f"InfluxDB Bucket: {self.influxdb_config.bucket}")
        print(f"Hostname: {self.influxdb_config.hostname}")

        try:
            while self.running:
                # Collect metrics
                print("\nCollecting metrics...")
                metrics = self.metrics_collector.collect_all_metrics()

                # Print summary
                if "cpu" in metrics and metrics["cpu"]:
                    cpu_usage = metrics["cpu"].get("cpu_usage_percent", "N/A")
                    print(f"CPU Usage: {cpu_usage}%")

                if "memory" in metrics and metrics["memory"]:
                    memory_percent = metrics["memory"].get("memory_percent", "N/A")
                    print(f"Memory Usage: {memory_percent}%")

                if "temperature" in metrics and metrics["temperature"]:
                    cpu_temp = metrics["temperature"].get("cpu_temperature", "N/A")
                    print(f"CPU Temperature: {cpu_temp}°C")

                # Send to InfluxDB
                self.influxdb_writer.write_metrics(
                    metrics, self.influxdb_config.hostname
                )

                # Wait for next collection interval
                if self.running:
                    time.sleep(self.monitoring_config.collection_interval)

        except KeyboardInterrupt:
            print("\nMonitoring interrupted by user")
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            raise
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        print("Cleaning up...")
        self.influxdb_writer.close()
        print("Monitoring service stopped")


def main():
    """Entry point for the monitoring script."""
    service = MonitoringService()
    service.run()


if __name__ == "__main__":
    main()
