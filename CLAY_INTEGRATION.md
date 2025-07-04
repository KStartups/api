# Clay.com Integration Guide

## Quick Start for Clay.com

🚀 **Ready to use API**: `https://yes-app.dqlb47.easypanel.host/`

**TL;DR for Clay.com setup:**
1. Create HTTP enrichment: `POST https://yes-app.dqlb47.easypanel.host/create-mailboxes`
2. Wait 30 seconds, check status: `GET https://yes-app.dqlb47.easypanel.host/status/{{container_id}}`
3. Copy the `auth_code`, go to `microsoft.com/devicelogin`, paste it
4. Wait 60 seconds, check final results with the same status endpoint
5. Each domain gets isolated container + unique auth code (no cross-contamination)

## Overview
This API creates **isolated containers for each domain** to ensure proper proxy hygiene and avoid linking between domains. Each container outputs its own authentication code that must be manually entered at microsoft.com/devicelogin.

## API Workflow

```
1. Clay.com → POST /create-mailboxes → Isolated container starts
2. Clay.com → GET /status/{container_id} → Get auth_code for this domain
3. User → microsoft.com/devicelogin → Enter auth_code manually  
4. Container polls for auth success → Creates mailboxes
5. Clay.com → GET /status/{container_id} → Get final results
```

## Key Features

✅ **Proxy Isolation**: Each domain gets its own container with optional proxy support  
✅ **Unique Auth Codes**: Every domain has its own Microsoft authentication  
✅ **No Cross-Contamination**: Domains can't be linked through shared sessions  
✅ **Parsable Output**: Clean JSON responses for automation  
✅ **Container Cleanup**: Automatic cleanup of old containers  

## Clay.com HTTP Enrichment Setup

### Step 1: Create Mailboxes (Isolated Container)
**HTTP Request:** `POST https://yes-app.dqlb47.easypanel.host/create-mailboxes`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Body:**
```json
{
  "domain": "{{domain}}",
  "sender_name": "{{first_name}} {{last_name}}",
  "password": "Matt123~",
  "variations": 10,
  "proxy_endpoint": "socks5://8jm9GymM9fj1umY_c_US:RNW78Fm5@secret.infrastructure.2.flowproxies.com:10590"
}
```

> **Note**: Email patterns now use professional business variations (no numbered suffixes like email1, email2). Patterns include: firstname.lastname, firstnamelastname, f.lastname, repetitions, vowel insertions, etc.

**Clay.com Response Mapping:**
- `container_id` → Save as `container_id`
- `status` → Save as `status`  
- `success` → Save as `api_success`

### Step 2: Wait & Check for Domain-Specific Auth Code
**HTTP Request:** `GET https://yes-app.dqlb47.easypanel.host/status/{{container_id}}`

**Clay.com Wait Settings:**
- Wait 30 seconds before running
- Retry 3 times with 30-second intervals

**Response Mapping:**
- `auth_code` → Save as `auth_code` (when available)
- `status` → Save as `current_status`
- `auth_url` → Save as `auth_url`

### Step 3: Manual Authentication Step
**When `auth_code` appears:**

1. **Copy the auth code** from Clay.com output
2. **Visit** `https://microsoft.com/devicelogin`
3. **Paste the auth code** for this specific domain
4. **Complete Microsoft authentication**

> **Important**: Each domain has its own unique auth code. Don't mix them up!

### Step 4: Poll for Completion
**HTTP Request:** `GET https://yes-app.dqlb47.easypanel.host/status/{{container_id}}`

**Clay.com Wait Settings:**
- Wait 60 seconds before running
- Retry 10 times with 60-second intervals
- Stop when `status = "completed"`

**Final Response Mapping:**
- `created_mailboxes` → Save as `created_emails` (JSON array)
- `failed_mailboxes` → Save as `failed_emails` (JSON array)
- `status` → Save as `final_status`

## Clay.com Table Setup

### Input Columns
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `domain` | Text | Target domain | "acme.com" |
| `first_name` | Text | Target first name | "John" |
| `last_name` | Text | Target last name | "Doe" |
| `proxy_endpoint` | Text | Optional proxy (per domain) | "socks5://user:pass@proxy:1080" |

### Output Columns
| Column | Type | Description |
|--------|------|-------------|
| `container_id` | Text | Unique container identifier |
| `auth_code` | Text | Microsoft auth code for this domain |
| `current_status` | Text | Processing status |
| `created_emails` | Text | JSON array of successful emails |
| `failed_emails` | Text | JSON array of failed emails |
| `mailbox_count` | Number | Count of successful mailboxes |
| `final_status` | Text | Final processing result |

## Example Clay.com Workflow

```
Row 1: domain="acme.com", first_name="John", last_name="Doe"
Row 2: domain="beta.com", first_name="Jane", last_name="Smith"

1. HTTP Enrichment "Create Mailboxes" (runs on both rows)
   Row 1 → container_id="mailbox-creator-acme-com-20241201_143022"
   Row 2 → container_id="mailbox-creator-beta-com-20241201_143025"

2. HTTP Enrichment "Check Auth Code" (wait 30s, runs on both)
   Row 1 → auth_code="ABC123DEF" (for acme.com)
   Row 2 → auth_code="XYZ789GHI" (for beta.com)

3. Manual step: 
   - Visit microsoft.com/devicelogin
   - Enter "ABC123DEF" for acme.com authentication
   - Enter "XYZ789GHI" for beta.com authentication

4. HTTP Enrichment "Get Results" (wait 60s)
   Row 1 → created_emails=["john.doe@acme.com", "j.doe@acme.com", ...]
   Row 2 → created_emails=["jane.smith@beta.com", "j.smith@beta.com", ...]
```

## Proxy Configuration

### Per-Domain Proxies (Recommended)
```json
{
  "domain": "acme.com",
  "sender_name": "John Doe",
  "password": "SecurePass123!",
  "variations": 10,
  "proxy_endpoint": "socks5://user1:pass1@proxy1.provider.com:1080"
}
```

### Supported Proxy Formats
- `socks5://user:pass@host:port`
- `http://user:pass@host:port`
- `https://user:pass@host:port`

### Proxy Providers
- **Residential Proxies**: SmartProxy, Oxylabs, Bright Data
- **Datacenter Proxies**: ProxyMesh, Storm Proxies
- **Rotating Proxies**: Recommended for better anonymity

## Status Flow

### Container Statuses
1. **`container_started`** → Container is launching
2. **`starting`** → PowerShell is loading
3. **`waiting_for_auth`** → Auth code ready, waiting for manual auth
4. **`creating_mailboxes`** → Auth complete, creating mailboxes
5. **`completed`** → All done, results available
6. **`auth_timeout`** → Auth not completed within 15 minutes
7. **`failed`** → Container failed to start or run

## Error Handling

### Common Issues & Solutions

**`auth_timeout` Status:**
- Microsoft auth wasn't completed within 15 minutes
- **Solution**: Restart the process, complete auth faster

**Empty `auth_code`:**
- Container may still be starting
- **Solution**: Wait 30 seconds and check again

**`failed` Status:**
- Container failed to start or connect to Exchange
- **Solution**: Check API logs, retry with different proxy

**Mixed-up Auth Codes:**
- Using wrong auth code for wrong domain
- **Solution**: Each container has unique auth code, don't mix them

### Clay.com Error Handling
```javascript
// In Clay.com, add conditional logic:
if (status === "auth_timeout") {
  // Mark row for manual retry
  return "RETRY_NEEDED";
} else if (status === "failed") {
  // Mark as failed
  return "FAILED";
} else if (status === "completed") {
  // Success, count mailboxes
  return created_emails.length;
}
```

## Security Best Practices

### Domain Isolation
- ✅ Each domain gets its own container
- ✅ No shared authentication sessions
- ✅ Independent proxy configurations
- ✅ Separate PowerShell processes

### Proxy Hygiene
- 🔄 **Rotate proxies per domain**
- 🌍 **Use residential IPs when possible**
- ⏰ **Add delays between requests**
- 🔀 **Randomize user agents** (if supported by proxy)

### Password Security
- 🔐 Don't store passwords in Clay.com tables
- 💾 Use environment variables on API server
- 🔄 Rotate passwords regularly
- 💪 Use complex passwords

## Advanced Configuration

### Batch Processing
```javascript
// Clay.com can process multiple domains simultaneously
// Each gets its own isolated container automatically
```

### Container Cleanup
The API automatically cleans up containers older than 24 hours:
```bash
# Manual cleanup if needed
curl -X DELETE "https://your-api.com/containers/CONTAINER_ID"
```

### Monitoring
```bash
# Check active containers
curl "https://your-api.com/containers"

# Health check
curl "https://your-api.com/health"
```

## Cost Estimation

### Per Domain Processing
- **Container runtime**: ~5-10 minutes per domain
- **Resources**: ~512MB RAM per container
- **Proxy cost**: $0.10-1.00 per domain (depending on provider)

### Scaling
- **Concurrent domains**: Limited by VPS resources
- **Recommended**: 4GB RAM VPS can handle 5-8 concurrent domains
- **Horizontal scaling**: Deploy multiple API instances

## Testing

### Local Testing
```bash
# Test single domain
curl -X POST "http://localhost:8000/create-mailboxes" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "test.com",
    "sender_name": "Test User",
    "password": "TestPass123!",
    "variations": 3
  }'

# Check status
curl "http://localhost:8000/status/CONTAINER_ID"
```

### Clay.com Testing
1. Start with 1-2 domains
2. Verify auth codes are unique
3. Complete authentication for each domain
4. Verify isolation (no cross-contamination)
5. Scale up once working properly

## Support

### Debugging Steps
1. **Check container logs**: `GET /status/{container_id}` → `logs` field
2. **Verify isolation**: Each domain should have unique container_id
3. **Test auth codes**: Each should be different and work independently
4. **Monitor resources**: Ensure VPS has enough memory for concurrent containers

### Container Naming Pattern
```
mailbox-creator-{domain-with-dashes}-{timestamp}

Examples:
- mailbox-creator-acme-com-20241201_143022
- mailbox-creator-beta-company-com-20241201_143025
```

This ensures each domain is completely isolated and traceable. 