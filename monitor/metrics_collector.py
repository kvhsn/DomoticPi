"""
Metrics collector module for Raspberry Pi system monitoring.
Collects CPU, memory, disk, temperature, and network metrics.
"""
import os
import psutil
from typing import Dict, List, Optional
from config import MonitoringConfig

# Configure psutil to use host paths when running in Docker
HOST_PROC = os.getenv("HOST_PROC", "/proc")
HOST_SYS = os.getenv("HOST_SYS", "/sys")


class MetricsCollector:
    """Collects system metrics from Raspberry Pi."""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        # Configure psutil to use host paths if running in Docker
        if HOST_PROC != "/proc":
            psutil.PROCFS_PATH = HOST_PROC
        if HOST_SYS != "/sys":
            # Note: psutil doesn't directly support HOST_SYS, but we handle it in get_cpu_temperature
            pass

    def get_cpu_temperature(self) -> Optional[float]:
        """
        Get CPU temperature from Raspberry Pi thermal zone.

        Returns:
            CPU temperature in Celsius, or None if unavailable.
        """
        if not self.config.enable_temperature:
            return None

        try:
            # Try configured path first, then try with HOST_SYS prefix for Docker
            temp_paths = [
                self.config.cpu_temp_path,
                os.path.join(HOST_SYS, "class/thermal/thermal_zone0/temp"),
            ]

            for temp_path in temp_paths:
                if os.path.exists(temp_path):
                    with open(temp_path, "r") as f:
                        temp = int(f.read().strip()) / 1000.0
                        return temp
        except (IOError, ValueError) as e:
            print(f"Error reading CPU temperature: {e}")
        return None

    def get_cpu_metrics(self) -> Dict[str, float]:
        """
        Get CPU usage metrics.

        Returns:
            Dictionary with CPU metrics (usage_percent, per_cpu_percent).
        """
        if not self.config.enable_cpu:
            return {}

        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            per_cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            metrics = {
                "cpu_usage_percent": cpu_percent,
                "cpu_count": float(cpu_count),
            }

            if cpu_freq:
                metrics["cpu_freq_current"] = cpu_freq.current
                if cpu_freq.min:
                    metrics["cpu_freq_min"] = cpu_freq.min
                if cpu_freq.max:
                    metrics["cpu_freq_max"] = cpu_freq.max

            # Add per-core CPU usage
            for idx, core_usage in enumerate(per_cpu_percent):
                metrics[f"cpu_core_{idx}_usage"] = core_usage

            return metrics
        except Exception as e:
            print(f"Error collecting CPU metrics: {e}")
            return {}

    def get_memory_metrics(self) -> Dict[str, float]:
        """
        Get memory usage metrics.

        Returns:
            Dictionary with memory metrics (total, used, free, percent).
        """
        if not self.config.enable_memory:
            return {}

        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            metrics = {
                "memory_total": float(memory.total),
                "memory_available": float(memory.available),
                "memory_used": float(memory.used),
                "memory_free": float(memory.free),
                "memory_percent": memory.percent,
            }

            if self.config.enable_memory:
                metrics.update(
                    {
                        "swap_total": float(swap.total),
                        "swap_used": float(swap.used),
                        "swap_free": float(swap.free),
                        "swap_percent": swap.percent,
                    }
                )

            return metrics
        except Exception as e:
            print(f"Error collecting memory metrics: {e}")
            return {}

    def get_disk_metrics(self) -> List[Dict[str, float]]:
        """
        Get disk usage metrics for all mounted partitions.

        Returns:
            List of dictionaries with disk metrics per partition.
        """
        if not self.config.enable_disk:
            return []

        disk_metrics = []
        try:
            partitions = psutil.disk_partitions()
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_metrics.append(
                        {
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "disk_total": float(usage.total),
                            "disk_used": float(usage.used),
                            "disk_free": float(usage.free),
                            "disk_percent": usage.percent,
                        }
                    )
                except PermissionError:
                    # Skip partitions we don't have permission to access
                    continue
        except Exception as e:
            print(f"Error collecting disk metrics: {e}")

        return disk_metrics

    def get_network_metrics(self) -> List[Dict[str, float]]:
        """
        Get network I/O metrics for all network interfaces.

        Returns:
            List of dictionaries with network metrics per interface.
        """
        if not self.config.enable_network:
            return []

        network_metrics = []
        try:
            net_io = psutil.net_io_counters(pernic=True)
            for interface, stats in net_io.items():
                network_metrics.append(
                    {
                        "interface": interface,
                        "bytes_sent": float(stats.bytes_sent),
                        "bytes_recv": float(stats.bytes_recv),
                        "packets_sent": float(stats.packets_sent),
                        "packets_recv": float(stats.packets_recv),
                        "errin": float(stats.errin),
                        "errout": float(stats.errout),
                        "dropin": float(stats.dropin),
                        "dropout": float(stats.dropout),
                    }
                )
        except Exception as e:
            print(f"Error collecting network metrics: {e}")

        return network_metrics

    def collect_all_metrics(self) -> Dict:
        """
        Collect all available system metrics.

        Returns:
            Dictionary containing all collected metrics organized by category.
        """
        metrics = {
            "cpu": self.get_cpu_metrics(),
            "memory": self.get_memory_metrics(),
            "disk": self.get_disk_metrics(),
            "network": self.get_network_metrics(),
        }

        cpu_temp = self.get_cpu_temperature()
        if cpu_temp is not None:
            metrics["temperature"] = {"cpu_temperature": cpu_temp}

        return metrics
