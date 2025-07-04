#!/usr/bin/env python3
"""
Test script for proxy verification feature
"""

import requests
import time
import json

# API Configuration
API_BASE = "https://yes-app.dqlb47.easypanel.host"
# API_BASE = "http://localhost:8000"  # For local testing

def test_proxy_verification():
    """Test the proxy verification feature"""
    
    print("🧪 Testing Proxy Verification Feature")
    print("=" * 50)
    
    # Test 1: Without proxy
    print("\n📍 Test 1: Creating container WITHOUT proxy")
    response1 = requests.post(f"{API_BASE}/create-mailboxes", json={
        "domain": "test-no-proxy.com",
        "sender_name": "Test User",
        "password": "TestPass123!",
        "variations": 3
        # No proxy_endpoint specified
    })
    
    if response1.status_code == 200:
        data1 = response1.json()
        container_id1 = data1["container_id"]
        print(f"✅ Container created: {container_id1}")
        
        # Check status after 30 seconds
        print("⏳ Waiting 30 seconds for IP check...")
        time.sleep(30)
        
        status1 = requests.get(f"{API_BASE}/status/{container_id1}")
        if status1.status_code == 200:
            status_data1 = status1.json()
            ip_info1 = status_data1.get("ip_info")
            print(f"🌍 IP Info (No Proxy): {ip_info1}")
        else:
            print(f"❌ Failed to get status: {status1.status_code}")
    else:
        print(f"❌ Failed to create container: {response1.status_code}")
    
    # Test 2: With proxy
    print("\n📍 Test 2: Creating container WITH proxy")
    response2 = requests.post(f"{API_BASE}/create-mailboxes", json={
        "domain": "test-with-proxy.com",
        "sender_name": "Test User", 
        "password": "TestPass123!",
        "variations": 3,
        "proxy_endpoint": "socks5://8jm9GymM9fj1umY_c_US:RNW78Fm5@secret.infrastructure.2.flowproxies.com:10590"
    })
    
    if response2.status_code == 200:
        data2 = response2.json()
        container_id2 = data2["container_id"]
        print(f"✅ Container created: {container_id2}")
        
        # Check status after 30 seconds
        print("⏳ Waiting 30 seconds for IP check...")
        time.sleep(30)
        
        status2 = requests.get(f"{API_BASE}/status/{container_id2}")
        if status2.status_code == 200:
            status_data2 = status2.json()
            ip_info2 = status_data2.get("ip_info")
            print(f"🌍 IP Info (With Proxy): {ip_info2}")
            
            # Compare results
            print("\n📊 Comparison Results:")
            print(f"No Proxy:   {ip_info1}")
            print(f"With Proxy: {ip_info2}")
            
            if ip_info1 and ip_info2:
                if ip_info1 != ip_info2:
                    print("✅ Proxy verification SUCCESS: Different IPs detected!")
                else:
                    print("⚠️  Proxy verification WARNING: Same IPs - proxy may not be working")
            else:
                print("❌ Could not compare - missing IP info")
                
        else:
            print(f"❌ Failed to get status: {status2.status_code}")
    else:
        print(f"❌ Failed to create container: {response2.status_code}")
    
    # Cleanup containers
    print("\n🧹 Cleaning up containers...")
    if 'container_id1' in locals():
        cleanup1 = requests.delete(f"{API_BASE}/containers/{container_id1}")
        print(f"Container 1 cleanup: {cleanup1.status_code}")
    
    if 'container_id2' in locals():
        cleanup2 = requests.delete(f"{API_BASE}/containers/{container_id2}")
        print(f"Container 2 cleanup: {cleanup2.status_code}")
    
    print("\n✨ Proxy verification test completed!")

if __name__ == "__main__":
    test_proxy_verification() 