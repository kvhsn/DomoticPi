"""
InfluxDB client module for sending metrics to InfluxDB.
"""
from typing import Dict, List, Optional
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from config import InfluxDBConfig


class InfluxDBWriter:
    """Handles writing metrics to InfluxDB."""

    def __init__(self, config: InfluxDBConfig):
        self.config = config
        self.client: Optional[InfluxDBClient] = None
        self.write_api = None
        self._connect()

    def _connect(self):
        """Establish connection to InfluxDB."""
        try:
            self.client = InfluxDBClient(
                url=self.config.url,
                token=self.config.token,
                org=self.config.org,
            )
            self.write_api = self.client.write_api(
                write_options=SYNCHRONOUS
            )
            print(f"Connected to InfluxDB at {self.config.url}")
        except Exception as e:
            print(f"Error connecting to InfluxDB: {e}")
            raise

    def _create_simple_point(
        self, measurement: str, hostname: str, metrics: Dict
    ) -> Optional[Point]:
        """Create a simple InfluxDB point with host tag and fields."""
        if not metrics:
            return None
        point = Point(measurement).tag("host", hostname)
        for key, value in metrics.items():
            point = point.field(key, value)
        return point

    def _create_cpu_point(self, hostname: str, cpu_metrics: Dict) -> Optional[Point]:
        """Create InfluxDB point for CPU metrics."""
        return self._create_simple_point("cpu", hostname, cpu_metrics)

    def _create_memory_point(
        self, hostname: str, memory_metrics: Dict
    ) -> Optional[Point]:
        """Create InfluxDB point for memory metrics."""
        return self._create_simple_point("memory", hostname, memory_metrics)

    def _create_temperature_point(
        self, hostname: str, temp_metrics: Dict
    ) -> Optional[Point]:
        """Create InfluxDB point for temperature metrics."""
        return self._create_simple_point("temperature", hostname, temp_metrics)

    def _create_disk_points(
        self, hostname: str, disk_metrics_list: List[Dict]
    ) -> List[Point]:
        """Create InfluxDB points for disk metrics (one per partition)."""
        points = []
        for disk_data in disk_metrics_list:
            disk_point = (
                Point("disk")
                .tag("host", hostname)
                .tag("device", disk_data.get("device", "unknown"))
                .tag("mountpoint", disk_data.get("mountpoint", "unknown"))
            )
            for key, value in disk_data.items():
                if key not in ["device", "mountpoint"]:
                    disk_point = disk_point.field(key, value)
            points.append(disk_point)
        return points

    def _create_network_points(
        self, hostname: str, network_metrics_list: List[Dict]
    ) -> List[Point]:
        """Create InfluxDB points for network metrics (one per interface)."""
        points = []
        for net_data in network_metrics_list:
            net_point = (
                Point("network")
                .tag("host", hostname)
                .tag("interface", net_data.get("interface", "unknown"))
            )
            for key, value in net_data.items():
                if key != "interface":
                    net_point = net_point.field(key, value)
            points.append(net_point)
        return points

    def write_metrics(self, metrics: Dict, hostname: str):
        """
        Write metrics to InfluxDB.

        Args:
            metrics: Dictionary containing all collected metrics
            hostname: Hostname tag for the metrics
        """
        if not self.write_api:
            print("InfluxDB client not initialized")
            return

        points = []

        # CPU metrics
        cpu_point = self._create_cpu_point(hostname, metrics.get("cpu", {}))
        if cpu_point:
            points.append(cpu_point)

        # Memory metrics
        memory_point = self._create_memory_point(hostname, metrics.get("memory", {}))
        if memory_point:
            points.append(memory_point)

        # Temperature metrics
        temp_point = self._create_temperature_point(
            hostname, metrics.get("temperature", {})
        )
        if temp_point:
            points.append(temp_point)

        # Disk metrics (one point per partition)
        points.extend(
            self._create_disk_points(hostname, metrics.get("disk", []))
        )

        # Network metrics (one point per interface)
        points.extend(
            self._create_network_points(hostname, metrics.get("network", []))
        )

        # Write all points to InfluxDB
        try:
            self.write_api.write(
                bucket=self.config.bucket,
                org=self.config.org,
                record=points,
            )
            print(f"Successfully wrote {len(points)} data points to InfluxDB")
        except Exception as e:
            print(f"Error writing to InfluxDB: {e}")

    def close(self):
        """Close the InfluxDB connection."""
        if self.client:
            self.client.close()
            print("InfluxDB connection closed")
