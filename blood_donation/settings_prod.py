"""
Production settings for blood_donation project.
These settings are used when deployed to Render.com
"""

from .settings import *
import os
from decouple import config

# Override DEBUG setting for production
DEBUG = config('DEBUG', default=False, cast=bool)

# Allow all hosts in production (Render handles security)
ALLOWED_HOSTS = ['*']

# Use environment variable for SECRET_KEY
SECRET_KEY = config('SECRET_KEY')

# Database configuration for production
if 'DATABASE_URL' in os.environ:
    import dj_database_url
    DATABASES['default'] = dj_database_url.config(
        default=os.environ['DATABASE_URL']
    )
else:
    # Fallback to SQLite if DATABASE_URL is not set (shouldn't happen on Render)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Production security settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Use Redis for cache if available
if 'REDIS_URL' in os.environ:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': config('REDIS_URL'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
else:
    # Fallback to in-memory cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'blood_donation_local_cache',
        }
    }

# Celery configuration for production
if 'REDIS_URL' in os.environ:
    CELERY_BROKER_URL = config('REDIS_URL')
    CELERY_RESULT_BACKEND = config('REDIS_URL')
else:
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Static files configuration for production
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Whitenoise configuration for serving static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Use modern STORAGES configuration (Django 4.2+)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "blood_donation.storage.WhiteNoiseStaticFilesStorage",
    },
}

# Email configuration - Brevo HTTP API for production (NOT SMTP)
# IMPORTANT: Use BrevoAPIEmailBackend to avoid SMTP port blocking on Render
EMAIL_BACKEND = config('EMAIL_BACKEND', default='blood_donation.email_backend.BrevoAPIEmailBackend')
BREVO_API_KEY = config('BREVO_API_KEY', default='')  # Must start with 'xkeysib-'
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@yourdomain.com')
DEFAULT_FROM_EMAIL_NAME = config('DEFAULT_FROM_EMAIL_NAME', default='Your Project Name')

# No SMTP settings needed - using HTTP API instead
# This avoids port 587 blocking on Render free tier

# Log email configuration status
import logging
logger = logging.getLogger(__name__)
if not BREVO_API_KEY or BREVO_API_KEY == '':
    logger.error("BREVO_API_KEY not configured! Email sending will FAIL!")
else:
    logger.info(f"✅ Brevo HTTP API configured for production (key length: {len(BREVO_API_KEY)})")

# Update CORS settings for production
if 'FRONTEND_URL' in os.environ:
    CORS_ALLOWED_ORIGINS = [
        config('FRONTEND_URL'),
    ]
else:
    CORS_ALLOWED_ORIGINS = [
        "https://blood-donation-platform.onrender.com",  # Replace with your actual Render URL
    ]

# Logging for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}