"""
CRM Cron Jobs for django-crontab with GQL Integration
"""

import os
import django
from datetime import datetime
import requests
import json
from django.db import connection
from django.core.cache import cache

# GQL imports for GraphQL health checks
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

def log_crm_heartbeat():
    """
    Enhanced CRM Heartbeat with GQL library integration
    Runs every 5 minutes to monitor CRM health
    """
    log_file = '/tmp/crm_heartbeat_log.txt'
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    try:
        # Run comprehensive health checks
        health_checks = {
            'graphql_gql': test_graphql_with_gql(),
            'graphql_rest': test_graphql_with_requests(),
            'database': test_database_connection(),
            'cache': test_cache_connection(),
        }
        
        # Determine overall status
        healthy_count = sum(1 for status in health_checks.values() if status == 'HEALTHY')
        total_checks = len(health_checks)
        
        if healthy_count == total_checks:
            overall_status = 'HEALTHY'
        elif healthy_count >= total_checks // 2:
            overall_status = 'DEGRADED'
        else:
            overall_status = 'UNHEALTHY'
        
        # Prepare detailed log message
        status_details = ', '.join([f"{k}: {v}" for k, v in health_checks.items()])
        message = f"{timestamp} CRM is {overall_status} ({healthy_count}/{total_checks}) - {status_details}"
        
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

def test_graphql_with_gql():
    """
    Test GraphQL endpoint using the gql library
    More robust GraphQL client with proper error handling
    """
    try:
        # Configure transport with timeout
        transport = RequestsHTTPTransport(
            url='http://localhost:8000/graphql',
            use_json=True,
            headers={
                'Content-Type': 'application/json',
            },
            verify=True,
            retries=3,
            timeout=10
        )
        
        # Create client
        client = Client(
            transport=transport,
            fetch_schema_from_transport=False  # Don't fetch schema for simple queries
        )
        
        # Define GraphQL query
        query = gql("""
            query HealthCheck {
                hello
                allCustomers {
                    totalCount
                }
                allProducts {
                    totalCount
                }
            }
        """)
        
        # Execute query
        result = client.execute(query)
        
        # Validate response
        if (result.get('hello') == "Hello, GraphQL!" and 
            'allCustomers' in result and 
            'allProducts' in result):
            return "HEALTHY"
        else:
            return "UNHEALTHY - Invalid response"
            
    except Exception as e:
        return f"ERROR - {str(e)}"

def test_graphql_with_requests():
    """
    Alternative GraphQL test using requests library
    Good for comparison and fallback
    """
    try:
        query = '''
        query HealthCheck {
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
                return "UNHEALTHY - Invalid data"
        else:
            return f"UNHEALTHY - HTTP {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        return f"NETWORK_ERROR - {str(e)}"
    except Exception as e:
        return f"ERROR - {str(e)}"

def test_database_connection():
    """
    Test database connection and basic ORM functionality
    """
    try:
        from django.db import connection
        from crm.models import Customer, Product, Order
        
        # Test connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Test basic ORM operations
        customer_count = Customer.objects.count()
        product_count = Product.objects.count()
        order_count = Order.objects.count()
        
        return "HEALTHY"
    except Exception as e:
        return f"UNHEALTHY - {str(e)}"

def test_cache_connection():
    """
    Test cache connection
    """
    try:
        test_key = 'crm_heartbeat_test'
        test_value = f'alive_{datetime.now().timestamp()}'
        
        # Test set and get
        cache.set(test_key, test_value, 60)
        retrieved_value = cache.get(test_key)
        
        if retrieved_value == test_value:
            return "HEALTHY"
        else:
            return "UNHEALTHY - Cache mismatch"
    except Exception as e:
        return f"UNHEALTHY - {str(e)}"

def test_complex_graphql_operations():
    """
    Test more complex GraphQL operations using gql library
    This can be used for more thorough testing
    """
    try:
        transport = RequestsHTTPTransport(
            url='http://localhost:8000/graphql',
            use_json=True,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # Test query with variables
        query_with_vars = gql("""
            query GetFilteredCustomers($filter: String) {
                filteredCustomers(filter: {nameIcontains: $filter}) {
                    id
                    name
                    email
                }
            }
        """)
        
        variables = {"filter": "test"}
        result = client.execute(query_with_vars, variable_values=variables)
        
        if 'filteredCustomers' in result:
            return "HEALTHY"
        else:
            return "UNHEALTHY - Complex query failed"
            
    except Exception as e:
        return f"ERROR - {str(e)}"

# Optional: Add a function to test mutations (read-only for safety)
def test_graphql_mutation_safe():
    """
    Safely test GraphQL mutations (using queries instead to avoid side effects)
    """
    try:
        transport = RequestsHTTPTransport(
            url='http://localhost:8000/graphql',
            use_json=True,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        client = Client(transport=transport, fetch_schema_from_transport=False)
        
        # Test introspection query to verify schema is accessible
        introspection_query = gql("""
            query {
                __schema {
                    types {
                        name
                        kind
                    }
                }
            }
        """)
        
        result = client.execute(introspection_query)
        
        if '__schema' in result and 'types' in result['__schema']:
            return "HEALTHY"
        else:
            return "UNHEALTHY - Introspection failed"
            
    except Exception as e:
        return f"ERROR - {str(e)}"
