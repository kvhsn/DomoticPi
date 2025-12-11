# Raspberry Pi Monitoring Scripts

Python scripts for collecting system metrics from Raspberry Pi and sending them to InfluxDB for visualization in Grafana.

## Overview

This monitoring system collects the following metrics from your Raspberry Pi:

- **CPU Metrics**: Usage percentage, per-core usage, frequency
- **Memory Metrics**: Total, used, free, available memory and swap
- **Disk Metrics**: Usage per mounted partition (total, used, free, percentage)
- **Temperature**: CPU temperature from thermal zone
- **Network Metrics**: Bytes/packets sent/received per network interface, errors, drops

## Prerequisites

- Python 3.7 or higher
- Raspberry Pi (or Linux system with similar capabilities)
- InfluxDB running (via Docker Compose)
- Access to `/sys/class/thermal/thermal_zone0/temp` for temperature monitoring

## Installation

1. **Install Python dependencies:**

```bash
cd monitor
pip install -r requirements.txt
```

Or using a virtual environment (recommended):

```bash
cd monitor
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment variables:**

Add these to your `.env` file in the project root:

```bash
# InfluxDB 2.x Initialization (for docker-compose)
INFLUXDB_USERNAME=admin
INFLUXDB_PASSWORD=your-secure-password
INFLUXDB_ORG=my-org
INFLUXDB_BUCKET=raspberrypi
INFLUXDB_TOKEN=your-admin-token  # Optional - auto-generated if not set

# InfluxDB Connection (for monitor service)
INFLUXDB_URL=http://influxdb:8086  # Use 'localhost:8086' if running standalone

# Monitoring Configuration
HOSTNAME=raspberrypi
COLLECTION_INTERVAL=60  # Seconds between metric collections

# Feature toggles (true/false)
ENABLE_CPU=true
ENABLE_MEMORY=true
ENABLE_DISK=true
ENABLE_TEMPERATURE=true
ENABLE_NETWORK=true

# CPU Temperature Path (default: /sys/class/thermal/thermal_zone0/temp)
CPU_TEMP_PATH=/sys/class/thermal/thermal_zone0/temp

# Optional: Network IPs (if using static IPs in docker-compose)
INFLUXDB_IP=172.x.x.x
MONITOR_IP=172.x.x.x
```

## Usage

### Running the Monitoring Script

**Option 1: Direct execution**

```bash
cd monitor
python3 main.py
```

**Option 2: Make it executable and run**

```bash
cd monitor
chmod +x main.py
./main.py
```

**Option 3: Run as a background service**

```bash
cd monitor
nohup python3 main.py > monitor.log 2>&1 &
```

### Running as a Systemd Service

Create a systemd service file `/etc/systemd/system/pi-monitor.service`:

```ini
[Unit]
Description=Raspberry Pi Monitoring Service
After=network.target docker.service

[Service]
Type=simple
User=pi
WorkingDirectory=/path/to/DomoticPi/monitor
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /path/to/DomoticPi/monitor/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable pi-monitor.service
sudo systemctl start pi-monitor.service
sudo systemctl status pi-monitor.service
```

## Configuration

### InfluxDB Setup

The scripts are configured to work with InfluxDB 2.x. The `docker-compose.yaml` automatically initializes InfluxDB 2.x on first startup using these environment variables:

- `INFLUXDB_USERNAME` - Admin username (default: admin)
- `INFLUXDB_PASSWORD` - Admin password (required)
- `INFLUXDB_ORG` - Organization name (default: my-org)
- `INFLUXDB_BUCKET` - Bucket name for metrics (default: raspberrypi)
- `INFLUXDB_TOKEN` - Admin token (optional, auto-generated if not set)

**For InfluxDB 2.x:**

- Requires `INFLUXDB_TOKEN` and `INFLUXDB_ORG` for the monitor service
- Uses buckets instead of databases
- Token can be retrieved from InfluxDB UI (Data → Tokens) after first startup

**For InfluxDB 1.x:**
You may need to modify `monitor/influxdb_client.py` to use the InfluxDB 1.x client library.

### Customizing Metrics Collection

Edit `monitor/config.py` or set environment variables to:

- Change collection interval
- Enable/disable specific metric categories
- Customize CPU temperature path

## Data Structure in InfluxDB

Metrics are written to InfluxDB with the following structure:

### Measurement: `cpu`

- Tags: `host`
- Fields: `cpu_usage_percent`, `cpu_count`, `cpu_freq_current`, `cpu_core_0_usage`, etc.

### Measurement: `memory`

- Tags: `host`
- Fields: `memory_total`, `memory_used`, `memory_free`, `memory_percent`, `swap_total`, etc.

### Measurement: `temperature`

- Tags: `host`
- Fields: `cpu_temperature`

### Measurement: `disk`

- Tags: `host`, `device`, `mountpoint`
- Fields: `disk_total`, `disk_used`, `disk_free`, `disk_percent`

### Measurement: `network`

- Tags: `host`, `interface`
- Fields: `bytes_sent`, `bytes_recv`, `packets_sent`, `packets_recv`, `errin`, `errout`, etc.

## Grafana Dashboard

After data is being collected, create a Grafana dashboard:

1. **Add InfluxDB as a data source:**

   - URL: `http://influxdb:8086` (or `http://localhost:8086` if running locally)
   - Database/Bucket: `raspberrypi`
   - Organization: `my-org` (for InfluxDB 2.x)

2. **Create panels for:**

   - CPU usage (line graph)
   - Memory usage (line graph)
   - CPU temperature (line graph)
   - Disk usage per partition (line graph)
   - Network traffic per interface (line graph)

3. **Example queries:**

```flux
# CPU Usage
from(bucket: "raspberrypi")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "cpu")
  |> filter(fn: (r) => r["_field"] == "cpu_usage_percent")

# CPU Temperature
from(bucket: "raspberrypi")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "temperature")
  |> filter(fn: (r) => r["_field"] == "cpu_temperature")

# Memory Usage
from(bucket: "raspberrypi")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "memory")
  |> filter(fn: (r) => r["_field"] == "memory_percent")
```

## Troubleshooting

### Connection Issues

- **Cannot connect to InfluxDB:**
  - Verify InfluxDB is running: `docker compose ps influxdb`
  - Check the URL: `http://localhost:8086` or `http://influxdb:8086` (from Docker network)
  - Verify port 8086 is accessible

### Permission Issues

- **Cannot read CPU temperature:**

  - Check file exists: `ls -l /sys/class/thermal/thermal_zone0/temp`
  - Run with appropriate permissions or add user to required groups

- **Cannot read disk metrics:**
  - Some partitions may require root access
  - The script will skip inaccessible partitions

### Missing Metrics

- Check that the corresponding feature is enabled in configuration
- Verify the metric source is available on your system
- Check logs for error messages

## Project Structure

```
monitor/
├── __init__.py          # Package initialization
├── config.py            # Configuration management
├── metrics_collector.py # System metrics collection
├── influxdb_client.py   # InfluxDB writing client
├── main.py              # Main monitoring script
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker build file
└── README.md            # This file
```

## License

See LICENSE file in the project root.
