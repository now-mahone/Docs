# VPS Server Setup Guide

## 01_INITIAL_HARDENING
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Setup Firewall
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable

# SSH Hardening (Optional but recommended)
# Edit /etc/ssh/sshd_config to disable password auth and change port
```

## 02_INSTALL_DOCKER
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install -y docker-compose
```

## 03_DEPLOY_BOT
```bash
# Clone repository
git clone <your-repo-url> kerne-protocol
cd kerne-protocol/bot

# Configure environment
nano .env # Paste your production .env content

# Launch infrastructure
sudo docker-compose up -d

# Check logs
sudo docker-compose logs -f
```

## 04_MONITORING
- The bot will automatically restart if it crashes.
- Discord alerts will notify you of low gas or reporting anomalies.
- The Canary tripwire should be run as a separate background process or added to docker-compose.
