#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root directory
cd "$PROJECT_ROOT"

# Execute Django shell command to clean inactive customers
python manage.py shell << EOF
import datetime
from django.utils import timezone
from crm.models import Customer, Order

# Calculate date one year ago
one_year_ago = timezone.now() - datetime.timedelta(days=365)

# Find customers with no orders in the last year
inactive_customers = Customer.objects.filter(
    order__isnull=True
) | Customer.objects.filter(
    order__order_date__lt=one_year_ago
).distinct()

# Get count before deletion
count = inactive_customers.count()

# Delete inactive customers
inactive_customers.delete()

# Log the results
with open('/tmp/customer_cleanup_log.txt', 'a') as f:
    timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    f.write(f"[{timestamp}] Deleted {count} inactive customers (no orders since {one_year_ago.strftime('%Y-%m-%d')})\n")

print(f"Successfully deleted {count} inactive customers")
EOF
