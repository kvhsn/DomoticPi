# 🚀 Automatic Deployment Setup Guide

This guide explains how to set up secure automatic deployment from GitHub to your Raspberry Pi using GitHub Actions.

## 📋 Table of Contents

- [Overview](#overview)
- [Security Architecture](#security-architecture)
- [Prerequisites](#prerequisites)
- [Step-by-Step Setup](#step-by-step-setup)
  - [1. Create Deployment User on Raspberry Pi](#1-create-deployment-user-on-raspberry-pi)
  - [2. Generate SSH Key Pair](#2-generate-ssh-key-pair)
  - [3. Configure GitHub Secrets](#3-configure-github-secrets)
  - [4. Set Up Deployment Directory](#4-set-up-deployment-directory)
  - [5. Test the Deployment](#5-test-the-deployment)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)
- [Rollback Procedures](#rollback-procedures)

---

## 🎯 Overview

The automatic deployment system works as follows:

1. Developer merges a PR to `main` branch
2. GitHub Actions workflow is triggered
3. Workflow connects to Raspberry Pi via SSH using a restricted user
4. Latest code is pulled from GitHub
5. Docker containers are updated and restarted
6. Deployment status is reported

## 🔒 Security Architecture

### Defense in Depth Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Secrets (Encrypted):                                 │  │
│  │  - SSH_PRIVATE_KEY (deploy key, never exposed)      │  │
│  │  - DEPLOY_HOST (Raspberry Pi IP/hostname)           │  │
│  │  - DEPLOY_USER (restricted user: deployer)          │  │
│  │  - DEPLOY_PATH (deployment directory path)          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓ SSH (Port 22)
                     [Public Internet]
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ User: deployer (restricted)                          │  │
│  │  - No sudo access                                    │  │
│  │  - No shell access (forced command)                  │  │
│  │  - SSH key authentication only                       │  │
│  │  - Member of 'docker' group only                     │  │
│  │  - Restricted to deployment directory                │  │
│  │  - authorized_keys with command restriction          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Docker Daemon                                        │  │
│  │  - Only accessible by docker group                   │  │
│  │  - Deployer can only run specific commands          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Security Principles

1. **Least Privilege**: Deploy user has minimal permissions
2. **SSH Key Authentication**: No password authentication
3. **Command Restriction**: SSH key restricted to specific commands
4. **No Sudo Access**: User cannot escalate privileges
5. **Docker Group Only**: Limited to Docker operations
6. **Secrets Management**: All sensitive data in GitHub Secrets
7. **Audit Trail**: All deployments logged

---

## 📦 Prerequisites

Before starting, ensure you have:

- ✅ Raspberry Pi running and accessible via SSH
- ✅ Docker and Docker Compose installed on Raspberry Pi
- ✅ Git installed on Raspberry Pi
- ✅ Admin/sudo access to Raspberry Pi
- ✅ Admin access to GitHub repository
- ✅ The repository cloned on Raspberry Pi

---

## 🛠️ Step-by-Step Setup

### 1. Create Deployment User on Raspberry Pi

SSH into your Raspberry Pi as your normal user (with sudo access):

```bash
ssh pi@your-raspberry-pi-ip
```

Create a restricted deployment user:

```bash
# Create user without home directory login shell
sudo useradd -r -m -s /bin/bash -c "GitHub Actions Deployer" deployer

# Add user to docker group (allows Docker operations)
sudo usermod -aG docker deployer

# Create .ssh directory for the deployer user
sudo mkdir -p /home/deployer/.ssh
sudo chmod 700 /home/deployer/.ssh
sudo chown deployer:deployer /home/deployer/.ssh
```

**Important**: The `deployer` user:
- ❌ Does NOT have sudo access
- ❌ Does NOT have password login
- ✅ Can ONLY authenticate via SSH key
- ✅ Can ONLY run Docker commands
- ✅ Has restricted SSH access (configured later)

---

### 2. Generate SSH Key Pair

**On your local machine** (not on Raspberry Pi), generate a dedicated SSH key pair:

```bash
# Generate ED25519 key (more secure than RSA)
ssh-keygen -t ed25519 -C "github-actions-deployer" -f ~/.ssh/github_actions_deploy_key

# This creates two files:
# - github_actions_deploy_key (private key - for GitHub Secrets)
# - github_actions_deploy_key.pub (public key - for Raspberry Pi)
```

**Security Note**: 
- ⚠️ **NEVER** commit the private key to Git
- ⚠️ **NEVER** share the private key
- ✅ Only the public key goes on the Raspberry Pi

#### Copy Public Key to Raspberry Pi

```bash
# Display the public key
cat ~/.ssh/github_actions_deploy_key.pub
```

Copy the entire output, then on your Raspberry Pi:

```bash
# SSH into Raspberry Pi
ssh pi@your-raspberry-pi-ip

# Add public key with command restriction
sudo tee /home/deployer/.ssh/authorized_keys > /dev/null << 'EOF'
command="/home/deployer/deploy.sh" ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... github-actions-deployer
EOF

# Replace the "AAAAC3Nza..." part with your actual public key

# Set correct permissions
sudo chmod 600 /home/deployer/.ssh/authorized_keys
sudo chown deployer:deployer /home/deployer/.ssh/authorized_keys
```

**What does `command="/home/deployer/deploy.sh"` do?**

This restricts the SSH key to ONLY execute the `deploy.sh` script, nothing else. Even if the private key is compromised, the attacker can only run this specific script.

---

### 3. Create Deployment Script on Raspberry Pi

Create a controlled deployment script:

```bash
# SSH into Raspberry Pi
ssh pi@your-raspberry-pi-ip

# Create the deployment script
sudo tee /home/deployer/deploy.sh > /dev/null << 'SCRIPT'
#!/bin/bash
set -euo pipefail

# Deployment configuration
DEPLOY_DIR="/opt/DomoticPi"
LOG_FILE="/home/deployer/deployment.log"
BACKUP_DIR="/home/deployer/backups"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Error handler
error_exit() {
    log "ERROR: $1"
    exit 1
}

log "=== Deployment Started ==="
log "User: $(whoami)"
log "Deploy directory: $DEPLOY_DIR"

# Verify we're in the correct directory
cd "$DEPLOY_DIR" || error_exit "Failed to change to deployment directory"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup of current state
BACKUP_NAME="backup_$(date +'%Y%m%d_%H%M%S').tar.gz"
log "Creating backup: $BACKUP_NAME"
tar -czf "$BACKUP_DIR/$BACKUP_NAME" \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='*.log' \
    --exclude='emby' \
    --exclude='homeassistant' \
    --exclude='letsencrypt' \
    --exclude='mosquitto' \
    --exclude='zigbee2mqtt' \
    --exclude='n8n_data' \
    . || log "Warning: Backup creation failed (non-critical)"

# Keep only last 5 backups
log "Cleaning old backups (keeping last 5)"
cd "$BACKUP_DIR" && ls -t backup_*.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm -f

cd "$DEPLOY_DIR" || error_exit "Failed to return to deployment directory"

# Pull latest changes from main branch
log "Pulling latest changes from GitHub..."
git fetch origin main || error_exit "Failed to fetch from GitHub"
git reset --hard origin/main || error_exit "Failed to reset to origin/main"

# Check for docker-compose.yaml changes
log "Checking for configuration changes..."
if git diff --name-only HEAD@{1} HEAD 2>/dev/null | grep -qE 'docker-compose.yaml|.env.example'; then
    log "Docker configuration changed, full restart required"
    FULL_RESTART=true
else
    log "No configuration changes detected"
    FULL_RESTART=false
fi

# Pull latest Docker images
log "Pulling latest Docker images..."
docker compose pull || error_exit "Failed to pull Docker images"

# Restart containers
if [ "$FULL_RESTART" = true ]; then
    log "Performing full restart (configuration changed)..."
    docker compose down || error_exit "Failed to stop containers"
    docker compose up -d || error_exit "Failed to start containers"
else
    log "Performing rolling update (no config changes)..."
    docker compose up -d --remove-orphans || error_exit "Failed to update containers"
fi

# Wait for services to be healthy
log "Waiting for services to start..."
sleep 10

# Check container status
log "Checking container health..."
FAILED_CONTAINERS=$(docker compose ps --format json | jq -r 'select(.State != "running") | .Name' | tr '\n' ' ')

if [ -n "$FAILED_CONTAINERS" ]; then
    log "WARNING: The following containers are not running: $FAILED_CONTAINERS"
    log "Check logs with: docker compose logs [container_name]"
else
    log "All containers are running successfully"
fi

# Cleanup old images
log "Cleaning up old Docker images..."
docker image prune -f || log "Warning: Image cleanup failed (non-critical)"

log "=== Deployment Completed Successfully ==="
log ""

exit 0
SCRIPT

# Make script executable
sudo chmod +x /home/deployer/deploy.sh
sudo chown deployer:deployer /home/deployer/deploy.sh

# Create log file
sudo touch /home/deployer/deployment.log
sudo chown deployer:deployer /home/deployer/deployment.log
```

---

### 4. Set Up Deployment Directory

```bash
# Create deployment directory
sudo mkdir -p /opt/DomoticPi

# Clone the repository (if not already there)
cd /opt
sudo git clone https://github.com/kvhsn/DomoticPi.git

# Set proper ownership
sudo chown -R deployer:deployer /opt/DomoticPi

# Configure git to allow directory
cd /opt/DomoticPi
sudo -u deployer git config --global --add safe.directory /opt/DomoticPi

# Copy your .env file to the deployment directory
sudo cp /path/to/your/.env /opt/DomoticPi/.env
sudo chown deployer:deployer /opt/DomoticPi/.env
sudo chmod 600 /opt/DomoticPi/.env
```

**Important**: The `.env` file should already be configured on your Raspberry Pi and should NOT be in the repository (it's in `.gitignore`).

---

### 5. Configure GitHub Secrets

Go to your GitHub repository:

1. Navigate to: `Settings` → `Secrets and variables` → `Actions`
2. Click `New repository secret`
3. Add the following secrets:

#### SSH_PRIVATE_KEY

```bash
# On your LOCAL machine, display the private key:
cat ~/.ssh/github_actions_deploy_key

# Copy the ENTIRE output including:
# -----BEGIN OPENSSH PRIVATE KEY-----
# ... content ...
# -----END OPENSSH PRIVATE KEY-----
```

- **Name**: `SSH_PRIVATE_KEY`
- **Value**: Paste the entire private key content

#### DEPLOY_HOST

- **Name**: `DEPLOY_HOST`
- **Value**: Your Raspberry Pi IP address or hostname (e.g., `192.168.1.100`)

#### DEPLOY_USER

- **Name**: `DEPLOY_USER`
- **Value**: `deployer`

#### DEPLOY_PATH

- **Name**: `DEPLOY_PATH`
- **Value**: `/opt/DomoticPi`

**Security Verification**:
- ✅ All secrets are encrypted by GitHub
- ✅ Secrets are never exposed in logs
- ✅ Only authorized workflows can access secrets
- ✅ Secrets are not available in forked repositories

---

### 6. Test the Deployment

#### Manual SSH Test

From your local machine:

```bash
# Test SSH connection with the deploy key
ssh -i ~/.ssh/github_actions_deploy_key deployer@your-raspberry-pi-ip

# This should automatically run the deploy.sh script
# You should see deployment logs
```

If the connection works and you see the deployment script running, the setup is correct!

#### Test GitHub Actions Workflow

1. Create a small change in your repository (e.g., update README)
2. Create a PR and merge it to `main`
3. Go to `Actions` tab in GitHub
4. Watch the deployment workflow run
5. Check the logs for any errors

#### Verify on Raspberry Pi

```bash
# SSH into Raspberry Pi
ssh pi@your-raspberry-pi-ip

# Check deployment logs
sudo cat /home/deployer/deployment.log

# Check container status
cd /opt/DomoticPi
docker compose ps

# Check recent deployments
ls -lh /home/deployer/backups/
```

---

## 🔐 Security Best Practices

### SSH Configuration

Harden SSH on your Raspberry Pi (`/etc/ssh/sshd_config`):

```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Add/modify these settings:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2

# For the deployer user specifically, add at the end:
Match User deployer
    PasswordAuthentication no
    PubkeyAuthentication yes
    PermitTTY no
    X11Forwarding no
    AllowTcpForwarding no
    ForceCommand /home/deployer/deploy.sh
```

Restart SSH:

```bash
sudo systemctl restart sshd
```

### Firewall Configuration

```bash
# Allow SSH only from specific IPs (optional but recommended)
sudo ufw allow from YOUR_HOME_IP to any port 22 proto tcp
sudo ufw allow from GITHUB_ACTIONS_IP_RANGE to any port 22 proto tcp

# Enable firewall
sudo ufw enable
```

**Note**: GitHub Actions IP ranges change. Consider using a VPN or fixed IP for better security.

### Monitoring

Set up monitoring for suspicious activities:

```bash
# Install fail2ban to block repeated failed SSH attempts
sudo apt-get update
sudo apt-get install fail2ban -y

# Check SSH authentication logs
sudo tail -f /var/log/auth.log | grep deployer
```

### Secrets Rotation

Regularly rotate your deployment SSH key (recommended every 6 months):

1. Generate a new SSH key pair
2. Update GitHub Secret `SSH_PRIVATE_KEY`
3. Update `/home/deployer/.ssh/authorized_keys` on Raspberry Pi
4. Test the new key
5. Delete the old private key from your local machine

### Regular Audits

```bash
# Check who has accessed the deployer account
sudo lastlog -u deployer

# Check deployment history
sudo tail -100 /home/deployer/deployment.log

# Review active SSH sessions
who
```

---

## 🐛 Troubleshooting

### Issue: SSH Connection Failed

**Symptoms**: GitHub Actions can't connect to Raspberry Pi

**Solutions**:

```bash
# 1. Verify SSH service is running
sudo systemctl status sshd

# 2. Check if public key is correctly installed
sudo cat /home/deployer/.ssh/authorized_keys

# 3. Check SSH logs
sudo tail -50 /var/log/auth.log | grep deployer

# 4. Test connection manually
ssh -i ~/.ssh/github_actions_deploy_key deployer@your-raspberry-pi-ip

# 5. Verify permissions
ls -la /home/deployer/.ssh/
# Should show:
# drwx------ 2 deployer deployer 4096 ... .ssh
# -rw------- 1 deployer deployer  xxx ... authorized_keys
```

### Issue: Docker Permission Denied

**Symptoms**: `deployer` user cannot run Docker commands

**Solutions**:

```bash
# 1. Verify deployer is in docker group
groups deployer
# Should include 'docker'

# 2. If not, add to docker group
sudo usermod -aG docker deployer

# 3. Test Docker access
sudo -u deployer docker ps

# 4. Restart Docker daemon
sudo systemctl restart docker
```

### Issue: Deployment Script Fails

**Symptoms**: Deployment logs show errors

**Solutions**:

```bash
# 1. Check deployment logs
sudo cat /home/deployer/deployment.log

# 2. Run deployment script manually as deployer
sudo -u deployer /home/deployer/deploy.sh

# 3. Check Docker container logs
cd /opt/DomoticPi
docker compose logs --tail=100

# 4. Verify .env file exists and has correct values
sudo cat /opt/DomoticPi/.env

# 5. Check git repository status
cd /opt/DomoticPi
sudo -u deployer git status
sudo -u deployer git log --oneline -5
```

### Issue: Containers Not Starting

**Symptoms**: Deployment succeeds but containers are not running

**Solutions**:

```bash
# 1. Check container status
cd /opt/DomoticPi
docker compose ps

# 2. Check logs for specific container
docker compose logs container_name

# 3. Try manual restart
docker compose down
docker compose up -d

# 4. Check for port conflicts
sudo netstat -tulpn | grep LISTEN

# 5. Verify .env variables are set
docker compose config
```

### Issue: GitHub Actions Workflow Fails

**Symptoms**: Workflow fails in GitHub Actions

**Solutions**:

1. Check workflow logs in GitHub Actions tab
2. Verify all GitHub Secrets are correctly set
3. Test SSH connection manually with the same key
4. Check if Raspberry Pi is reachable from internet
5. Verify the deploy script has no syntax errors

---

## 🔄 Rollback Procedures

### Automatic Rollback

If a deployment fails, the system maintains backups automatically.

### Manual Rollback

```bash
# 1. SSH into Raspberry Pi
ssh pi@your-raspberry-pi-ip

# 2. List available backups
ls -lh /home/deployer/backups/

# 3. Extract a backup (example with backup from today)
cd /opt/DomoticPi
sudo -u deployer tar -xzf /home/deployer/backups/backup_20241221_143000.tar.gz

# 4. Restart containers
docker compose down
docker compose up -d

# 5. Verify services are running
docker compose ps
```

### Emergency Procedures

If everything fails:

```bash
# 1. Stop all containers
cd /opt/DomoticPi
docker compose down

# 2. Reset to last known good commit
sudo -u deployer git log --oneline -10  # Find good commit
sudo -u deployer git reset --hard <commit-hash>

# 3. Restart containers
docker compose up -d

# 4. Notify team and investigate
```

---

## 📊 Monitoring Deployments

### View Deployment History

```bash
# On Raspberry Pi
sudo cat /home/deployer/deployment.log | grep "Deployment Started"

# View last 10 deployments
sudo cat /home/deployer/deployment.log | grep "Deployment Started" | tail -10
```

### Check Container Health

```bash
cd /opt/DomoticPi

# Check all containers
docker compose ps

# Check specific container logs
docker compose logs -f container_name

# Check resource usage
docker stats
```

---

## 📝 Maintenance Tasks

### Weekly

- ✅ Review deployment logs
- ✅ Check container health
- ✅ Verify backup integrity

### Monthly

- ✅ Review and clean old backups (keep last 30 days)
- ✅ Update Docker images
- ✅ Review SSH logs for suspicious activity

### Every 6 Months

- ✅ Rotate SSH deployment keys
- ✅ Review and update security configurations
- ✅ Audit user permissions

---

## 🎯 Success Criteria

After completing this setup, you should have:

- ✅ Restricted `deployer` user with minimal permissions
- ✅ SSH key-based authentication (no passwords)
- ✅ Forced command execution (SSH key restricted to deploy script)
- ✅ GitHub Secrets configured correctly
- ✅ Automatic deployment on merge to `main`
- ✅ Backup system in place
- ✅ Comprehensive logging
- ✅ Ability to rollback deployments
- ✅ No sensitive data exposed in repository
- ✅ Defense-in-depth security architecture

---

## 📞 Support

If you encounter issues:

1. Review this document thoroughly
2. Check the [Troubleshooting](#troubleshooting) section
3. Review deployment logs on Raspberry Pi
4. Check GitHub Actions workflow logs
5. Verify all security configurations

---

## 🔗 Related Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [SSH Security Best Practices](https://www.ssh.com/academy/ssh/security)
- [Raspberry Pi Security Guide](https://www.raspberrypi.com/documentation/computers/configuration.html#securing-your-raspberry-pi)

---

**Last Updated**: 2024-12-21
**Version**: 1.0.0
