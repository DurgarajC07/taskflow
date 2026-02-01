"""
Quick API Test Script
Tests the REST API endpoints to ensure they're working.
"""

import requests
import json

BASE_URL = 'http://127.0.0.1:8000/api/v1'

def test_endpoints():
    print("=== TaskFlow API Test ===\n")
    
    # 1. Register a new user
    print("1. Testing user registration...")
    try:
        response = requests.post(f'{BASE_URL}/auth/register/', json={
            'email': 'demo@taskflow.com',
            'password': 'DemoPass123!',
            'password_confirm': 'DemoPass123!',
            'first_name': 'Demo',
            'last_name': 'User'
        })
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"   ✓ User created: {data['user']['email']}")
            access_token = data['access']
            print(f"   ✓ Access token received")
        else:
            print(f"   ✗ Error: {response.text}")
            # Try to login instead
            print("\n2. Trying to login with existing user...")
            response = requests.post(f'{BASE_URL}/auth/login/', json={
                'email': 'demo@taskflow.com',
                'password': 'DemoPass123!'
            })
            if response.status_code == 200:
                data = response.json()
                access_token = data['access']
                print(f"   ✓ Login successful")
            else:
                print(f"   ✗ Login failed: {response.text}")
                return
    except Exception as e:
        print(f"   ✗ Exception: {e}")
        return
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # 2. Create an organization
    print("\n3. Creating organization...")
    try:
        response = requests.post(f'{BASE_URL}/organizations/', 
            headers=headers,
            json={
                'name': 'Demo Organization',
                'slug': 'demo-org',
                'description': 'A test organization'
            }
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            org = response.json()
            print(f"   ✓ Organization created: {org['name']}")
            org_id = org['id']
        else:
            print(f"   ✗ Error: {response.text}")
            org_id = None
    except Exception as e:
        print(f"   ✗ Exception: {e}")
        org_id = None
    
    # 3. Create a project
    print("\n4. Creating project...")
    try:
        response = requests.post(f'{BASE_URL}/projects/',
            headers=headers,
            json={
                'name': 'Demo Project',
                'key': 'DEMO',
                'description': 'A test project',
                'status': 'active',
                'priority': 'high'
            }
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            project = response.json()
            print(f"   ✓ Project created: {project['name']} ({project['key']})")
            project_id = project['id']
        else:
            print(f"   ✗ Error: {response.text}")
            project_id = None
    except Exception as e:
        print(f"   ✗ Exception: {e}")
        project_id = None
    
    # 4. List projects
    print("\n5. Fetching projects list...")
    try:
        response = requests.get(f'{BASE_URL}/projects/', headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            projects = data.get('results', [])
            print(f"   ✓ Found {len(projects)} project(s)")
            for p in projects:
                print(f"      - {p['name']} ({p['key']}) - {p['status']}")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # 5. Create a task
    if project_id:
        print("\n6. Creating task...")
        try:
            response = requests.post(f'{BASE_URL}/tasks/',
                headers=headers,
                json={
                    'title': 'Test Task',
                    'description': 'This is a test task',
                    'project': project_id,
                    'priority': 'high',
                    'type': 'task'
                }
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 201:
                task = response.json()
                print(f"   ✓ Task created: {task['task_key']} - {task['title']}")
            else:
                print(f"   ✗ Error: {response.text}")
        except Exception as e:
            print(f"   ✗ Exception: {e}")
    
    # 6. List tasks
    print("\n7. Fetching tasks list...")
    try:
        response = requests.get(f'{BASE_URL}/tasks/', headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            tasks = data.get('results', [])
            print(f"   ✓ Found {len(tasks)} task(s)")
            for t in tasks:
                print(f"      - {t['task_key']}: {t['title']} ({t['priority']})")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    print("\n=== API Test Complete ===")


if __name__ == '__main__':
    test_endpoints()
