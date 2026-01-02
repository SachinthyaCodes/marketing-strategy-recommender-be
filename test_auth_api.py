"""
Integration tests for authentication endpoints
Requires server to be running: python run_server.py
"""
import requests
import random
import string


BASE_URL = "http://localhost:8000"
TEST_EMAIL = f"test_{''.join(random.choices(string.ascii_lowercase, k=8))}@example.com"
TEST_PASSWORD = "SecureTestPass123"


def test_register():
    """Test user registration"""
    print("\n📝 Testing User Registration...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"   ✅ User registered successfully")
        print(f"   User ID: {data['id']}")
        print(f"   Email: {data['email']}")
        return True
    else:
        print(f"   ❌ Registration failed: {response.text}")
        return False


def test_login():
    """Test user login"""
    print("\n🔐 Testing User Login...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Login successful")
        print(f"   Token Type: {data['token_type']}")
        print(f"   Access Token: {data['access_token'][:50]}...")
        return data['access_token']
    else:
        print(f"   ❌ Login failed: {response.text}")
        return None


def test_protected_route(token):
    """Test protected route access"""
    print("\n🛡️  Testing Protected Route...")
    
    response = requests.get(
        f"{BASE_URL}/api/v1/auth/protected",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Protected route accessed successfully")
        print(f"   Message: {data['message']}")
        print(f"   User Email: {data['user_email']}")
        print(f"   User ID: {data['user_id']}")
        return True
    else:
        print(f"   ❌ Protected route access failed: {response.text}")
        return False


def test_get_current_user(token):
    """Test get current user endpoint"""
    print("\n👤 Testing Get Current User...")
    
    response = requests.get(
        f"{BASE_URL}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ User data retrieved successfully")
        print(f"   Email: {data['email']}")
        print(f"   ID: {data['id']}")
        print(f"   Created At: {data['created_at']}")
        return True
    else:
        print(f"   ❌ Get current user failed: {response.text}")
        return False


def test_invalid_token():
    """Test access with invalid token"""
    print("\n🚫 Testing Invalid Token...")
    
    response = requests.get(
        f"{BASE_URL}/api/v1/auth/protected",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 401:
        print(f"   ✅ Invalid token correctly rejected")
        return True
    else:
        print(f"   ❌ Invalid token should return 401")
        return False


def test_duplicate_registration():
    """Test registering with existing email"""
    print("\n♻️  Testing Duplicate Registration...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": "AnotherPassword123"
        }
    )
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 400:
        print(f"   ✅ Duplicate registration correctly rejected")
        print(f"   Error: {response.json()['detail']}")
        return True
    else:
        print(f"   ❌ Duplicate registration should return 400")
        return False


def test_wrong_password():
    """Test login with wrong password"""
    print("\n❌ Testing Wrong Password...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": "WrongPassword123"
        }
    )
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 401:
        print(f"   ✅ Wrong password correctly rejected")
        return True
    else:
        print(f"   ❌ Wrong password should return 401")
        return False


def main():
    """Run all integration tests"""
    print("=" * 70)
    print("JWT Authentication System - API Integration Tests")
    print("=" * 70)
    print(f"\n📍 Base URL: {BASE_URL}")
    print(f"📧 Test Email: {TEST_EMAIL}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"✅ Server is running")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Server is not running at {BASE_URL}")
        print(f"   Please start the server: python run_server.py")
        return 1
    
    results = []
    token = None
    
    # Run tests in sequence
    results.append(("User Registration", test_register()))
    
    token = test_login()
    results.append(("User Login", token is not None))
    
    if token:
        results.append(("Protected Route", test_protected_route(token)))
        results.append(("Get Current User", test_get_current_user(token)))
    
    results.append(("Invalid Token", test_invalid_token()))
    results.append(("Duplicate Registration", test_duplicate_registration()))
    results.append(("Wrong Password", test_wrong_password()))
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Results Summary:")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📊 Total: {passed} passed, {failed} failed out of {passed + failed} tests")
    
    if failed == 0:
        print("\n🎉 All integration tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
