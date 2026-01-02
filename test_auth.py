"""
Test script for JWT authentication system
Run this after starting the server to verify authentication works
"""
import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token
)


def test_password_hashing():
    """Test password hashing and verification"""
    print("\n🔒 Testing Password Hashing...")
    
    password = "TestPassword123"
    hashed = get_password_hash(password)
    
    print(f"   Original: {password}")
    print(f"   Hashed: {hashed[:50]}...")
    
    # Verify correct password
    is_valid = verify_password(password, hashed)
    print(f"   ✅ Correct password verified: {is_valid}")
    
    # Verify incorrect password
    is_valid_wrong = verify_password("WrongPassword", hashed)
    print(f"   ✅ Wrong password rejected: {not is_valid_wrong}")
    
    return is_valid and not is_valid_wrong


def test_jwt_tokens():
    """Test JWT token creation and verification"""
    print("\n🎫 Testing JWT Tokens...")
    
    # Create token
    token_data = {
        "sub": "test@example.com",
        "user_id": "123e4567-e89b-12d3-a456-426614174000"
    }
    
    token = create_access_token(data=token_data)
    print(f"   Token created: {token[:50]}...")
    
    # Decode token
    try:
        decoded = decode_access_token(token)
        print(f"   ✅ Token decoded successfully")
        print(f"   Email: {decoded.email}")
        print(f"   User ID: {decoded.user_id}")
        
        return decoded.email == token_data["sub"]
    except Exception as e:
        print(f"   ❌ Token decode failed: {e}")
        return False


def print_api_examples():
    """Print example API calls"""
    print("\n📝 API Usage Examples:")
    print("\n1. Register a new user:")
    print("""
curl -X POST http://localhost:8000/api/v1/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123"
  }'
    """)
    
    print("\n2. Login:")
    print("""
curl -X POST http://localhost:8000/api/v1/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123"
  }'
    """)
    
    print("\n3. Access protected route:")
    print("""
# Save token from login response
TOKEN="your_token_here"

curl -X GET http://localhost:8000/api/v1/auth/protected \\
  -H "Authorization: Bearer $TOKEN"
    """)


def main():
    """Run all tests"""
    print("=" * 60)
    print("JWT Authentication System - Unit Tests")
    print("=" * 60)
    
    results = []
    
    # Test password hashing
    results.append(("Password Hashing", test_password_hashing()))
    
    # Test JWT tokens
    results.append(("JWT Tokens", test_jwt_tokens()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        print_api_examples()
        print("\n⚠️  Next steps:")
        print("  1. Run the SQL migration in Supabase (migrations/001_create_users_table.sql)")
        print("  2. Add JWT_SECRET to your .env file")
        print("  3. Start the server: python run_server.py")
        print("  4. Test the API endpoints above")
    else:
        print("\n❌ Some tests failed. Check your implementation.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
