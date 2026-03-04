"""
Test JWT Authentication Endpoints
Run this script to test if JWT authentication is working correctly.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/auth"

def test_register():
    """Test user registration"""
    print("\n" + "="*60)
    print("Testing User Registration...")
    print("="*60)
    
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123",
        "password_confirm": "TestPass123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = requests.post(f"{BASE_URL}/register/", json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        tokens = response.json()["tokens"]
        return tokens
    return None

def test_login():
    """Test user login"""
    print("\n" + "="*60)
    print("Testing User Login...")
    print("="*60)
    
    data = {
        "email": "test@example.com",
        "password": "TestPass123"
    }
    
    response = requests.post(f"{BASE_URL}/login/", json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        tokens = response.json()["tokens"]
        return tokens
    return None

def test_me(access_token):
    """Test getting current user"""
    print("\n" + "="*60)
    print("Testing Get Current User (Me)...")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(f"{BASE_URL}/me/", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_refresh_token(refresh_token):
    """Test token refresh"""
    print("\n" + "="*60)
    print("Testing Token Refresh...")
    print("="*60)
    
    data = {
        "refresh": refresh_token
    }
    
    response = requests.post(f"{BASE_URL}/refresh_token/", json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        return response.json()["tokens"]
    return None

def test_logout(access_token, refresh_token):
    """Test user logout"""
    print("\n" + "="*60)
    print("Testing User Logout...")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    data = {
        "refresh": refresh_token
    }
    
    response = requests.post(f"{BASE_URL}/logout/", headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def run_tests():
    """Run all tests"""
    print("\n")
    print("🚀 " + "="*54 + " 🚀")
    print("   JWT AUTHENTICATION TEST SUITE")
    print("🚀 " + "="*54 + " 🚀")
    
    # Test 1: Register (or skip if user exists)
    print("\nNote: If registration fails (user exists), we'll login instead.")
    tokens = test_register()
    
    if not tokens:
        # If registration fails, try login
        tokens = test_login()
    
    if not tokens:
        print("\n❌ Failed to get tokens. Please check your Django server.")
        return
    
    access_token = tokens["access"]
    refresh_token = tokens["refresh"]
    
    # Test 2: Get current user
    test_me(access_token)
    
    # Test 3: Refresh token
    new_tokens = test_refresh_token(refresh_token)
    if new_tokens:
        access_token = new_tokens["access"]
        refresh_token = new_tokens["refresh"]
        print("\n✅ Token refreshed successfully!")
    
    # Test 4: Logout
    test_logout(access_token, refresh_token)
    
    # Test 5: Try to use blacklisted token (should fail)
    print("\n" + "="*60)
    print("Testing Blacklisted Token (Should Fail)...")
    print("="*60)
    test_me(access_token)
    
    print("\n")
    print("🎉 " + "="*54 + " 🎉")
    print("   ALL TESTS COMPLETED!")
    print("🎉 " + "="*54 + " 🎉")
    print("\n")

if __name__ == "__main__":
    try:
        run_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to Django server.")
        print("Please make sure your Django server is running on http://localhost:8000")
        print("Run: python manage.py runserver")
    except Exception as e:
        print(f"\n❌ Error: {e}")
