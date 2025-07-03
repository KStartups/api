#!/usr/bin/env python3
import requests
import json
import time

# ===== CONFIGURATION =====
DOMAIN = "atcushwake.com"
SENDER_NAME = "Michelle Martin"
PASSWORD = "Testest123~"
VARIATIONS = 5
PROXY = "socks5://8jm9GymM9fj1umY_c_US:RNW78Fm5@secret.infrastructure.2.flowproxies.com:10590"
API_BASE = "https://yes-app.dqlb47.easypanel.host"

def print_header(text):
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60)

def print_step(text):
    print(f"\n🔄 {text}")

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def create_container():
    print_header("CREATING MAILBOX CONTAINER")
    print_info(f"Domain: {DOMAIN}")
    print_info(f"Sender: {SENDER_NAME}")
    print_info(f"Password: {PASSWORD}")
    print_info(f"Variations: {VARIATIONS}")
    print_info(f"Proxy: {PROXY}")
    
    data = {
        "domain": DOMAIN,
        "sender_name": SENDER_NAME,
        "password": PASSWORD,
        "variations": VARIATIONS,
        "proxy_endpoint": PROXY
    }
    
    print_step("Sending request to create container...")
    
    try:
        response = requests.post(f"{API_BASE}/create-mailboxes", json=data, timeout=30)
        result = response.json()
        
        if result.get("success"):
            container_id = result.get("container_id")
            print_success(f"Container created: {container_id}")
            return container_id
        else:
            print_error(f"Failed to create container: {result}")
            return None
            
    except Exception as e:
        print_error(f"Error creating container: {e}")
        return None

def check_status(container_id):
    print_header(f"CHECKING STATUS: {container_id}")
    
    try:
        response = requests.get(f"{API_BASE}/status/{container_id}", timeout=10)
        result = response.json()
        
        print_info(f"Status: {result.get('status', 'unknown')}")
        
        auth_code = result.get('auth_code')
        if auth_code:
            print_success(f"🔑 AUTH CODE: {auth_code}")
            print_info("👉 Go to: https://microsoft.com/devicelogin")
            print_info(f"👉 Enter code: {auth_code}")
        
        logs = result.get('logs', '')
        if logs:
            print_step("Recent logs:")
            # Show last 1000 chars of logs
            recent_logs = logs[-1000:] if len(logs) > 1000 else logs
            print(recent_logs)
        
        created = result.get('created_mailboxes', [])
        failed = result.get('failed_mailboxes', [])
        
        if created:
            print_success(f"Created {len(created)} mailboxes:")
            for email in created:
                print(f"  ✅ {email}")
        
        if failed:
            print_error(f"Failed {len(failed)} mailboxes:")
            for email in failed:
                print(f"  ❌ {email}")
        
        return result
        
    except Exception as e:
        print_error(f"Error checking status: {e}")
        return None

def monitor_container(container_id):
    print_header(f"MONITORING CONTAINER: {container_id}")
    print_info("Checking status every 10 seconds...")
    print_info("Press Ctrl+C to stop monitoring")
    
    try:
        while True:
            result = check_status(container_id)
            
            if result:
                status = result.get('status', 'unknown')
                
                if status in ['completed', 'failed', 'auth_timeout']:
                    print_success(f"Final status: {status}")
                    break
                    
                if status == 'waiting_for_auth' and result.get('auth_code'):
                    print_info("⏳ Waiting for you to complete authentication...")
            
            print_info("Waiting 10 seconds before next check...")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print_info("\nMonitoring stopped by user")

def main():
    print_header("MAILBOX CREATOR TEST")
    
    # Create container
    container_id = create_container()
    if not container_id:
        return
    
    # Wait a moment for container to start
    print_step("Waiting 5 seconds for container to initialize...")
    time.sleep(5)
    
    # Monitor the container
    monitor_container(container_id)

if __name__ == "__main__":
    main() 