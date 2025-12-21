# DomoticPi

Docker infrastructure for home server based on Traefik, including media management, home automation, and file sharing.

## 📋 Table of Contents

- [Architecture](#architecture)
- [Services](#services)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)

## 🏗️ Architecture

The infrastructure is based on multiple Docker services orchestrated by Docker Compose, with Traefik as the central reverse proxy handling HTTPS routing and automatic SSL certificates via Let's Encrypt.

### Network Schema

```
Internet
    ↓
Traefik (${TRAEFIK_IP}) - Reverse Proxy & SSL
    ├── transmission.{DOMAIN} → Transmission (${TRANSMISSION_IP})
    ├── emby.{DOMAIN} → Emby (${EMBY_IP})
    ├── homeassistant.{DOMAIN} → Home Assistant (${HOMEASSISTANT_IP})
    └── n8n.{DOMAIN} → n8n (${N8N_IP})

Internal Network (${NETWORK_SUBNET})
    ├── Mosquitto (${MOSQUITTO_IP}) - MQTT Broker
    ├── Zigbee2MQTT (${ZIGBEE2MQTT_IP})
    └── Samba (direct ports)
```

### Storage

- `/data/usbshare/` - Main mount point for external storage
  - `/downloads` - Transmission downloads
  - `/Series` - TV Series for Emby
  - `/Movies` - Movies for Emby
  - `/Manga` - Manga for Emby

## 🐳 Services

### Traefik (Reverse Proxy)

- **Port**: 80 (HTTP), 443 (HTTPS)
- **Function**: Reverse proxy with automatic SSL certificate generation
- **Features**:
  - Automatic HTTP → HTTPS redirect
  - Let's Encrypt certificates with TLS challenge
  - Dashboard accessible in insecure mode (development)

### Transmission (BitTorrent Client)

- **URL**: `https://transmission.{DOMAIN}`
- **Internal Port**: 9091
- **Function**: Web-based torrent client
- **Storage**: `/data/usbshare/downloads`

### Emby (Media Server)

- **URL**: `https://emby.{DOMAIN}`
- **Internal Port**: 8096
- **Function**: Multimedia streaming server
- **Support**:
  - TV Series, Movies, Manga
  - Hardware acceleration (ARM64)
- **Libraries**:
  - `/mnt/share1` → Series
  - `/mnt/share2` → Movies
  - `/mnt/share3` → Manga

### Samba (Network Share)

- **Ports**: 137-139, 445
- **Function**: Windows/SMB file sharing server
- **Share**: `\\{IP}\raspberrypi`
- **Access**: Read/Write/Guest allowed

### Home Assistant (Home Automation)

- **URL**: `https://homeassistant.{DOMAIN}`
- **Internal Port**: 8123
- **Function**: Home automation platform
- **Hardware**:
  - Zigbee USB dongle (Sonoff Zigbee 3.0 USB Dongle Plus)
  - D-Bus access for system integrations

### Mosquitto (MQTT Broker)

- **Ports**: 1883 (MQTT), 9001 (WebSocket)
- **IP**: `${MOSQUITTO_IP}` (configured in `.env`)
- **Function**: IoT message broker
- **Used by**: Home Assistant, Zigbee2MQTT

### Zigbee2MQTT

- **Port**: 8080 (Frontend)
- **IP**: `${ZIGBEE2MQTT_IP}` (configured in `.env`)
- **Function**: Bridge between Zigbee devices and MQTT
- **Hardware**: Zigbee USB dongle shared with Home Assistant

### n8n (Workflow Automation)

- **URL**: `https://n8n.{DOMAIN}`
- **Internal Port**: 5678
- **IP**: `${N8N_IP}` (configured in `.env`)
- **Function**: Self-hosted workflow automation platform
- **Features**:
  - Visual workflow editor
  - 400+ integrations (HTTP, databases, APIs, etc.)
  - Webhooks support for external triggers
  - Basic authentication enabled by default
- **Use cases**:
  - Home automation workflows
  - Data synchronization between services
  - Notifications and alerts
  - Integration with Home Assistant

## 🔧 Prerequisites

### Hardware

- Raspberry Pi (or ARM64 equivalent) with Docker installed
- External USB drive mounted on `/data/usbshare`
- Zigbee USB dongle: Sonoff Zigbee 3.0 USB Dongle Plus

### Software

- Docker Engine 20.10+
- Docker Compose V2
- Domain configured pointing to your public IP
- Ports 80 and 443 opened on your router

### File System

```bash
# Required directory structure
/data/usbshare/
├── downloads/
├── Series/
├── Movies/
└── Manga/
```

## 📦 Installation

### 1. Clone or create the structure

```bash
# Create the project directory
mkdir ~/home-server && cd ~/home-server

# Create configuration directories
mkdir -p letsencrypt emby homeassistant mosquitto/{config,data,log} zigbee2mqtt/data n8n
```

### 2. Create the .env file

**⚠️ IMPORTANT: Never commit the `.env` file to version control. It's already in `.gitignore`.**

```bash
# Copy the example template
cp .env.example .env

# Edit with your actual values
nano .env
```

Configure the following values in your `.env` file:

| Variable                  | Description                                  | Example                          |
| ------------------------- | -------------------------------------------- | -------------------------------- |
| `DOMAIN`                  | Your domain name or IP address               | `example.com` or `192.168.1.100` |
| `ACME_EMAIL`              | Email for Let's Encrypt certificates         | `admin@example.com`              |
| **Network Configuration** | _Internal Docker IPs (not exposed publicly)_ |                                  |
| `TRAEFIK_IP`              | Traefik reverse proxy IP                     | `x.x.x.x`                        |
| `TRANSMISSION_IP`         | Transmission service IP                      | `x.x.x.x`                        |
| `EMBY_IP`                 | Emby media server IP                         | `x.x.x.x`                        |
| `HOMEASSISTANT_IP`        | Home Assistant IP                            | `x.x.x.x`                        |
| `MOSQUITTO_IP`            | Mosquitto MQTT broker IP                     | `x.x.x.x`                        |
| `ZIGBEE2MQTT_IP`          | Zigbee2MQTT bridge IP                        | `x.x.x.x`                        |
| `N8N_IP`                  | n8n automation platform IP                   | `x.x.x.x`                        |
| `NETWORK_SUBNET`          | Docker network subnet                        | `x.x.x.x/16`                     |
| **Credentials**           | _Keep these secure_                          |                                  |
| `TRANSMISSION_USER`       | Username for Transmission access             | `torrent_user`                   |
| `TRANSMISSION_PASS`       | Password for Transmission access             | `secure_password`                |
| `SAMBA_USER`              | Username for Samba file sharing              | `share_user`                     |
| `SAMBA_PASS`              | Password for Samba file sharing              | `secure_password`                |
| `N8N_ENCRYPTION_KEY`      | Encryption key for credentials (min 32 chars)| `your-32-char-encryption-key`    |

### 3. Check permissions

```bash
# Adjust permissions for user 1000:1000
sudo chown -R 1000:1000 emby homeassistant mosquitto zigbee2mqtt n8n

# Check USB mount point
ls -la /data/usbshare
```

### 4. Start the services

```bash
docker compose up -d
```

### 5. Verify deployment

```bash
# Check containers
docker compose ps

# Check logs
docker compose logs -f traefik
```

## ⚙️ Configuration

### Environment Variables (.env)

Create a `.env` file at the project root with the following variables:

```env
# Domain configuration
DOMAIN=yourdomain.com
ACME_EMAIL=your-email@example.com

# Network configuration (internal Docker IPs - not exposed publicly)
TRAEFIK_IP=
TRANSMISSION_IP=
EMBY_IP=
HOMEASSISTANT_IP=
MOSQUITTO_IP=
ZIGBEE2MQTT_IP=
N8N_IP=
NETWORK_SUBNET=

# Transmission credentials
TRANSMISSION_USER=admin
TRANSMISSION_PASS=yourPassword

# Samba credentials
SAMBA_USER=user
SAMBA_PASS=yourPassword

# n8n configuration
N8N_ENCRYPTION_KEY=your-32-character-encryption-key
```

### Mosquitto Configuration

Create the file `mosquitto/config/mosquitto.conf`:

```conf
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
```

### Zigbee2MQTT Configuration

The `zigbee2mqtt/data/configuration.yaml` file will be created on first launch, edit to configure:

```yaml
homeassistant: true
permit_join: false
mqtt:
  base_topic: zigbee2mqtt
  server: mqtt://${MOSQUITTO_IP}:1883
serial:
  port: /dev/ttyUSB0
frontend:
  port: 8080
  host: 0.0.0.0
advanced:
  network_key: GENERATE
  pan_id: GENERATE
```

## 🚀 Usage

### Access Services

- **Transmission**: `https://transmission.yourdomain.com`
- **Emby**: `https://emby.yourdomain.com`
- **Home Assistant**: `https://homeassistant.yourdomain.com`
- **n8n**: `https://n8n.yourdomain.com`
- **Zigbee2MQTT**: `http://{SERVER_IP}:8080`
- **Samba**: `\\{SERVER_IP}\raspberrypi`

### Initial Setup

#### Emby

1. Access the web interface
2. Follow the setup wizard
3. Add media libraries:
   - Series: `/mnt/share1`
   - Movies: `/mnt/share2`
   - Manga: `/mnt/share3`

#### Home Assistant

1. Access the web interface
2. Create a user account
3. Configure MQTT integration (Mosquitto: `${MOSQUITTO_IP}`)
4. Add Zigbee2MQTT integration

#### Transmission

1. Log in with configured credentials
2. Configure download folders if necessary

#### n8n

1. Access `https://n8n.yourdomain.com`
2. On first access, create an owner account (email + password)
3. Create your first workflow using the visual editor
4. Useful integrations:
   - **Home Assistant**: Trigger workflows from HA events
   - **Webhook**: Receive external triggers
   - **HTTP Request**: Call external APIs
   - **MQTT**: Integrate with your Mosquitto broker

## 🔄 Maintenance

### Update Services

```bash
# Pull latest images
docker compose pull

# Restart with new images
docker compose up -d
```

### Backup

```bash
# Backup configurations
tar -czf backup-$(date +%Y%m%d).tar.gz \
  emby/ \
  homeassistant/ \
  mosquitto/ \
  zigbee2mqtt/ \
  n8n/ \
  letsencrypt/ \
  docker-compose.yaml \
  .env
```

### Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f homeassistant

# Last 100 lines
docker compose logs --tail=100 traefik
```

### Restart

```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart transmission
```

## 🐛 Troubleshooting

### SSL/Certificate Issues

```bash
# Check Traefik logs
docker compose logs traefik | grep -i acme

# Remove corrupted certificates
rm -f letsencrypt/acme.json
docker compose restart traefik
```

### Permission Issues

```bash
# Check UIDs/GIDs
docker compose exec emby id
docker compose exec homeassistant id

# Fix permissions
sudo chown -R 1000:1000 emby homeassistant
```

### Zigbee Issues

```bash
# Check if dongle is detected
ls -la /dev/serial/by-id/

# Restart zigbee2mqtt
docker compose restart zigbee2mqtt

# Check logs
docker compose logs -f zigbee2mqtt
```

### Network Issues

```bash
# Check assigned IPs
docker network inspect home-server_traefik-net

# Test inter-container connectivity
docker compose exec homeassistant ping ${MOSQUITTO_IP}
```

### Disk Space

```bash
# Check Docker disk usage
docker system df

# Clean unused resources
docker system prune -a

# Check USB drive space
df -h /data/usbshare
```

## 📊 Scripts

Utility scripts for monitoring and maintenance are available in the [`scripts/`](scripts/README.md) directory.

- **NAS Disk Inspector** - Monitors disk space and reports to Home Assistant via MQTT

## 📝 Notes

- Services use `Europe/Paris` timezone
- All persistent services use UID/GID 1000:1000
- Docker network uses subnet `${NETWORK_SUBNET}` (configured in `.env`)
- Let's Encrypt certificates are valid for 90 days and renewed automatically
- Debug mode is enabled on Traefik (disable in production)

## 🔒 Security

### Environment Variables Protection

**Critical**: Always use the `.env` file for sensitive information:

- ✅ Domain names and IP addresses
- ✅ User credentials (Transmission, Samba)
- ✅ Email addresses
- ✅ API keys and tokens

The `.env` file is already in `.gitignore` to prevent accidental commits. Use the provided `.env.example` as a template for new installations.

### Recommendations

1. **Keep `.env` file secure**:

   - Never commit it to version control
   - Set appropriate file permissions: `chmod 600 .env`
   - Backup securely separately from public repositories

2. **Disable Traefik dashboard in production**:

   - Remove `--api.insecure=true`
   - Add authentication if necessary

3. **Use strong passwords** for Transmission and Samba

   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, and symbols

4. **Configure a firewall** to limit service access

5. **Backup regularly** configurations and data

6. **Update regularly** Docker images

7. **Disable Traefik debug mode** in production:
   ```yaml
   - "--log.level=INFO" # instead of DEBUG
   ```

## 📄 License

Free to use for personal use.
