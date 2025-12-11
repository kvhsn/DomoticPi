"""
Configuration module for Raspberry Pi monitoring system.
"""
import os
from typing import Optional


class InfluxDBConfig:
    """Configuration for InfluxDB connection."""

    def __init__(self):
        self.url: str = os.getenv("INFLUXDB_URL")
        if not self.url:
            raise ValueError("INFLUXDB_URL environment variable is required")
        self.token: Optional[str] = os.getenv("INFLUXDB_TOKEN")
        if not self.token:
            raise ValueError("INFLUXDB_TOKEN environment variable is required")
        self.org: str = os.getenv("INFLUXDB_ORG")
        if not self.org:
            raise ValueError("INFLUXDB_ORG environment variable is required")
        self.bucket: str = os.getenv("INFLUXDB_BUCKET")
        if not self.bucket:
            raise ValueError("INFLUXDB_BUCKET environment variable is required")
        self.hostname: str = os.getenv("HOSTNAME")
        if not self.hostname:
            raise ValueError("HOSTNAME environment variable is required")


class MonitoringConfig:
    """Configuration for monitoring intervals and settings."""

    def __init__(self):
        collection_interval_str = os.getenv("COLLECTION_INTERVAL")
        if not collection_interval_str:
            raise ValueError("COLLECTION_INTERVAL environment variable is required")
        self.collection_interval: int = int(collection_interval_str)
        
        self.cpu_temp_path: str = os.getenv("CPU_TEMP_PATH")
        if not self.cpu_temp_path:
            raise ValueError("CPU_TEMP_PATH environment variable is required")
        
        enable_cpu_str = os.getenv("ENABLE_CPU")
        if enable_cpu_str is None:
            raise ValueError("ENABLE_CPU environment variable is required")
        self.enable_cpu: bool = enable_cpu_str.lower() == "true"
        
        enable_memory_str = os.getenv("ENABLE_MEMORY")
        if enable_memory_str is None:
            raise ValueError("ENABLE_MEMORY environment variable is required")
        self.enable_memory: bool = enable_memory_str.lower() == "true"
        
        enable_disk_str = os.getenv("ENABLE_DISK")
        if enable_disk_str is None:
            raise ValueError("ENABLE_DISK environment variable is required")
        self.enable_disk: bool = enable_disk_str.lower() == "true"
        
        enable_temperature_str = os.getenv("ENABLE_TEMPERATURE")
        if enable_temperature_str is None:
            raise ValueError("ENABLE_TEMPERATURE environment variable is required")
        self.enable_temperature: bool = enable_temperature_str.lower() == "true"
        
        enable_network_str = os.getenv("ENABLE_NETWORK")
        if enable_network_str is None:
            raise ValueError("ENABLE_NETWORK environment variable is required")
        self.enable_network: bool = enable_network_str.lower() == "true"

