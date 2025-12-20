# Scripts

This directory contains utility scripts for the DomoticPi infrastructure.

## NAS Disk Inspector (`nas-disk-inspector.sh`)

This script monitors disk space usage on the NAS mount point (`/data/usbshare`) and publishes the data to Home Assistant via MQTT protocol. This enables real-time disk usage visualization in Home Assistant dashboards.

### How it works

1. Retrieves disk information (total, used, available) using `df -h`
2. Publishes data to MQTT topic `homeassistant/sensor/nas/state`
3. Uses secured MQTT authentication via environment variables

### Installation

#### 1. Move the secrets file and secure it

```bash
# Copy the secrets template to /etc
sudo cp scripts/mqtt_secrets.env /etc/mqtt_secrets.env

# Edit with your MQTT credentials
sudo nano /etc/mqtt_secrets.env
# Add: MQTT_USER=your_username
# Add: MQTT_PASS=your_password

# Secure the file (readable only by root)
sudo chown root:root /etc/mqtt_secrets.env
sudo chmod 600 /etc/mqtt_secrets.env
```

#### 2. Move the script and make it executable

```bash
# Copy the script to system bin directory
sudo cp scripts/nas-disk-inspector.sh /usr/local/bin/nas-disk-inspector.sh

# Make it executable
sudo chmod 755 /usr/local/bin/nas-disk-inspector.sh
```

#### 3. Schedule periodic execution with crontab

```bash
# Edit root's crontab (required to read /etc/mqtt_secrets.env)
sudo crontab -e

# Add this line to run every 5 minutes:
*/5 * * * * /usr/local/bin/nas-disk-inspector.sh

# Or run every hour:
0 * * * * /usr/local/bin/nas-disk-inspector.sh
```

#### 4. Verify the cron job is registered

```bash
sudo crontab -l
```

### Home Assistant Configuration

Add a sensor in Home Assistant to receive the MQTT data:

```yaml
mqtt:
  sensor:
    - name: "NAS Disk Usage"
      state_topic: "homeassistant/sensor/nas/state"
      value_template: "{{ value.split()[1] }}"
      unit_of_measurement: "GB"
```

### Files

| File | Description |
|------|-------------|
| `nas-disk-inspector.sh` | Main script that collects disk info and publishes to MQTT |
| `rpi-metrics.sh` | Script that collects Raspberry Pi system metrics and publishes to MQTT |
| `mqtt_secrets.env` | Template for MQTT credentials (must be moved to `/etc/mqtt_secrets.env`) |

---

## Raspberry Pi Metrics (`rpi-metrics.sh`)

This script monitors Raspberry Pi system performance metrics (CPU, RAM, temperature, disk, load) and publishes them to Home Assistant via MQTT protocol. This enables real-time system monitoring in Home Assistant dashboards.

### Metrics Collected

| Metric | Type | Description |
|--------|------|-------------|
| `cpu_temp` | float | CPU temperature in °C |
| `cpu_usage` | float | CPU usage percentage |
| `ram_total_mb` | int | Total RAM in MB |
| `ram_used_mb` | int | Used RAM in MB |
| `ram_free_mb` | int | Free RAM in MB |
| `ram_available_mb` | int | Available RAM in MB |
| `ram_usage_percent` | float | RAM usage percentage |
| `disk_total` | string | Root partition total size |
| `disk_used` | string | Root partition used space |
| `disk_available` | string | Root partition available space |
| `disk_usage_percent` | string | Root partition usage percentage |
| `load_avg` | float | 1-minute load average |
| `uptime_seconds` | int | System uptime in seconds |

### How it works

1. Collects CPU temperature from `/sys/class/thermal/thermal_zone0/temp`
2. Retrieves CPU usage via `top`
3. Gathers RAM metrics using `free -m`
4. Gets disk usage for root partition via `df -h`
5. Reads load average from `/proc/loadavg`
6. Publishes all data as JSON to MQTT topic `homeassistant/sensor/rpi/state`

### Installation

#### 1. Ensure MQTT secrets are configured

If not already done (see NAS Disk Inspector section above), configure the MQTT secrets file.

#### 2. Move the script and make it executable

```bash
# Copy the script to system bin directory
sudo cp scripts/rpi-metrics.sh /usr/local/bin/rpi-metrics.sh

# Make it executable
sudo chmod 755 /usr/local/bin/rpi-metrics.sh
```

#### 3. Schedule periodic execution with crontab

```bash
# Edit root's crontab (required to read /etc/mqtt_secrets.env)
sudo crontab -e

# Add this line to run every minute:
* * * * * /usr/local/bin/rpi-metrics.sh

# Or run every 5 minutes:
*/5 * * * * /usr/local/bin/rpi-metrics.sh
```

### Home Assistant Configuration

Add MQTT sensors in Home Assistant to receive the metrics:

```yaml
mqtt:
  sensor:
    - name: "RPi CPU Temperature"
      state_topic: "homeassistant/sensor/rpi/state"
      value_template: "{{ value_json.cpu_temp }}"
      unit_of_measurement: "°C"
      device_class: temperature

    - name: "RPi CPU Usage"
      state_topic: "homeassistant/sensor/rpi/state"
      value_template: "{{ value_json.cpu_usage }}"
      unit_of_measurement: "%"

    - name: "RPi RAM Usage"
      state_topic: "homeassistant/sensor/rpi/state"
      value_template: "{{ value_json.ram_usage_percent }}"
      unit_of_measurement: "%"

    - name: "RPi RAM Available"
      state_topic: "homeassistant/sensor/rpi/state"
      value_template: "{{ value_json.ram_available_mb }}"
      unit_of_measurement: "MB"

    - name: "RPi Disk Usage"
      state_topic: "homeassistant/sensor/rpi/state"
      value_template: "{{ value_json.disk_usage_percent | replace('%', '') }}"
      unit_of_measurement: "%"

    - name: "RPi Load Average"
      state_topic: "homeassistant/sensor/rpi/state"
      value_template: "{{ value_json.load_avg }}"

    - name: "RPi Uptime"
      state_topic: "homeassistant/sensor/rpi/state"
      value_template: "{{ (value_json.uptime_seconds / 3600) | round(1) }}"
      unit_of_measurement: "hours"
```
