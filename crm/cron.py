"""
CRM Cron Jobs for django-crontab
"""

import os
import django
from datetime import datetime
from django.test import Client
from django.conf import settings
import json
import requests

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

def log_crm_heartbeat():
    """
    CRM Heartbeat cron job that runs every 5 minutes
    Logs system health and optionally tests GraphQL endpoint
    """
    log_file = '/tmp/crm_heartbeat_log.txt'
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    try:
        # Test GraphQL endpoint responsiveness
        graphql_status = test_graphql_endpoint()
        
        # Prepare log message
        message = f"{timestamp} CRM is alive - GraphQL: {graphql_status}"
        
        # Log to file
        with open(log_file, 'a') as f:
            f.write(message + '\n')
        
        print(f"Heartbeat logged: {message}")
        
    except Exception as e:
        # Log error if something goes wrong
        error_message = f"{timestamp} CRM heartbeat failed: {str(e)}"
        with open(log_file, 'a') as f:
            f.write(error_message + '\n')
        print(f"Heartbeat error: {error_message}")

def test_graphql_endpoint():
    """
    Test GraphQL endpoint by querying the hello field
    Returns status string
    """
    try:
        # Method 1: Using Django test client (more reliable)
        from django.test import Client
        client = Client()
        
        query = '''
        query {
            hello
        }
        '''
        
        response = client.post(
            '/graphql',
            data={'query': query},
            content_type='application/json'
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['hello'] == "Hello, GraphQL!":
                return "HEALTHY"
            else:
                return f"UNHEALTHY - Response: {data}"
        else:
            return f"UNHEALTHY - HTTP {response.status_code}"
            
    except Exception as e:
        return f"ERROR - {str(e)}"

def test_graphql_with_requests():
    """
    Alternative method using requests to test GraphQL endpoint
    Useful if you want to test the actual HTTP endpoint
    """
    try:
        query = '''
        query {
            hello
        }
        '''
        
        response = requests.post(
            'http://localhost:8000/graphql',
            json={'query': query},
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['hello'] == "Hello, GraphQL!":
                return "HEALTHY"
            else:
                return f"UNHEALTHY - Response: {data}"
        else:
            return f"UNHEALTHY - HTTP {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        return f"NETWORK_ERROR - {str(e)}"
    except Exception as e:
        return f"ERROR - {str(e)}"

"""
"""
CRM Cron Jobs for django-crontab - Enhanced Version
"""

import os
import django
from datetime import datetime
import requests
import json
from django.db import connection
from django.core.cache import cache

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

def log_crm_heartbeat():
    """
    Enhanced CRM Heartbeat with multiple health checks
    """
    log_file = '/tmp/crm_heartbeat_log.txt'
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    try:
        # Run multiple health checks
        health_checks = {
            'graphql': test_graphql_endpoint(),
            'database': test_database_connection(),
            'cache': test_cache_connection(),
        }
        
        # Determine overall status
        all_healthy = all(status == 'HEALTHY' for status in health_checks.values())
        overall_status = 'HEALTHY' if all_healthy else 'DEGRADED'
        
        # Prepare detailed log message
        status_details = ', '.join([f"{k}: {v}" for k, v in health_checks.items()])
        message = f"{timestamp} CRM is {overall_status} - {status_details}"
        
        # Log to file
        with open(log_file, 'a') as f:
            f.write(message + '\n')
        
        print(f"Heartbeat logged: {message}")
        
    except Exception as e:
        # Log error if something goes wrong
        error_message = f"{timestamp} CRM heartbeat failed: {str(e)}"
        with open(log_file, 'a') as f:
            f.write(error_message + '\n')
        print(f"Heartbeat error: {error_message}")

def test_graphql_endpoint():
    """
    Test GraphQL endpoint using Django test client
    """
    try:
        from django.test import Client
        client = Client()
        
        query = '''
        query {
            hello
        }
        '''
        
        response = client.post(
            '/graphql',
            data=json.dumps({'query': query}),
            content_type='application/json'
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['hello'] == "Hello, GraphQL!":
                return "HEALTHY"
            else:
                return "UNHEALTHY"
        else:
            return f"HTTP_{response.status_code}"
            
    except Exception as e:
        return f"ERROR"

def test_database_connection():
    """
    Test database connection
    """
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return "HEALTHY"
    except Exception:
        return "UNHEALTHY"

def test_cache_connection():
    """
    Test cache connection
    """
    try:
        cache.set('heartbeat_test', 'alive', 1)
        if cache.get('heartbeat_test') == 'alive':
            return "HEALTHY"
        return "UNHEALTHY"
    except Exception:
        return "UNHEALTHY"
"""
