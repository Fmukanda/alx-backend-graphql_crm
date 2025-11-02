from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime
import requests
import json
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

logger = get_task_logger(__name__)

@shared_task
def generate_crm_report():
    """
    Celery task to generate weekly CRM report using GraphQL queries
    """
    log_file = '/tmp/crm_report_log.txt'
    
    try:
        # Configure GraphQL client
        transport = RequestsHTTPTransport(
            url='http://localhost:8000/graphql',
            use_json=True,
            headers={'Content-Type': 'application/json'},
            verify=True,
            retries=3,
            timeout=30
        )
        
        client = Client(transport=transport, fetch_schema_from_transport=False)
        
        # GraphQL query to fetch CRM statistics
        query = gql("""
            query CRMReport {
                # Customer statistics
                allCustomers {
                    totalCount
                }
                
                # Order statistics
                allOrders {
                    totalCount
                    edges {
                        node {
                            totalAmount
                            orderDate
                            customer {
                                name
                                email
                            }
                            orderitemSet {
                                product {
                                    name
                                    price
                                }
                                quantity
                            }
                        }
                    }
                }
                
                # Product statistics
                allProducts {
                    totalCount
                    edges {
                        node {
                            name
                            price
                            stock
                        }
                    }
                }
            }
        """)
        
        # Execute query
        result = client.execute(query)
        
        # Process the data
        customer_count = result.get('allCustomers', {}).get('totalCount', 0)
        order_count = result.get('allOrders', {}).get('totalCount', 0)
        orders_data = result.get('allOrders', {}).get('edges', [])
        products_data = result.get('allProducts', {}).get('edges', [])
        
        # Calculate total revenue
        total_revenue = 0
        for order_edge in orders_data:
            order = order_edge.get('node', {})
            total_revenue += float(order.get('totalAmount', 0))
        
        # Calculate product statistics
        total_products = len(products_data)
        low_stock_products = 0
        for product_edge in products_data:
            product = product_edge.get('node', {})
            if product.get('stock', 0) < 10:
                low_stock_products += 1
        
        # Generate report timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Create report content
        report_lines = [
            f"\n{'='*50}",
            f"Weekly CRM Report - {timestamp}",
            f"{'='*50}",
            f"📊 Summary Statistics:",
            f"  • Total Customers: {customer_count}",
            f"  • Total Orders: {order_count}",
            f"  • Total Revenue: ${total_revenue:.2f}",
            f"  • Total Products: {total_products}",
            f"  • Low Stock Products: {low_stock_products}",
            f"",
            f"📈 Recent Activity:",
        ]
        
        # Add recent orders (last 5)
        recent_orders = orders_data[-5:] if len(orders_data) > 5 else orders_data
        if recent_orders:
            report_lines.append("  Recent Orders:")
            for order_edge in recent_orders:
                order = order_edge.get('node', {})
                customer = order.get('customer', {})
                report_lines.append(
                    f"    - {customer.get('name', 'Unknown')}: "
                    f"${float(order.get('totalAmount', 0)):.2f} "
                    f"({order.get('orderDate', '')[:10]})"
                )
        else:
            report_lines.append("  No recent orders")
        
        # Add low stock alert if any
        if low_stock_products > 0:
            report_lines.append("")
            report_lines.append(f"⚠️  Alert: {low_stock_products} products are low in stock!")
        
        report_lines.append(f"{'='*50}\n")
        
        # Write report to log file
        report_content = '\n'.join(report_lines)
        with open(log_file, 'a') as f:
            f.write(report_content)
        
        # Also create a simple log entry for cron-style logging
        simple_log = f"{timestamp} - Report: {customer_count} customers, {order_count} orders, ${total_revenue:.2f} revenue\n"
        with open(log_file, 'a') as f:
            f.write(simple_log)
        
        logger.info(f"CRM report generated: {customer_count} customers, {order_count} orders, ${total_revenue:.2f} revenue")
        
        return {
            'success': True,
            'customer_count': customer_count,
            'order_count': order_count,
            'total_revenue': total_revenue,
            'total_products': total_products,
            'low_stock_products': low_stock_products
        }
        
    except Exception as e:
        error_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Report generation failed: {str(e)}"
        with open(log_file, 'a') as f:
            f.write(error_message + '\n')
        
        logger.error(f"CRM report generation failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def daily_health_check():
    """
    Daily health check task using GraphQL
    """
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
                allCustomers {
                    totalCount
                }
                allOrders {
                    totalCount
                }
                allProducts {
                    totalCount
                }
            }
        """)
        
        result = client.execute(query)
        
        customer_count = result.get('allCustomers', {}).get('totalCount', 0)
        order_count = result.get('allOrders', {}).get('totalCount', 0)
        product_count = result.get('allProducts', {}).get('totalCount', 0)
        
        logger.info(f"Daily health check: System healthy - {customer_count} customers, {order_count} orders, {product_count} products")
        
        return {
            'status': 'healthy',
            'customer_count': customer_count,
            'order_count': order_count,
            'product_count': product_count
        }
        
    except Exception as e:
        logger.error(f"Daily health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'error': str(e)
        }

@shared_task
def generate_custom_report(report_type='weekly', custom_filters=None):
    """
    Flexible report generation task that can be called with different parameters
    """
    logger.info(f"Generating {report_type} report with filters: {custom_filters}")
    
    # This can be extended based on specific reporting needs
    if report_type == 'weekly':
        return generate_crm_report()
    elif report_type == 'daily':
        return daily_health_check()
    else:
        logger.warning(f"Unknown report type: {report_type}")
        return {'success': False, 'error': f'Unknown report type: {report_type}'}
