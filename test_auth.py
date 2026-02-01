import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

# Test 1: Register
print("=" * 50)
print("Testing REGISTER endpoint...")
print("=" * 50)
register_data = {
    "full_name": "Test User",
    "email": "test@example.com",
    "password": "test123"
}

try:
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        token = response.json().get("token")
        print(f"\n✅ Registration successful!")
        print(f"Token: {token[:50]}...")
    else:
        print(f"\n❌ Registration failed!")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Login
print("\n" + "=" * 50)
print("Testing LOGIN endpoint...")
print("=" * 50)
login_data = {
    "email": "test@example.com",
    "password": "test123"
}

try:
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        token = response.json().get("token")
        print(f"\n✅ Login successful!")
        print(f"Token: {token[:50]}...")
        
        # Test 3: Get Profile
        print("\n" + "=" * 50)
        print("Testing PROFILE endpoint...")
        print("=" * 50)
        headers = {"Authorization": f"Bearer {token}"}
        profile_response = requests.get(f"{BASE_URL}/auth/profile", headers=headers)
        print(f"Status Code: {profile_response.status_code}")
        print(f"Response: {json.dumps(profile_response.json(), indent=2)}")
        
        if profile_response.status_code == 200:
            print(f"\n✅ Profile retrieval successful!")
        else:
            print(f"\n❌ Profile retrieval failed!")
    else:
        print(f"\n❌ Login failed!")
except Exception as e:
    print(f"Error: {e}")
