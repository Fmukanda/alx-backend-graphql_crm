# CRM Celery Setup Guide

This guide explains how to set up Celery with Celery Beat for automated CRM reporting.

## Prerequisites

- Redis server
- Python 3.8+
- Django 3.2+

## Installation Steps

### 1. Install Dependencies

```
pip install -r requirements.txt
```

### 2. Install and Start Redis
```
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

### 3. Database Setup
```
python manage.py runserver
```

### 4. Start Django Development Server
```
python manage.py runserver
```

### 5. Start Celery Worker
```
celery -A crm worker -l info
```

### 6. Start Celery Beat
```
celery -A crm beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### 7. Check Redis Connection
```
redis-cli ping
```

### 8. Test Celery Task Manually
**Start Django shell:**
```
python manage.py shell
```

**Test the task:**
```
from crm.tasks import generate_crm_report
result = generate_crm_report.delay()
print(result.get(timeout=30))
```

**Check Logs**
```
# CRM reports log
tail -f /tmp/crm_report_log.txt

# Celery worker logs
tail -f celery_worker.log

# Celery beat logs  
tail -f celery_beat.log
```

For monitoring Celery tasks, install Flower:
```
pip install flower
celery -A crm flower
```

### 9. Manual Task Execution
```
python manage.py shell
```
```
from crm.tasks import generate_crm_report, daily_health_check

# Execute immediately
generate_crm_report.delay()

# Execute at specific time
from datetime import datetime, timedelta
generate_crm_report.apply_async(eta=datetime.now() + timedelta(minutes=5))
```

### 10. Performance Tips
 - Use Redis persistence for important tasks
 - Monitor Celery queue lengths
 - Set appropriate task timeouts
 - Use task retries for transient failures

### 11. Create a Management Command for Testing

Create `crm/management/commands/test_celery.py`:

```
from django.core.management.base import BaseCommand
from crm.tasks import generate_crm_report, daily_health_check

class Command(BaseCommand):
    help = 'Test Celery tasks manually'

    def handle(self, *args, **options):
        self.stdout.write('Testing Celery tasks...')
        
        # Test CRM report
        result = generate_crm_report.delay()
        self.stdout.write(f'CRM Report Task ID: {result.id}')
        
        # Test health check
        health_result = daily_health_check.delay()
        self.stdout.write(f'Health Check Task ID: {health_result.id}')
        
        self.stdout.write(
            self.style.SUCCESS('Celery tasks submitted successfully!')
        )
```

Usage
```
python manage.py test_celery
```

```
python manage.py shell
```

```
from celery.result import AsyncResult
from crm.celery import app

# Check task status
result = AsyncResult('your-task-id-here', app=app)
print(result.status)  # PENDING, SUCCESS, FAILURE
print(result.result)  # Task return value
```
