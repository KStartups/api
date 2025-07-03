# Simple Mailbox Creator API

A containerized REST API for creating Exchange Online mailboxes with **domain isolation** and **proxy support**. Built specifically for Clay.com integration and automation workflows.

## 🚀 Key Features

- **🔒 Domain Isolation**: Each domain gets its own isolated container
- **🌐 Proxy Support**: Per-domain proxy configuration for anonymity
- **📱 Device Authentication**: Microsoft device flow with parsable auth codes
- **🤖 Clay.com Ready**: REST API designed for automation
- **🐳 Docker Based**: Easy deployment on any VPS
- **🧹 Auto Cleanup**: Automatic container cleanup after 24 hours

## 📁 Project Structure

```
API/
├── app.py                  # Main FastAPI application
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Docker Compose for easy deployment
├── requirements.txt        # Python dependencies
├── HOSTINGER_DEPLOYMENT.md # Complete VPS deployment guide
├── CLAY_INTEGRATION.md     # Clay.com integration documentation
└── README.md              # This file
```

## 🔄 Architecture

```
Clay.com → API → Isolated PowerShell Container (per domain)
                     ↓
               Microsoft Exchange Online
                     ↓
                Created Mailboxes
```

### Domain Isolation Flow
1. Each domain request creates a **unique container**
2. Container connects to Exchange with **domain-specific proxy**
3. Generates **unique authentication code**
4. Creates mailboxes **independently**
5. Results returned to Clay.com
6. Container auto-cleaned after 24 hours

## 🚀 Quick Start

### 1. Deploy to VPS (Choose One)
**🟢 Recommended**: **[EASYPANEL_DEPLOYMENT.md](./EASYPANEL_DEPLOYMENT.md)** - 5-minute setup with web UI
**⚙️ Manual**: **[HOSTINGER_DEPLOYMENT.md](./HOSTINGER_DEPLOYMENT.md)** - Full control but more work

### 2. Test the API
```bash
# Health check
curl http://YOUR_SERVER_IP:8000/health

# Create mailboxes
curl -X POST "http://YOUR_SERVER_IP:8000/create-mailboxes" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "sender_name": "John Doe",
    "password": "SecurePass123!",
    "variations": 5
  }'

# Check status
curl "http://YOUR_SERVER_IP:8000/status/CONTAINER_ID"
```

### 3. Integrate with Clay.com
Follow the integration guide: **[CLAY_INTEGRATION.md](./CLAY_INTEGRATION.md)**

## 📊 API Endpoints

### POST `/create-mailboxes`
Start mailbox creation in isolated container.

**Request:**
```json
{
  "domain": "acme.com",
  "sender_name": "John Doe", 
  "password": "SecurePass123!",
  "variations": 10,
  "proxy_endpoint": "socks5://user:pass@proxy:port"
}
```

**Response:**
```json
{
  "success": true,
  "container_id": "mailbox-creator-acme-com-20241201_143022",
  "status": "container_started",
  "auth_url": "https://microsoft.com/devicelogin"
}
```

### GET `/status/{container_id}`
Get container status, auth code, and results.

**Response:**
```json
{
  "success": true,
  "container_id": "mailbox-creator-acme-com-20241201_143022",
  "status": "waiting_for_auth",
  "auth_code": "ABC123DEF",
  "auth_url": "https://microsoft.com/devicelogin",
  "created_mailboxes": ["john.doe@acme.com", "j.doe@acme.com"],
  "failed_mailboxes": [],
  "logs": "Container execution logs..."
}
```

### GET `/containers`
List all active containers.

### DELETE `/containers/{container_id}`
Manually cleanup a specific container.

### GET `/health`
API health check.

## 📋 Status Flow

| Status | Description |
|--------|-------------|
| `container_started` | Container is launching |
| `starting` | PowerShell is loading |
| `waiting_for_auth` | Auth code ready, manual auth needed |
| `creating_mailboxes` | Auth complete, creating mailboxes |
| `completed` | All done, results available |
| `auth_timeout` | Auth not completed within 15 minutes |
| `failed` | Container failed |

## 🔐 Security Features

### Domain Isolation
- ✅ Each domain runs in separate container
- ✅ No shared authentication sessions
- ✅ Independent proxy configurations
- ✅ Isolated PowerShell processes

### Proxy Support
- 🌐 Per-domain proxy configuration
- 🔄 SOCKS5, HTTP, HTTPS proxy support
- 🏠 Residential proxy compatibility
- 🔀 Rotation-friendly architecture

## 🛠️ Development

### Local Development
```bash
# Clone repository
git clone <your-repo>
cd API

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Test endpoints
curl http://localhost:8000/health
```

### Build Docker Image
```bash
# Build
docker build -t mailbox-api .

# Run
docker run -p 8000:8000 -v /var/run/docker.sock:/var/run/docker.sock mailbox-api
```

## 📊 Resource Requirements

### Minimum VPS Specs
- **RAM**: 2GB (4GB recommended)
- **CPU**: 2 cores (4 cores recommended)
- **Storage**: 40GB SSD
- **OS**: Ubuntu 20.04/22.04 LTS

### Resource Usage Per Domain
- **RAM**: ~512MB per active container
- **Runtime**: 5-10 minutes per domain
- **Storage**: ~100MB per container

### Scaling Guidelines
- **4GB VPS**: 5-8 concurrent domains
- **8GB VPS**: 12-15 concurrent domains
- **Horizontal**: Deploy multiple API instances

## 💰 Cost Breakdown

| Component | Cost |
|-----------|------|
| Hostinger VPS (4GB) | $7-12/month |
| Domain (optional) | $10/year |
| SSL Certificate | Free (Let's Encrypt) |
| Proxy (per domain) | $0.10-1.00 |
| **Total** | **~$8-15/month** |

## 🎯 Clay.com Integration Benefits

### vs. Current Complex System
| Feature | Old System | New API | Winner |
|---------|------------|---------|--------|
| **Lines of Code** | 2,907 | ~400 | 🟢 API |
| **Deployment** | Local install | Docker anywhere | 🟢 API |
| **Clay.com Support** | None | Built-in | 🟢 API |
| **Domain Isolation** | No | Yes | 🟢 API |
| **Proxy Support** | Manual | Per-domain | 🟢 API |
| **Maintenance** | Complex | Minimal | 🟢 API |

### Clay.com Workflow
```
1. Upload domain list to Clay.com
2. HTTP Enrichment: Create mailboxes (parallel processing)
3. Get auth codes for each domain
4. Manual authentication step
5. Automated result collection
6. Export created mailboxes
```

## 🐛 Troubleshooting

### Common Issues

**Container not starting:**
```bash
docker compose logs mailbox-api
docker ps -a
```

**Auth code not appearing:**
```bash
curl "http://YOUR_IP:8000/status/CONTAINER_ID"
# Check logs field for errors
```

**High memory usage:**
```bash
docker stats
# Consider upgrading VPS or reducing concurrent domains
```

**Proxy connection issues:**
```bash
# Test proxy separately
curl --proxy socks5://user:pass@proxy:port https://ipinfo.io/ip
```

## 📚 Documentation

- **[EASYPANEL_DEPLOYMENT.md](./EASYPANEL_DEPLOYMENT.md)** - 🟢 **Recommended**: 5-minute deployment with web UI
- **[HOSTINGER_DEPLOYMENT.md](./HOSTINGER_DEPLOYMENT.md)** - Manual Docker deployment guide
- **[CLAY_INTEGRATION.md](./CLAY_INTEGRATION.md)** - Clay.com integration walkthrough
- **[API Reference](#-api-endpoints)** - Endpoint documentation (above)

## 🤝 Support

### Getting Help
1. **Check logs**: `GET /status/{container_id}` → `logs` field
2. **Verify resources**: `docker stats` and `free -h`
3. **Test isolation**: Each domain should have unique container_id
4. **Monitor cleanup**: Old containers auto-removed after 24h

### Debug Commands
```bash
# API logs
docker compose logs -f mailbox-api

# Container stats
docker stats

# System resources
htop
df -h

# Active containers
docker ps --filter "name=mailbox-creator-"
```

## 🔮 Future Enhancements

- [ ] **Webhook support** for Clay.com notifications
- [ ] **Rate limiting** for production use
- [ ] **Authentication** with API keys
- [ ] **Batch processing** optimization
- [ ] **Metrics dashboard** for monitoring
- [ ] **Auto-scaling** based on load

## 📄 License

This project is designed to replace the complex licensing system of the original tool. **No remote licensing, no bricking, just works.**

---

**Ready to deploy?** Start with **[EASYPANEL_DEPLOYMENT.md](./EASYPANEL_DEPLOYMENT.md)** (5 minutes)

**Need Clay.com integration?** Check **[CLAY_INTEGRATION.md](./CLAY_INTEGRATION.md)** 