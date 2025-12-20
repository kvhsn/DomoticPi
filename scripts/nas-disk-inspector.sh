#!/bin/bash

mount_point="/data/usbshare"
mqtt_topic="homeassistant/sensor/nas/state"
disk_info=$(df -h "$mount_point" | awk 'NR==2 {print $2,$3,$4}')

# Charge les variables d’environnement
source /etc/mqtt_secrets.env
 
mosquitto_pub -h localhost -p 1883 -u "$MQTT_USER" -P "$MQTT_PASS" -t "$mqtt_topic" -m "$disk_info"
