#!/usr/bin/env python3
"""
Quick test for IP verification
"""

import requests
import time

API_BASE = "https://yes-app.dqlb47.easypanel.host"

def quick_ip_test():
    print("🧪 Quick IP Verification Test")
    print("=" * 40)
    
    # Create container with proxy
    print("📍 Creating container with proxy...")
    response = requests.post(f"{API_BASE}/create-mailboxes", json={
        "domain": "quick-test.com",
        "sender_name": "Test User",
        "password": "TestPass123!",
        "variations": 2,
        "proxy_endpoint": "socks5://8jm9GymM9fj1umY_c_US:RNW78Fm5@secret.infrastructure.2.flowproxies.com:10590"
    })
    
    if response.status_code == 200:
        data = response.json()
        container_id = data["container_id"]
        print(f"✅ Container: {container_id}")
        
        # Wait and check status
        print("⏳ Waiting 35 seconds for IP check...")
        time.sleep(35)
        
        status_response = requests.get(f"{API_BASE}/status/{container_id}")
        if status_response.status_code == 200:
            status_data = status_response.json()
            ip_info = status_data.get("ip_info")
            print(f"🌍 IP Info: {ip_info}")
            
            if ip_info:
                print("✅ IP verification working!")
            else:
                print("❌ No IP info found")
                print("📋 Container logs:")
                print(status_data.get("logs", "No logs"))
        else:
            print(f"❌ Status check failed: {status_response.status_code}")
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        cleanup = requests.delete(f"{API_BASE}/containers/{container_id}")
        print(f"Cleanup: {cleanup.status_code}")
        
    else:
        print(f"❌ Container creation failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    quick_ip_test() 