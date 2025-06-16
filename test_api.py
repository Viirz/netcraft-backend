#!/usr/bin/env python3
"""
Simple test script to verify the API is working correctly
"""
import requests
import json
import time

API_BASE = "http://localhost:3000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_register():
    """Test user registration"""
    print("\nTesting user registration...")
    user_data = {
        "nickname": "testuser2",
        "email": "test2@mail.com",
        "password": "Password123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/auth/register", json=user_data)
        print(f"Registration: {response.status_code} - {response.json()}")
        if response.status_code == 201:
            return response.json().get('token')
    except Exception as e:
        print(f"Registration failed: {e}")
    return None

def test_login():
    """Test user login"""
    print("\nTesting user login...")
    login_data = {
        "email": "test2@mail.com",
        "password": "Password123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/auth/login", json=login_data)
        print(f"Login: {response.status_code} - {response.json()}")
        if response.status_code == 200:
            return response.json().get('token')
    except Exception as e:
        print(f"Login failed: {e}")
    return None

def test_logout(token):
    """Test user logout"""
    if not token:
        print("\nSkipping logout test - no token")
        return False
        
    print("\nTesting user logout...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{API_BASE}/api/auth/logout", headers=headers)
        print(f"Logout: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Logout failed: {e}")
        return False

def test_protected_endpoint_after_logout(token):
    """Test that protected endpoints reject revoked token"""
    if not token:
        print("\nSkipping protected endpoint test - no token")
        return
        
    print("\nTesting protected endpoint with revoked token...")
    headers = {"Authorization": f"Bearer {token}"}
    project_data = {
        "name": "Test Project After Logout",
        "data": {"description": "Should fail", "version": "1.0"}
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/projects/save", 
                               json=project_data, headers=headers)
        print(f"Protected endpoint with revoked token: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Protected endpoint test failed: {e}")

def test_create_project(token):
    """Test project creation"""
    if not token:
        print("\nSkipping project test - no token")
        return
        
    print("\nTesting project creation...")
    headers = {"Authorization": f"Bearer {token}"}
    project_data = {
        "name": "Test Project",
        "data": {"description": "A test project", "version": "1.0"}
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/projects/save", 
                               json=project_data, headers=headers)
        print(f"Project creation: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Project creation failed: {e}")

def main():
    print("NETCRAFT API Test Script")
    print("=" * 30)
    
    # Wait for API to be ready
    print("Waiting for API to be ready...")
    for i in range(30):
        if test_health():
            break
        time.sleep(2)
        print(f"Attempt {i+1}/30...")
    else:
        print("API health check failed after 30 attempts")
        return
    
    # Test registration
    token = test_register()
    
    # Test login (in case registration fails due to existing user)
    if not token:
        token = test_login()
    
    # Test project creation with valid token
    test_create_project(token)
    
    # Test logout
    logout_success = test_logout(token)
    
    # Test protected endpoint with revoked token
    if logout_success:
        test_protected_endpoint_after_logout(token)
    
    print("\n" + "=" * 30)
    print("Test completed!")

if __name__ == "__main__":
    main()