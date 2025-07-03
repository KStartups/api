# EasyPanel Deployment Guide (Recommended)

EasyPanel is a **much simpler alternative** to manual Docker deployment. It provides a web UI for managing containers and handles SSL, domains, and deployment automatically.

## Why EasyPanel > Manual Docker?

| Feature | Manual Docker | EasyPanel | Winner |
|---------|---------------|-----------|--------|
| **Setup Time** | 30+ minutes | 5 minutes | 🟢 EasyPanel |
| **Web UI** | Command line only | Beautiful dashboard | 🟢 EasyPanel |
| **SSL Setup** | Manual Let's Encrypt | Automatic | 🟢 EasyPanel |
| **Domain Management** | Manual Nginx config | Built-in | 🟢 EasyPanel |
| **Updates** | Manual rebuild | One-click | 🟢 EasyPanel |
| **Monitoring** | Manual commands | Built-in graphs | 🟢 EasyPanel |
| **Cost** | Same | Same | 🟰 Equal |

## Prerequisites

### Hostinger VPS (or any VPS)
- **Minimum**: 2GB RAM, 2 CPU cores, 40GB SSD
- **Recommended**: 4GB RAM, 4 CPU cores, 80GB SSD
- **OS**: Ubuntu 20.04 or 22.04 LTS
- **Fresh server** (EasyPanel installs everything)

## Step 1: Install EasyPanel

### Connect to Your VPS
```bash
ssh root@YOUR_SERVER_IP
```

### One-Command EasyPanel Installation
```bash
curl -sSL https://get.easypanel.io | sh
```

This single command:
- ✅ Installs Docker automatically
- ✅ Sets up EasyPanel dashboard  
- ✅ Configures reverse proxy
- ✅ Sets up SSL management
- ✅ Creates admin user

### Access EasyPanel Dashboard
1. **Open browser**: `https://YOUR_SERVER_IP`
2. **Create admin account** (first time only)
3. **Login** to EasyPanel dashboard

## Step 2: Deploy Mailbox API

### Create New Service
1. **Click** "Services" in EasyPanel dashboard
2. **Click** "Create Service"
3. **Choose** "From Source Code"

### Configuration
**Basic Settings:**
- **Name**: `mailbox-api`
- **Repository**: Upload your API folder or use Git
- **Build Method**: `Dockerfile`
- **Port**: `8000`

**Advanced Settings:**
- **Enable** "Auto Deploy"
- **Enable** "Health Checks"
- **Set** Health Check URL: `/health`

### Environment Variables
Add these in EasyPanel:
```bash
PYTHONUNBUFFERED=1
```

### Volumes (Critical)
In EasyPanel dashboard, add these volumes:
```
/var/run/docker.sock:/var/run/docker.sock
/tmp/mailbox_scripts:/tmp/mailbox_scripts
```

**Why this matters**: The API needs Docker socket access to create PowerShell containers.

### Deploy
1. **Click** "Deploy"
2. **Wait** for build to complete (~2-3 minutes)
3. **Check** logs in EasyPanel dashboard

## Step 3: Setup Domain (Optional)

### Using Custom Domain
If you have a domain (e.g., `api.yourdomain.com`):

1. **In your domain registrar**:
   - Create A record: `api.yourdomain.com` → `YOUR_SERVER_IP`

2. **In EasyPanel dashboard**:
   - Go to your `mailbox-api` service
   - Click "Domains" tab
   - Add domain: `api.yourdomain.com`
   - **Enable SSL** (automatic Let's Encrypt)

### Using Subdomain
EasyPanel provides free subdomains:
1. In service settings, choose "Generate Subdomain"
2. Get something like: `mailbox-api-abc123.easypanel.host`
3. SSL is automatic

## Step 4: Test Deployment

### Health Check
```bash
# Test with your domain/subdomain
curl https://api.yourdomain.com/health

# Or with IP (if no domain)
curl https://YOUR_SERVER_IP/health
```

### Test Mailbox Creation
```bash
curl -X POST "https://api.yourdomain.com/create-mailboxes" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "test.com",
    "sender_name": "John Doe", 
    "password": "TestPass123!",
    "variations": 3
  }'
```

## Step 5: EasyPanel Dashboard Features

### Service Monitoring
- **CPU/RAM usage** graphs
- **Request logs** in real-time
- **Container status** indicators
- **Health check** results

### Log Viewing
- **Real-time logs** for API service
- **Filter by** timestamp or level
- **Download logs** for debugging

### One-Click Updates
1. **Push code** to repository
2. **Click "Deploy"** in EasyPanel
3. **Zero-downtime** deployment

### SSL Management
- **Automatic renewal** of Let's Encrypt certificates
- **Force HTTPS** redirects
- **SSL status** monitoring

## Step 6: Configure Firewall (Auto-Handled)

EasyPanel **automatically configures**:
- ✅ Port 80 (HTTP) - redirects to HTTPS
- ✅ Port 443 (HTTPS) - main API access
- ✅ Port 3001 (EasyPanel dashboard)
- ✅ Port 22 (SSH) - kept open for admin

**You don't need to manually configure UFW or iptables.**

## Step 7: Clay.com Integration

Your API is now available at:
- **With domain**: `https://api.yourdomain.com`
- **With EasyPanel subdomain**: `https://mailbox-api-abc123.easypanel.host`
- **Direct IP**: `https://YOUR_SERVER_IP` (with SSL)

### Use in Clay.com
Follow the same workflow from `CLAY_INTEGRATION.md`, but with your EasyPanel URL:

```json
{
  "endpoint": "https://api.yourdomain.com/create-mailboxes",
  "method": "POST",
  "headers": {"Content-Type": "application/json"}
}
```

## Step 8: Advanced EasyPanel Features

### Service Templates
Save your configuration as a template for easy redeployment:
1. **Service Settings** → **Export Template**
2. **Save** configuration JSON
3. **Import** on other servers instantly

### Backup & Restore
- **Automatic backups** of service configurations
- **One-click restore** from previous versions
- **Export/import** services between servers

### Multiple Environments
Deploy different versions:
- **Production**: `api.yourdomain.com`
- **Staging**: `staging-api.yourdomain.com`
- **Development**: `dev-api.yourdomain.com`

### Resource Limits
Set container limits in EasyPanel:
- **Memory limit**: 2GB (prevents OOM)
- **CPU limit**: 2 cores
- **Auto-restart** on failures

## Step 9: Monitoring & Maintenance

### EasyPanel Dashboard
Access at: `https://YOUR_SERVER_IP:3001`

**Key Metrics:**
- Service uptime
- Response times
- Memory/CPU usage
- Request count
- Error rates

### Container Management
- **View logs** in real-time
- **Restart services** with one click
- **Scale containers** up/down
- **Monitor resource usage**

### Automatic Updates
```bash
# EasyPanel auto-updates itself
# Your API auto-deploys on code changes
# SSL certificates auto-renew
```

## Step 10: Scaling & Performance

### Vertical Scaling (Upgrade VPS)
1. **Upgrade** Hostinger VPS to higher tier
2. **Restart** EasyPanel services
3. **Update** resource limits in dashboard

### Horizontal Scaling (Multiple Instances)
1. **Deploy** to multiple VPS servers
2. **Use** load balancer (Cloudflare, etc.)
3. **Share** database if needed

### Performance Optimization
- **Enable** container caching
- **Set** resource limits appropriately
- **Monitor** and tune based on usage

## Troubleshooting

### Service Won't Start
1. **Check logs** in EasyPanel dashboard
2. **Verify** Docker socket volume is mounted
3. **Restart** service from dashboard

### SSL Issues
1. **Check domain** DNS propagation
2. **Regenerate** SSL certificate in EasyPanel
3. **Verify** port 80/443 are accessible

### High Resource Usage
1. **Check** active containers: Dashboard → System → Containers
2. **Set** memory limits on services
3. **Clean up** old containers automatically

### API Not Accessible
1. **Verify** service is running (green status)
2. **Check** domain configuration
3. **Test** health endpoint: `/health`

## Cost Comparison

### EasyPanel Deployment
- **Hostinger VPS**: $7-12/month
- **Domain**: $10/year (optional)
- **EasyPanel**: Free
- **SSL**: Free (auto Let's Encrypt)
- **Total**: **$7-12/month**

### Manual Docker Deployment
- **Same cost** but **much more work**

## Migration from Manual Docker

Already deployed manually? Switch to EasyPanel:

1. **Install EasyPanel** on same server
2. **Import** existing containers
3. **Configure** through dashboard
4. **Remove** manual configs

## Why EasyPanel Wins

### For Non-DevOps People
- 🎯 **Visual dashboard** vs command line
- 🔄 **One-click deployments** vs manual rebuilds
- 📊 **Built-in monitoring** vs manual tools
- 🔒 **Automatic SSL** vs manual setup
- 🛡️ **Security updates** handled automatically

### For Scaling
- 📈 **Resource monitoring** built-in
- ⚡ **Performance graphs** show bottlenecks
- 🔧 **Easy resource adjustments**
- 📋 **Service templates** for quick scaling

### For Maintenance
- 🔄 **Auto-restart** failed services
- 📝 **Centralized logs** with search
- 🛠️ **One-click updates**
- 💾 **Automatic backups**

## Summary

**EasyPanel gives you everything from HOSTINGER_DEPLOYMENT.md but with:**
- ✅ **5-minute setup** instead of 30 minutes
- ✅ **Web dashboard** instead of SSH commands
- ✅ **Automatic SSL** instead of manual setup
- ✅ **Built-in monitoring** instead of manual tools
- ✅ **One-click updates** instead of rebuild scripts

**Perfect for your mailbox API deployment!**

---

**Ready to deploy?** Just run: `curl -sSL https://get.easypanel.io | sh` 