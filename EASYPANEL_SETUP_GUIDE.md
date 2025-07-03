# EasyPanel Step-by-Step Setup Guide

## Method: Upload Source Code (Recommended)

You'll upload your `API/` folder and EasyPanel will automatically detect the `Dockerfile` and build it.

## Step 1: Install EasyPanel

```bash
# SSH to your VPS
ssh root@YOUR_SERVER_IP

# Install EasyPanel (one command)
curl -sSL https://get.easypanel.io | sh
```

Wait 2-3 minutes for installation to complete.

## Step 2: Access EasyPanel Dashboard

1. **Open browser**: Go to `https://YOUR_SERVER_IP`
2. **Create admin account** (first time only):
   - Email: your-email@domain.com
   - Password: strong-password
   - Click "Create Account"

## Step 3: Create New Service

### In EasyPanel Dashboard:

1. **Click "Services"** (left sidebar)
2. **Click "Create Service"** (blue button)
3. **Choose "Source"** (not Docker Registry)

## Step 4: Configure Service

### Basic Configuration Tab:

**Name**: `mailbox-api`
**Source Type**: Choose **"Archive"** (this lets you upload files)

### Upload Your Files:

1. **Zip your API folder** on your computer:
   ```
   API/
   ├── app.py
   ├── Dockerfile  
   ├── requirements.txt
   ├── docker-compose.yml (not needed for EasyPanel)
   └── other files...
   ```
   
2. **Create ZIP file** called `api.zip`

3. **In EasyPanel**: Click **"Upload Archive"**

4. **Select your `api.zip`** file

5. **Click Upload** and wait for it to process

### Build Configuration:

**Build Type**: Select **"Dockerfile"**
**Dockerfile Path**: Leave as `Dockerfile` (EasyPanel will find it)
**Build Context**: Leave as `.` (current directory)

## Step 5: Configure Service Settings

### Environment Tab:
Add this environment variable:
- **Key**: `PYTHONUNBUFFERED`  
- **Value**: `1`

### Networking Tab:
- **Port**: `8000`
- **Protocol**: `HTTP`

### Volumes Tab (CRITICAL):
Add these two volumes:

**Volume 1:**
- **Host Path**: `/var/run/docker.sock`
- **Container Path**: `/var/run/docker.sock`
- **Type**: `Bind`

**Volume 2:**
- **Host Path**: `/tmp/mailbox_scripts`
- **Container Path**: `/tmp/mailbox_scripts`  
- **Type**: `Bind`

**Why volumes matter**: Your API needs Docker access to create PowerShell containers.

### Health Check Tab:
- **Enable Health Check**: ✅ ON
- **Health Check Path**: `/health`
- **Health Check Interval**: `30` seconds

## Step 6: Deploy

1. **Click "Deploy"** (blue button at top right)
2. **Wait for build** (2-3 minutes first time)
3. **Watch logs** in the "Logs" tab

### Build Process:
```
📦 Uploading source code...
🔨 Building Docker image...
🚀 Starting container...
✅ Service running!
```

## Step 7: Test Your API

### Get Your URL:
EasyPanel will show your service URL in the dashboard, something like:
- `https://mailbox-api-abc123.easypanel.host` (auto-generated subdomain)
- Or `https://YOUR_SERVER_IP` if no domain

### Test Health Endpoint:
```bash
curl https://your-easypanel-url/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "message": "Simple Mailbox Creator API",
  "version": "1.0.0",
  "timestamp": "2024-12-01T14:30:22.123456"
}
```

### Test Mailbox Creation:
```bash
curl -X POST "https://your-easypanel-url/create-mailboxes" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "test.com",
    "sender_name": "John Doe",
    "password": "TestPass123!",
    "variations": 3
  }'
```

## Step 8: Add Custom Domain (Optional)

### If you have a domain:

1. **In your domain registrar**:
   - Add A record: `api.yourdomain.com` → `YOUR_SERVER_IP`

2. **In EasyPanel dashboard**:
   - Go to your `mailbox-api` service
   - Click **"Domains"** tab
   - Click **"Add Domain"**
   - Enter: `api.yourdomain.com`
   - **Enable SSL**: ✅ ON (automatic)
   - Click **"Add"**

SSL will be automatic via Let's Encrypt.

## Step 9: Monitor & Manage

### EasyPanel Dashboard Features:
- **📊 Metrics**: CPU, RAM, network usage
- **📝 Logs**: Real-time container logs  
- **🔄 Restart**: One-click service restart
- **⚙️ Settings**: Update environment variables
- **🔧 Deploy**: Update code with one click

### View Logs:
1. **Go to your service** in EasyPanel
2. **Click "Logs" tab**
3. **See real-time output** from your API

### Update Your Code:
1. **Make changes** to your local files
2. **Create new ZIP** with updated files
3. **Upload new archive** in EasyPanel
4. **Click "Deploy"**
5. **Zero-downtime update**

## Troubleshooting

### "Service won't start"
**Check**: Logs tab shows error details
**Fix**: Usually missing environment variables or volume mounts

### "Can't create containers"
**Check**: Docker socket volume is mounted correctly
**Fix**: Verify `/var/run/docker.sock:/var/run/docker.sock` in Volumes tab

### "Health check failing"
**Check**: API is listening on port 8000
**Fix**: Verify `uvicorn app:app --host 0.0.0.0 --port 8000` in your code

### "Build failing"
**Check**: Dockerfile syntax and requirements.txt
**Fix**: Test locally first: `docker build -t test .`

## Alternative: Git Repository Method

### If you prefer Git:

1. **Push your API folder** to GitHub/GitLab
2. **In EasyPanel**: Choose **"Git Repository"** instead of Archive
3. **Enter repository URL**: `https://github.com/yourusername/yourrepo`
4. **Branch**: `main` (or your branch)
5. **Build Path**: `/` (root)
6. **Same configuration** as above (volumes, environment, etc.)

**Benefit**: Auto-deploy when you push to Git

## Files You Need in ZIP

### Essential Files:
```
api.zip:
├── app.py              ← Main FastAPI application
├── Dockerfile          ← EasyPanel uses this to build
├── requirements.txt    ← Python dependencies
└── README.md          ← Optional documentation
```

### NOT Needed for EasyPanel:
- `docker-compose.yml` (EasyPanel handles orchestration)
- `.env` files (use Environment tab instead)
- Build scripts (EasyPanel builds automatically)

## Summary

**You use "Source Code" method because:**
✅ You have local files (not a Docker image)
✅ EasyPanel detects Dockerfile automatically  
✅ Easier than setting up Git repository
✅ Can upload directly via web interface

**EasyPanel handles:**
✅ Docker build process
✅ Container orchestration
✅ SSL certificate management
✅ Health checks and monitoring
✅ Service discovery

Your API will be running with full domain isolation and ready for Clay.com integration! 