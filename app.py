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
    """Generate professional business email variations based on real company patterns"""
    variations = []
    
    # Professional business email patterns (no numbers, job titles, or unprofessional suffixes)
    patterns = [
        # Basic combinations
        f"{first_name}.{last_name}",
        f"{first_name}{last_name}",
        f"{last_name}.{first_name}",
        f"{last_name}{first_name}",
        
        # Initial combinations
        f"{first_name[0]}.{last_name}",
        f"{first_name}.{last_name[0]}",
        f"{first_name[0]}{last_name}",
        f"{first_name}{last_name[0]}",
        f"{last_name}.{first_name[0]}",
        f"{last_name}{first_name[0]}",
        f"{first_name[0]}.{first_name[0]}.{last_name}",
        f"{first_name[0]}{first_name[0]}",
        f"{last_name[0]}{last_name[0]}",
        
        # Repetition patterns
        f"{first_name}{first_name}",
        f"{last_name}{last_name}",
        f"{first_name}.{first_name}",
        f"{last_name}.{last_name}",
        
        # Positional variations
        f"{first_name}.{last_name}.{first_name}",
        f"{last_name}.{first_name}.{last_name}",
        f"{first_name[0]}.{first_name}.{last_name}",
        f"{first_name}.{first_name[0]}.{last_name}",
        
        # Vowel insertion patterns (professional variations)
        f"a{first_name}",
        f"{first_name}a",
        f"e{first_name}",
        f"{first_name}e",
        f"i{first_name}",
        f"{first_name}i",
        f"o{first_name}",
        f"{first_name}o",
        f"u{first_name}",
        f"{first_name}u",
        f"a{last_name}",
        f"{last_name}a",
        f"e{last_name}",
        f"{last_name}e",
        f"i{last_name}",
        f"{last_name}i",
        f"o{last_name}",
        f"{last_name}o",
        f"u{last_name}",
        f"{last_name}u",
        
        # Multiple vowel patterns
        f"{first_name}ee",
        f"{first_name}ii",
        f"{first_name}oo",
        f"{first_name}aa",
        f"{last_name}ee",
        f"{last_name}ii", 
        f"{last_name}oo",
        f"{last_name}aa",
        f"{first_name}eee{last_name}",
        f"{first_name}iii{last_name}",
        f"{last_name}iii{first_name}",
        f"{last_name}eee{first_name}",
        
        # Extended combinations
        f"{first_name}.{last_name}.com",
        f"{first_name}.{last_name}.co",
        f"{first_name}{last_name}.mail",
        f"{first_name}{last_name}.biz",
        f"{last_name}.{first_name}.pro",
        
        # Underscore variations
        f"{first_name}_{last_name}",
        f"{last_name}_{first_name}",
        f"{first_name[0]}_{last_name}",
        f"{first_name}_{last_name[0]}",
        
        # Triple combinations
        f"{first_name}.{first_name}.{last_name}",
        f"{last_name}.{last_name}.{first_name}",
        f"{first_name}.{last_name}.{last_name}",
        f"{last_name}.{first_name}.{first_name}",
        
        # Mixed case preservation patterns
        f"{first_name.capitalize()}.{last_name.lower()}",
        f"{first_name.lower()}.{last_name.capitalize()}",
        f"{first_name.upper()}.{last_name.lower()}",
        f"{first_name.lower()}.{last_name.upper()}",
        
        # Abbreviated forms
        f"{first_name[:3]}.{last_name}",
        f"{first_name}.{last_name[:3]}",
        f"{first_name[:3]}{last_name}",
        f"{first_name}{last_name[:3]}",
        f"{first_name[:2]}.{last_name}",
        f"{first_name}.{last_name[:2]}",
        
        # Professional domain-style patterns
        f"{first_name}.{last_name}.office",
        f"{first_name}.{last_name}.corp",
        f"{first_name}.{last_name}.team",
        f"{first_name}.{last_name}.group",
        f"{first_name}.{last_name}.dept",
    ]
    
    # Convert all to lowercase and remove duplicates while preserving order
    seen = set()
    for pattern in patterns:
        clean_pattern = pattern.lower()
        if clean_pattern not in seen and len(variations) < count:
            seen.add(clean_pattern)
            variations.append(clean_pattern)
            
        if len(variations) >= count:
            break
    
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
        elif is_authenticated_from_logs(logs):
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
    Write-Host "Connecting to Exchange Online..." -ForegroundColor Yellow
    
    # Connect to Exchange Online - this will handle auth code display and waiting automatically
    Connect-ExchangeOnline -Device
    
    # If we reach here, authentication was successful
    Write-Host "Authentication successful!" -ForegroundColor Green
    
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
    
    # Generate unique container name for this domain
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    container_name = f"mailbox-creator-{domain.replace('.', '-')}-{timestamp}"
    
    print(f"DEBUG: Starting container for domain: {domain}")
    
    try:
        # Build Docker command for detached container
        cmd = [
            "docker", "run", "-d", "--name", container_name,
        ]
        
        # Add proxy configuration only if provided - TESTING WITHOUT PROXY FIRST
        if proxy_endpoint:
            cmd.extend([
                "-e", f"ALL_PROXY={proxy_endpoint}",
                "-e", f"HTTP_PROXY={proxy_endpoint}",
                "-e", f"HTTPS_PROXY={proxy_endpoint}"
            ])
        else:
            print(f"DEBUG: Running container without proxy for testing")
        
        # Create a wrapper script that executes the main script and ensures output goes to container logs
        wrapper_script = f"""
# Write script to temp file inside container
$scriptContent = @'
{ps_script}
'@

$scriptPath = "/tmp/mailbox_script.ps1"
$scriptContent | Out-File -FilePath $scriptPath -Encoding UTF8

# Execute the script and ensure all output goes to container stdout/stderr
Write-Host "Starting mailbox creation script..." -ForegroundColor Cyan
& $scriptPath 2>&1 | Tee-Object -FilePath "/dev/stdout"
Write-Host "Script execution completed." -ForegroundColor Cyan
"""
        
        # Start container with the wrapper script
        cmd.extend([
            "mcr.microsoft.com/powershell:latest",
            "pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-c", wrapper_script
        ])
        
        # Start the detached container
        print(f"DEBUG: Executing Docker command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise Exception(f"Failed to start container: {result.stderr}")
        
        actual_container_id = result.stdout.strip()
        print(f"DEBUG: Started container: {actual_container_id}")
        
        return container_name
        
    except Exception as e:
        # Cleanup container on error
        try:
            subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, timeout=10)
        except:
            pass
        raise e

def extract_auth_code(logs: str) -> Optional[str]:
    """Extract authentication code from PowerShell logs"""
    
    # More precise patterns to avoid false positives
    patterns = [
        r"AUTH_CODE: ([A-Z0-9]+)",
        r"enter the code ([A-Z0-9]{6,12}) to authenticate",
        r"and enter the code ([A-Z0-9]{6,12}) to authenticate",
        r"Code: ([A-Z0-9]{6,12})",
        r"device.*?code.*?([A-Z0-9]{8,10})",  # More specific context
        r"authentication.*?code.*?([A-Z0-9]{8,10})",  # More specific context
    ]
    
    for pattern in patterns:
        match = re.search(pattern, logs, re.IGNORECASE)
        if match:
            code = match.group(1)
            # Additional validation: real auth codes are typically 8-10 chars and not common words
            if 6 <= len(code) <= 12 and not code.lower() in ['atcushwake', 'microsoft', 'exchange', 'online']:
                return code
    
    return None

def is_authenticated_from_logs(logs: str) -> bool:
    """Check if authentication was successful by detecting welcome message"""
    
    # Look for welcome message patterns that appear after successful authentication
    welcome_patterns = [
        "This V3 EXO PowerShell module contains new REST API backed Exchange Online cmdlets",
        "Unlike the EXO* prefixed cmdlets, the cmdlets in this module support full functional parity", 
        "For more information check https://aka.ms/exov3-module",
        "Starting with EXO V3.7",
        "REST backed EOP and SCC cmdlets are also available",
        "LoadCmdletHelp parameter alongside Connect-ExchangeOnline",
        "=== CREATING MAILBOXES ===",  # This appears after successful auth
        "Creating .* mailboxes for domain:"  # Regex pattern for mailbox creation start
    ]
    
    for pattern in welcome_patterns:
        if re.search(pattern, logs, re.IGNORECASE):
            return True
    
    return False

def parse_container_status(logs: str) -> str:
    """Parse current status from container logs"""
    if "AUTH_TIMEOUT:" in logs:
        return "auth_timeout"
    elif is_authenticated_from_logs(logs):
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