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

def update_low_stock():
    """
    Cron job to update low-stock products every 12 hours
    Uses GraphQL mutation to restock products with stock < 10
    """
    log_file = '/tmp/low_stock_updates_log.txt'
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    try:
        # Configure GraphQL client
        transport = RequestsHTTPTransport(
            url='http://localhost:8000/graphql',
            use_json=True,
            headers={
                'Content-Type': 'application/json',
            },
            verify=True,
            retries=3,
            timeout=30
        )
        
        client = Client(
            transport=transport,
            fetch_schema_from_transport=False
        )
        
        # Define GraphQL mutation for updating low-stock products
        mutation = gql("""
            mutation UpdateLowStockProducts($restockAmount: Int) {
                updateLowStockProducts(restockAmount: $restockAmount) {
                    success
                    message
                    errors
                    updatedProducts {
                        id
                        name
                        price
                        stock
                        description
                    }
                }
            }
        """)
        
        # Execute mutation with restock amount
        variables = {"restockAmount": 10}
        result = client.execute(mutation, variable_values=variables)
        
        mutation_result = result.get('updateLowStockProducts', {})
        
        if mutation_result.get('success'):
            updated_products = mutation_result.get('updatedProducts', [])
            message = mutation_result.get('message', '')
            
            # Log the results
            log_entries = [
                f"{timestamp} - Low Stock Update Job Started",
                f"Mutation Result: {message}"
            ]
            
            if updated_products:
                log_entries.append("Updated Products:")
                for product in updated_products:
                    log_entry = (
                        f"  - Product: {product.get('name', 'N/A')} "
                        f"(ID: {product.get('id', 'N/A')}), "
                        f"New Stock: {product.get('stock', 0)}"
                    )
                    log_entries.append(log_entry)
            else:
                log_entries.append("No products were updated.")
            
            log_entries.append(f"{timestamp} - Low Stock Update Job Completed\n")
            
        else:
            errors = mutation_result.get('errors', ['Unknown error'])
            log_entries = [
                f"{timestamp} - Low Stock Update Job Failed",
                f"Errors: {', '.join(errors)}",
                f"{timestamp} - Low Stock Update Job Completed with Errors\n"
            ]
        
        # Write all log entries
        with open(log_file, 'a') as f:
            for entry in log_entries:
                f.write(entry + '\n')
                print(entry)  # Also print to console for cron logging
        
        print("Low stock update job completed successfully")
        
    except Exception as e:
        error_message = f"{timestamp} - Low Stock Update Job Failed: {str(e)}"
        with open(log_file, 'a') as f:
            f.write(error_message + '\n')
        print(f"Low stock update job failed: {str(e)}")

def update_low_stock_with_requests():
    """
    Alternative implementation using requests library instead of gql
    """
    log_file = '/tmp/low_stock_updates_log.txt'
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    try:
        # GraphQL mutation
        mutation = """
            mutation UpdateLowStockProducts {
                updateLowStockProducts {
                    success
                    message
                    errors
                    updatedProducts {
                        id
                        name
                        price
                        stock
                    }
                }
            }
        """
        
        response = requests.post(
            'http://localhost:8000/graphql',
            json={'query': mutation},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            mutation_result = data.get('data', {}).get('updateLowStockProducts', {})
            
            if mutation_result.get('success'):
                updated_products = mutation_result.get('updatedProducts', [])
                message = mutation_result.get('message', '')
                
                log_entry = f"{timestamp} - {message}\n"
                
                if updated_products:
                    log_entry += "Updated Products:\n"
                    for product in updated_products:
                        log_entry += (
                            f"  - {product.get('name')} "
                            f"(Stock: {product.get('stock')})\n"
                        )
                
                with open(log_file, 'a') as f:
                    f.write(log_entry + '\n')
                
                print(f"Low stock update successful: {message}")
            else:
                errors = mutation_result.get('errors', ['Unknown error'])
                error_message = f"{timestamp} - Update failed: {', '.join(errors)}"
                with open(log_file, 'a') as f:
                    f.write(error_message + '\n')
                print(error_message)
        else:
            error_message = f"{timestamp} - HTTP Error: {response.status_code}"
            with open(log_file, 'a') as f:
                f.write(error_message + '\n')
            print(error_message)
            
    except Exception as e:
        error_message = f"{timestamp} - Low Stock Update Job Failed: {str(e)}"
        with open(log_file, 'a') as f:
            f.write(error_message + '\n')
        print(f"Low stock update job failed: {str(e)}")

# Keep the existing heartbeat function and other health checks
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
    """Test GraphQL endpoint using the gql library"""
    try:
        transport = RequestsHTTPTransport(
            url='http://localhost:8000/graphql',
            use_json=True,
            headers={'Content-Type': 'application/json'},
            verify=True,
            retries=3,
            timeout=10
        )
        
        client = Client(transport=transport, fetch_schema_from_transport=False)
        
        query = gql("""
            query HealthCheck {
                hello
            }
        """)
        
        result = client.execute(query)
        
        if result.get('hello') == "Hello, GraphQL!":
            return "HEALTHY"
        else:
            return "UNHEALTHY - Invalid response"
            
    except Exception as e:
        return f"ERROR - {str(e)}"

def test_graphql_with_requests():
    """Alternative GraphQL test using requests library"""
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
    """Test database connection"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return "HEALTHY"
    except Exception:
        return "UNHEALTHY"

def test_cache_connection():
    """Test cache connection"""
    try:
        cache.set('heartbeat_test', 'alive', 1)
        if cache.get('heartbeat_test') == 'alive':
            return "HEALTHY"
        return "UNHEALTHY"
    except Exception:
        return "UNHEALTHY"
