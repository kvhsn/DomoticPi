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
| `mqtt_secrets.env` | Template for MQTT credentials (must be moved to `/etc/mqtt_secrets.env`) |
