# Add to INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'graphene_django',
    'django_filters',
    'django_crontab',  # Add this line
    
    # Local apps
    'crm',
]

# Add CRONJOBS configuration at the bottom of settings.py
CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
]

# Optional: Configure cron job logging
CRONTAB_COMMAND_SUFFIX = '2>&1'  # Capture stderr as well

# If you want to use a different Python path
# CRONTAB_PYTHON_EXECUTABLE = '/usr/bin/python3'
