#!/usr/bin/env python3
"""
GraphQL Order Reminder Script using gql library
Sends reminders for pending orders from the last 7 days
"""

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import datetime
from datetime import timedelta
import os
import sys

# GraphQL endpoint
GRAPHQL_URL = "http://localhost:8000/graphql"
LOG_FILE = "/tmp/order_reminders_log.txt"

def log_message(message):
    """Log messages to both console and log file"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    
    print(log_entry)
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry + '\n')

def get_recent_orders_gql():
    """
    Query GraphQL API for orders from the last 7 days using gql library
    """
    try:
        # Configure transport
        transport = RequestsHTTPTransport(
            url=GRAPHQL_URL,
            use_json=True,
            headers={'Content-Type': 'application/json'},
        )
        
        # Create client
        client = Client(transport=transport, fetch_schema_from_transport=False)
        
        # Calculate date 7 days ago
        seven_days_ago = (datetime.datetime.now() - timedelta(days=7)).isoformat()
        
        # GraphQL query
        query = gql("""
            query GetRecentOrders($since: DateTime!) {
                filteredOrders(filter: {orderDateGte: $since}) {
                    id
                    orderDate
                    totalAmount
                    customer {
                        id
                        name
                        email
                        phone
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
        """)
        
        variables = {"since": seven_days_ago}
        
        # Execute query
        result = client.execute(query, variable_values=variables)
        return result.get('filteredOrders', [])
        
    except Exception as e:
        log_message(f"GraphQL query failed: {str(e)}")
        return []

def send_order_reminders():
    """
    Main function to process recent orders and send reminders
    """
    log_message("Starting order reminder processing")
    
    # Choose which method to use (requests or gql)
    recent_orders = get_recent_orders_gql()  # Using gql library
    
    if not recent_orders:
        log_message("No recent orders found or failed to fetch orders")
        print("Order reminders processed!")
        return
    
    log_message(f"Found {len(recent_orders)} orders from the last 7 days")
    
    # Process each order
    for order in recent_orders:
        order_id = order.get('id', 'N/A')
        order_date = order.get('orderDate', 'N/A')
        customer = order.get('customer', {})
        customer_email = customer.get('email', 'No email')
        customer_name = customer.get('name', 'Unknown Customer')
        total_amount = order.get('totalAmount', 0)
        
        # Log order reminder details
        reminder_message = (
            f"Order Reminder - ID: {order_id}, "
            f"Customer: {customer_name} ({customer_email}), "
            f"Date: {order_date}, "
            f"Total: ${total_amount}"
        )
        
        log_message(reminder_message)
    
    log_message("Order reminder processing completed")
    print("Order reminders processed!")

if __name__ == "__main__":
    send_order_reminders()
