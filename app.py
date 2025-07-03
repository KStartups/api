from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import tempfile
import os
import re
import json
import asyncio
import uuid
from typing import Optional, List
import logging
from datetime import datetime

app = FastAPI(title="Simple Mailbox Creator API", version="1.0.0")

class MailboxRequest(BaseModel):
    domain: str
    sender_name: str
    password: str
    variations: int = 10
    proxy_endpoint: Optional[str] = None  # Optional proxy for this domain

class MailboxResponse(BaseModel):
    success: bool
    container_id: str
    status: str
    auth_code: Optional[str] = None
    auth_url: str = "https://microsoft.com/devicelogin"
    created_mailboxes: Optional[List[str]] = None
    failed_mailboxes: Optional[List[str]] = None
    logs: Optional[str] = None

def generate_email_variations(first_name: str, last_name: str, count: int) -> List[str]:
    """Generate email variations - simplified from original logic"""
    variations = []
    base_combinations = [
        f"{first_name}.{last_name}",
        f"{first_name[0]}.{last_name}",
        f"{first_name}.{last_name[0]}",
        f"{first_name}{last_name}",
        f"{first_name[0]}{last_name}",
        f"{first_name}{last_name[0]}",
        f"{last_name}.{first_name}",
        f"{last_name}{first_name}",
    ]
    
    # Add numbered variations if needed
    for i, base in enumerate(base_combinations):
        if len(variations) >= count:
            break
        variations.append(base.lower())
        
        # Add numbered versions
        for num in range(1, 10):
            if len(variations) >= count:
                break
            variations.append(f"{base.lower()}{num}")
    
    return variations[:count]

@app.post("/create-mailboxes", response_model=MailboxResponse)
async def create_mailboxes(request: MailboxRequest):
    """
    Create mailboxes for a domain in an isolated container.
    Each domain gets its own container for proxy isolation.
    """
    
    # Parse sender name
    name_parts = request.sender_name.strip().split()
    if len(name_parts) < 2:
        raise HTTPException(400, "Sender name must include first and last name")
    
    first_name = name_parts[0]
    last_name = " ".join(name_parts[1:])
    
    # Generate email variations
    variations = generate_email_variations(first_name, last_name, request.variations)
    
    # Create PowerShell script for this domain
    ps_script = create_powershell_script(
        variations=variations,
        domain=request.domain,
        password=request.password,
        first_name=first_name,
        last_name=last_name
    )
    
    # Start isolated container for this domain
    container_id = await start_domain_container(
        domain=request.domain,
        ps_script=ps_script,
        proxy_endpoint=request.proxy_endpoint
    )
    
    return MailboxResponse(
        success=True,
        container_id=container_id,
        status="container_started",
        auth_url="https://microsoft.com/devicelogin"
    )

@app.get("/status/{container_id}", response_model=MailboxResponse)
async def get_container_status(container_id: str):
    """
    Get status of a specific domain container.
    Returns auth code when available, final results when complete.
    """
    
    try:
        # Get container logs
        result = subprocess.run(
            ["docker", "logs", container_id],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise HTTPException(404, f"Container {container_id} not found")
        
        logs = result.stdout + result.stderr
        
        # Parse current status from logs
        status = parse_container_status(logs)
        auth_code = extract_auth_code(logs)
        created, failed = parse_final_results(logs)
        
        # Check if container is still running
        status_result = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name={container_id}"],
            capture_output=True,
            text=True
        )
        
        is_running = bool(status_result.stdout.strip())
        
        # Determine overall status
        if "AUTH_CODE:" in logs and not auth_code:
            # Extract auth code
            auth_code = extract_auth_code(logs)
            current_status = "waiting_for_auth"
        elif "AUTH_SUCCESS:" in logs:
            current_status = "creating_mailboxes"
        elif "AUTH_TIMEOUT:" in logs:
            current_status = "auth_timeout"
        elif not is_running:
            if created or failed:
                current_status = "completed"
            else:
                current_status = "failed"
        else:
            current_status = "starting"
        
        return MailboxResponse(
            success=True,
            container_id=container_id,
            status=current_status,
            auth_code=auth_code,
            created_mailboxes=created,
            failed_mailboxes=failed,
            logs=logs
        )
        
    except subprocess.TimeoutExpired:
        raise HTTPException(408, "Timeout getting container status")
    except Exception as e:
        raise HTTPException(500, f"Error checking status: {str(e)}")

@app.delete("/containers/{container_id}")
async def cleanup_container(container_id: str):
    """Clean up a specific container"""
    try:
        # Stop and remove container
        subprocess.run(["docker", "stop", container_id], timeout=10)
        subprocess.run(["docker", "rm", container_id], timeout=10)
        
        return {"success": True, "message": f"Container {container_id} cleaned up"}
    except Exception as e:
        raise HTTPException(500, f"Error cleaning up container: {str(e)}")

@app.get("/containers")
async def list_active_containers():
    """List all active mailbox creator containers"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=mailbox-creator-", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return {"containers": result.stdout.split('\n')[1:]}  # Skip header
    except Exception as e:
        raise HTTPException(500, f"Error listing containers: {str(e)}")

def create_powershell_script(variations: List[str], domain: str, password: str, first_name: str, last_name: str) -> str:
    """Create PowerShell script for isolated domain processing"""
    
    mailbox_commands = []
    display_name = f"{first_name} {last_name}"
    
    for variation in variations:
        email = f"{variation}@{domain}"
        mailbox_commands.append(f"""
try {{
    $result = New-Mailbox -Name "{variation}" -DisplayName "{display_name}" -PrimarySmtpAddress "{email}" -Shared -Password (ConvertTo-SecureString "{password}" -AsPlainText -Force) -ResetPasswordOnNextLogon $false -ErrorAction Stop
    Write-Host "SUCCESS: Created mailbox {email}" -ForegroundColor Green
}} catch {{
    Write-Host "FAILED: Could not create {email} - $_" -ForegroundColor Red
}}""")
    
    script = f"""
# Isolated Mailbox Creation Script for {domain}
Write-Host "=== STARTING MAILBOX CREATION FOR {domain.upper()} ===" -ForegroundColor Cyan
Write-Host "Container ID: $env:HOSTNAME" -ForegroundColor Gray
Write-Host "Timestamp: $(Get-Date)" -ForegroundColor Gray

# Install and Import Exchange Online module
Write-Host "Installing ExchangeOnlineManagement module..." -ForegroundColor Yellow
Install-Module -Name ExchangeOnlineManagement -Force -AllowClobber -Scope CurrentUser

Write-Host "Importing ExchangeOnlineManagement module..." -ForegroundColor Yellow
Import-Module ExchangeOnlineManagement -Force

# Connect to Exchange Online with device authentication
Write-Host "Connecting to Exchange Online for domain: {domain}" -ForegroundColor Yellow
Write-Host "This will generate an authentication code..." -ForegroundColor Yellow

try {{
    # Capture the connection output to extract auth code
    $connectOutput = Connect-ExchangeOnline -Device 2>&1
    
    # Parse and display the auth code clearly
    $authCode = ""
    $authCodeFound = $false
    
    foreach ($line in $connectOutput) {{
        $lineStr = $line.ToString()
        
        # Look for various auth code patterns
        if ($lineStr -match "enter the code ([A-Z0-9]{{6,}}) to authenticate") {{
            $authCode = $matches[1]
            $authCodeFound = $true
        }}
        elseif ($lineStr -match "Code: ([A-Z0-9]{{6,}})") {{
            $authCode = $matches[1]
            $authCodeFound = $true
        }}
        elseif ($lineStr -match "([A-Z0-9]{{9}})") {{
            $authCode = $matches[1]
            $authCodeFound = $true
        }}
        
        if ($authCodeFound) {{
            break
        }}
    }}
    
    if ($authCode) {{
        Write-Host ""
        Write-Host "AUTH_CODE: $authCode" -ForegroundColor Yellow
        Write-Host "Please visit https://microsoft.com/devicelogin and enter: $authCode" -ForegroundColor Yellow
        Write-Host ""
    }} else {{
        Write-Host "ERROR: Could not extract authentication code from output" -ForegroundColor Red
        Write-Host "Raw output: $connectOutput" -ForegroundColor Gray
        exit 1
    }}
    
    # Poll for authentication success
    Write-Host "Waiting for authentication to complete..." -ForegroundColor Cyan
    $authComplete = $false
    $attempts = 0
    $maxAttempts = 60  # 15 minutes (15 second intervals)
    
    while (-not $authComplete -and $attempts -lt $maxAttempts) {{
        Start-Sleep -Seconds 15
        $attempts++
        
        Write-Host "AUTH_POLLING: Attempt $attempts/$maxAttempts - checking authentication status..." -ForegroundColor Gray
        
        try {{
            # Test authentication by trying to get mailboxes
            $null = Get-Mailbox -ResultSize 1 -ErrorAction Stop
            $authComplete = $true
            Write-Host "AUTH_SUCCESS: Authentication completed successfully!" -ForegroundColor Green
        }} catch {{
            Write-Host "AUTH_WAITING: Still waiting for authentication... (attempt $attempts/$maxAttempts)" -ForegroundColor Yellow
        }}
    }}
    
    if (-not $authComplete) {{
        Write-Host "AUTH_TIMEOUT: Authentication not completed within 15 minutes" -ForegroundColor Red
        Write-Host "Please restart the process if you completed authentication" -ForegroundColor Red
        exit 1
    }}
    
    # Authentication successful - now create mailboxes
    Write-Host ""
    Write-Host "=== CREATING MAILBOXES ===" -ForegroundColor Green
    Write-Host "Creating {len(variations)} mailboxes for domain: {domain}" -ForegroundColor Cyan
    Write-Host ""
    
    {chr(10).join(mailbox_commands)}
    
    Write-Host ""
    Write-Host "=== MAILBOX CREATION COMPLETED ===" -ForegroundColor Green
    Write-Host "Check the SUCCESS/FAILED messages above for individual results" -ForegroundColor Cyan
    
}} catch {{
    Write-Host "ERROR: Failed to connect to Exchange Online: $_" -ForegroundColor Red
    exit 1
}}
"""
    
    return script

async def start_domain_container(domain: str, ps_script: str, proxy_endpoint: Optional[str] = None) -> str:
    """Start an isolated container for a specific domain"""
    
    # Create temporary script file
    script_dir = "/tmp/mailbox_scripts"
    os.makedirs(script_dir, exist_ok=True)
    
    # Generate unique container name for this domain
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    container_name = f"mailbox-creator-{domain.replace('.', '-')}-{timestamp}"
    
    script_path = os.path.join(script_dir, f"{container_name}.ps1")
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(ps_script)
    
    try:
        # Build Docker command with proxy if provided
        cmd = [
            "docker", "run", "-d", "--name", container_name,
            "-v", f"{script_path}:/script.ps1:ro",
        ]
        
        # Add proxy configuration if provided
        if proxy_endpoint:
            cmd.extend([
                "-e", f"ALL_PROXY={proxy_endpoint}",
                "-e", f"HTTP_PROXY={proxy_endpoint}",
                "-e", f"HTTPS_PROXY={proxy_endpoint}"
            ])
        
        # Add PowerShell container
        cmd.extend([
            "mcr.microsoft.com/powershell:latest",
            "pwsh", "-File", "/script.ps1"
        ])
        
        # Start the container
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise Exception(f"Failed to start container: {result.stderr}")
        
        return container_name
        
    except Exception as e:
        # Cleanup temp file on error
        try:
            os.unlink(script_path)
        except:
            pass
        raise e

def extract_auth_code(logs: str) -> Optional[str]:
    """Extract authentication code from PowerShell logs"""
    
    patterns = [
        r"AUTH_CODE: ([A-Z0-9]+)",
        r"enter the code ([A-Z0-9]{6,}) to authenticate",
        r"Code: ([A-Z0-9]{6,})",
        r"([A-Z0-9]{9})"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, logs, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def parse_container_status(logs: str) -> str:
    """Parse current status from container logs"""
    if "AUTH_TIMEOUT:" in logs:
        return "auth_timeout"
    elif "AUTH_SUCCESS:" in logs:
        return "creating_mailboxes"
    elif "AUTH_CODE:" in logs:
        return "waiting_for_auth"
    elif "=== MAILBOX CREATION COMPLETED ===" in logs:
        return "completed"
    elif "ERROR:" in logs:
        return "error"
    else:
        return "starting"

def parse_final_results(logs: str) -> tuple[List[str], List[str]]:
    """Parse final results from logs"""
    created = []
    failed = []
    
    for line in logs.split('\n'):
        if "SUCCESS: Created mailbox" in line:
            # Extract email from success message
            email_match = re.search(r'Created mailbox ([\w\.\-]+@[\w\.\-]+)', line)
            if email_match:
                created.append(email_match.group(1))
        elif "FAILED: Could not create" in line:
            # Extract email from failure message
            email_match = re.search(r'Could not create ([\w\.\-]+@[\w\.\-]+)', line)
            if email_match:
                failed.append(email_match.group(1))
    
    return created, failed

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "message": "Simple Mailbox Creator API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 