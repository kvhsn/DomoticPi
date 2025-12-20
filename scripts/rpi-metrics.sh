#!/bin/bash

mqtt_topic="homeassistant/sensor/rpi/state"

# Load environment variables
source /etc/mqtt_secrets.env

# CPU temperature (Raspberry Pi specific)
if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    cpu_temp=$(awk '{printf "%.1f", $1/1000}' /sys/class/thermal/thermal_zone0/temp)
else
    cpu_temp="null"
fi

# CPU usage (percentage)
cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print 100 - $8}')

# RAM metrics (in MB)
read -r total_ram used_ram free_ram available_ram <<< $(free -m | awk 'NR==2 {print $2, $3, $4, $7}')
ram_usage_percent=$(awk "BEGIN {printf \"%.1f\", ($used_ram/$total_ram)*100}")

# Disk usage for root partition
read -r disk_total disk_used disk_available disk_usage_percent <<< $(df -h / | awk 'NR==2 {print $2, $3, $4, $5}')

# Load average
load_avg=$(cat /proc/loadavg | awk '{print $1}')

# Uptime in seconds
uptime_seconds=$(cat /proc/uptime | awk '{print int($1)}')

# Build JSON payload
payload=$(cat <<EOF
{
    "cpu_temp": $cpu_temp,
    "cpu_usage": $cpu_usage,
    "ram_total_mb": $total_ram,
    "ram_used_mb": $used_ram,
    "ram_free_mb": $free_ram,
    "ram_available_mb": $available_ram,
    "ram_usage_percent": $ram_usage_percent,
    "disk_total": "$disk_total",
    "disk_used": "$disk_used",
    "disk_available": "$disk_available",
    "disk_usage_percent": "$disk_usage_percent",
    "load_avg": $load_avg,
    "uptime_seconds": $uptime_seconds
}
EOF
)

# Publish to MQTT
mosquitto_pub -h localhost -p 1883 -u "$MQTT_USER" -P "$MQTT_PASS" -t "$mqtt_topic" -m "$payload"
