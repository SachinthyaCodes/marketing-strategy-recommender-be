"""Quick test script for registration endpoint"""
import requests
import json

url = "http://localhost:8000/api/v1/auth/register"
data = {
    "email": "testuser@example.com",
    "password": "password123"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 201:
        print("\n✅ Registration successful!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"\n❌ Registration failed with status {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
