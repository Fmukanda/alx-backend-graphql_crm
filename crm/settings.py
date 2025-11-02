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
    'django_crontab',
    
    # Local apps
    'crm',
]

# GraphQL configuration
GRAPHENE = {
    'SCHEMA': 'crm.schema.schema',
    'MIDDLEWARE': [
        'graphene_django.debug.DjangoDebugMiddleware',
    ],
}

# Cron jobs configuration
CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat', '>> /tmp/crm_cron.log 2>&1'),
]

# Optional: Configure cron job logging more precisely
CRONTAB_COMMAND_SUFFIX = '2>&1'

# Cache configuration (if testing cache health)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
