# Hostinger VPS Deployment Guide

## Prerequisites

### Hostinger VPS Requirements
- **Minimum**: 2GB RAM, 2 CPU cores, 40GB SSD
- **Recommended**: 4GB RAM, 4 CPU cores, 80GB SSD  
- **OS**: Ubuntu 20.04 or 22.04 LTS
- **Location**: Choose closest to your target audience

### Purchase Hostinger VPS
1. Go to [Hostinger VPS](https://hostinger.com/vps-hosting)
2. Select VPS plan (KVM 2 or higher recommended)
3. Choose Ubuntu 22.04 LTS
4. Complete purchase and note down:
   - **Server IP address**
   - **Root password** (sent via email)

## Step 1: Initial Server Setup

### Connect to Your VPS
```bash
# From your local machine
ssh root@YOUR_SERVER_IP

# Enter the password when prompted
```

### Update System
```bash
# Update package lists
apt update && apt upgrade -y

# Install essential tools
apt install -y curl wget git nano htop ufw
```

### Create Non-Root User (Optional but Recommended)
```bash
# Create new user
adduser apiuser

# Add to sudo group
usermod -aG sudo apiuser

# Switch to new user
su - apiuser
```

## Step 2: Install Docker

### Install Docker Engine
```bash
# Update package index
sudo apt-get update

# Install packages to allow apt to use repository over HTTPS
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group (avoid sudo for docker commands)
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
exit
ssh apiuser@YOUR_SERVER_IP  # or just ssh root@YOUR_SERVER_IP
```

### Verify Docker Installation
```bash
# Test Docker
docker --version
docker run hello-world

# Test Docker Compose
docker compose version
```

## Step 3: Deploy the API

### Clone and Setup
```bash
# Create application directory
mkdir -p /home/apiuser/mailbox-api
cd /home/apiuser/mailbox-api

# Create the API files directly on server
```

### Create API Files on Server

#### 1. Create app.py
```bash
nano app.py
```
Copy and paste the entire content from the `API/app.py` file.

#### 2. Create requirements.txt
```bash
nano requirements.txt
```
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
```

#### 3. Create Dockerfile
```bash
nano Dockerfile
```
Copy and paste the entire content from the `API/Dockerfile` file.

#### 4. Create docker-compose.yml
```bash
nano docker-compose.yml
```
Copy and paste the entire content from the `API/docker-compose.yml` file.

### Build and Start the API
```bash
# Build the API container
docker compose build

# Start the services
docker compose up -d

# Check if running
docker compose ps

# View logs
docker compose logs -f mailbox-api
```

### Verify Deployment
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test from outside (replace with your server IP)
curl http://YOUR_SERVER_IP:8000/health
```

## Step 4: Configure Firewall

### Setup UFW (Uncomplicated Firewall)
```bash
# Enable UFW
sudo ufw enable

# Allow SSH (IMPORTANT: Don't lock yourself out!)
sudo ufw allow ssh
sudo ufw allow 22

# Allow API port
sudo ufw allow 8000

# Allow HTTP and HTTPS (optional, for future web interface)
sudo ufw allow 80
sudo ufw allow 443

# Check status
sudo ufw status
```

## Step 5: Setup Automatic Startup

### Create Systemd Service (Alternative to docker-compose)
```bash
# Create service file
sudo nano /etc/systemd/system/mailbox-api.service
```

```ini
[Unit]
Description=Mailbox Creator API
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/apiuser/mailbox-api
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable mailbox-api.service
sudo systemctl start mailbox-api.service

# Check status
sudo systemctl status mailbox-api.service
```

## Step 6: Domain Setup (Optional)

### Point Domain to Your VPS
If you have a domain (e.g., `api.yourdomain.com`):

1. **In your domain registrar**:
   - Create an A record: `api.yourdomain.com` → `YOUR_SERVER_IP`

2. **Install Nginx (reverse proxy)**:
```bash
sudo apt install -y nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/mailbox-api
```

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/mailbox-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Allow Nginx through firewall
sudo ufw allow 'Nginx Full'
```

3. **Setup SSL with Let's Encrypt**:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

## Step 7: Testing the Deployment

### Test API Endpoints
```bash
# Health check
curl http://YOUR_SERVER_IP:8000/health

# Test mailbox creation (replace with real data)
curl -X POST "http://YOUR_SERVER_IP:8000/create-mailboxes" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "test.com",
    "sender_name": "John Doe",
    "password": "TestPass123!",
    "variations": 3
  }'

# Check container status (use container_id from above response)
curl http://YOUR_SERVER_IP:8000/status/CONTAINER_ID
```

## Step 8: Monitoring and Maintenance

### View API Logs
```bash
# Real-time logs
docker compose logs -f mailbox-api

# Last 100 lines
docker compose logs --tail=100 mailbox-api
```

### Monitor System Resources
```bash
# Check disk space
df -h

# Check memory usage
free -h

# Check CPU usage
htop

# Check Docker containers
docker ps -a
```

### Cleanup Old Containers
```bash
# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -f

# Remove unused volumes
docker volume prune -f
```

### Automatic Cleanup Script
```bash
# Create cleanup script
nano /home/apiuser/cleanup.sh
```

```bash
#!/bin/bash
# Cleanup old containers and images
docker container prune -f
docker image prune -f
docker volume prune -f

# Remove containers older than 24 hours
docker ps -a --filter "name=mailbox-creator-" --filter "status=exited" --format "{{.Names}}" | while read container; do
    created=$(docker inspect --format='{{.Created}}' "$container")
    created_timestamp=$(date -d "$created" +%s)
    current_timestamp=$(date +%s)
    age=$((current_timestamp - created_timestamp))
    
    # 86400 seconds = 24 hours
    if [ $age -gt 86400 ]; then
        echo "Removing old container: $container"
        docker rm "$container"
    fi
done
```

```bash
# Make executable
chmod +x /home/apiuser/cleanup.sh

# Add to crontab (run daily at 2 AM)
crontab -e
```

Add this line:
```
0 2 * * * /home/apiuser/cleanup.sh > /dev/null 2>&1
```

## Step 9: Security Hardening

### Change SSH Port (Optional)
```bash
sudo nano /etc/ssh/sshd_config
```
Change `Port 22` to `Port 2222` (or any other port)

```bash
sudo systemctl restart ssh
sudo ufw allow 2222
sudo ufw delete allow 22
```

### Install Fail2Ban
```bash
sudo apt install -y fail2ban

# Configure
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Step 10: API Integration with Clay.com

Your API is now available at:
- **Direct IP**: `http://YOUR_SERVER_IP:8000`
- **With domain**: `https://api.yourdomain.com` (if you set up domain)

### Clay.com Setup
Use these endpoints in Clay.com HTTP enrichments:

1. **Create Mailboxes**: `POST /create-mailboxes`
2. **Check Status**: `GET /status/{container_id}`
3. **Health Check**: `GET /health`

## Troubleshooting

### API Not Starting
```bash
# Check Docker logs
docker compose logs mailbox-api

# Check if port is available
sudo netstat -tulpn | grep :8000

# Restart services
docker compose down
docker compose up -d
```

### PowerShell Containers Failing
```bash
# Check if PowerShell image exists
docker images | grep powershell

# Pull manually if needed
docker pull mcr.microsoft.com/powershell:latest

# Check container logs
docker logs CONTAINER_NAME
```

### High Memory Usage
```bash
# Check container resource usage
docker stats

# Restart API if needed
docker compose restart mailbox-api
```

## Costs Summary

- **Hostinger VPS (KVM 4)**: ~$7-12/month
- **Domain (optional)**: ~$10/year
- **SSL Certificate**: Free (Let's Encrypt)

**Total monthly cost**: ~$7-12 for a fully functional API server.

## Support

For issues:
1. Check logs: `docker compose logs mailbox-api`
2. Verify firewall: `sudo ufw status`
3. Test containers: `docker ps -a`
4. Monitor resources: `htop` and `df -h` 