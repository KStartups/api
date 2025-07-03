import requests
import json
import time

# Test API with a simple request
url = "https://yes-app.dqlb47.easypanel.host/create-mailboxes"
data = {
    "domain": "test3.com",
    "sender_name": "Test User",
    "password": "TestPass123!",
    "variations": 2
}

print("Making API request...")
response = requests.post(url, json=data)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    result = response.json()
    container_id = result.get('container_id')
    print(f"\nContainer ID: {container_id}")
    
    if container_id:
        print("Waiting 5 seconds then checking status...")
        time.sleep(5)
        
        status_url = f"https://yes-app.dqlb47.easypanel.host/status/{container_id}"
        status_response = requests.get(status_url)
        print(f"\nStatus Response: {status_response.text}")
        
        print("\nChecking containers list...")
        containers_response = requests.get("https://yes-app.dqlb47.easypanel.host/containers")
        print(f"Containers: {containers_response.text}") 