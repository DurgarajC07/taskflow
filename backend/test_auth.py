"""
Auth Service
Authentication API endpoints for login, register, logout.
"""

from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.serializers import UserSerializer
import requests

API_BASE_URL = 'http://127.0.0.1:8000/api/v1'


def register_user(email: str, password: str, first_name: str = '', last_name: str = ''):
    """Register a new user."""
    response = requests.post(f'{API_BASE_URL}/auth/register/', json={
        'email': email,
        'password': password,
        'password_confirm': password,
        'first_name': first_name,
        'last_name': last_name
    })
    return response.json()


def login_user(email: str, password: str):
    """Login user and get tokens."""
    response = requests.post(f'{API_BASE_URL}/auth/login/', json={
        'email': email,
        'password': password
    })
    return response.json()


if __name__ == '__main__':
    # Create a test user
    print("Creating test user...")
    try:
        result = register_user(
            email='test@taskflow.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        print(f"User created: {result}")
    except Exception as e:
        print(f"Registration error: {e}")
    
    # Try to login
    print("\nLogging in...")
    try:
        result = login_user('test@taskflow.com', 'TestPass123!')
        print(f"Login successful!")
        print(f"Access token: {result.get('access', '')[:50]}...")
    except Exception as e:
        print(f"Login error: {e}")
