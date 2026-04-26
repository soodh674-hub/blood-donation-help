"""
Django settings for blood donation platform.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
import logging
import warnings
from pathlib import Path
from decouple import config

# Suppress common deprecation warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='pkg_resources is deprecated')
warnings.filterwarnings('ignore', message='pkg_resources')

# Set up logging for settings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Check if we're running on Render (multiple detection methods)
IS_RENDER = any([
    'RENDER' in os.environ,
    'RENDER_SERVICE_ID' in os.environ,
    'RENDER_SERVICE_NAME' in os.environ,
    os.environ.get('DYNO'),  # Also detect Heroku-like environments
])

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-development-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Allow specific hosts in production for security
if IS_RENDER:
    # Production: Allow Render domains and custom domain
    ALLOWED_HOSTS = config(
        'ALLOWED_HOSTS', 
        default='bloodis-life.online,.onrender.com,localhost,127.0.0.1',
        cast=lambda v: [s.strip() for s in v.split(',')]
    )
else:
    # Development: Local hosts only
    ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

logger.info(f"IS_RENDER: {IS_RENDER}")
logger.info(f"SECRET_KEY length: {len(SECRET_KEY) if SECRET_KEY else 0}")
logger.info(f"DEBUG: {DEBUG}")
logger.info(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")

# Application definition

INSTALLED_APPS = [
    'daphne',  # Must be first for ASGI
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Django allauth for email verification
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',
    'django_redis',
    'auditlog',
    'captcha',
    'rangefilter',
    'axes',  # Login rate limiting and brute force protection
    'channels',
    
    # Custom apps
    'accounts',
    'donors',
    'blood_requests_app',
    'notifications',
    'analytics',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Required by django-allauth
    'axes.middleware.AxesMiddleware',  # Login rate limiting and brute force protection
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.security_middleware.SecurityMiddleware',  # Security middleware to block attacks
    'auditlog.middleware.AuditlogMiddleware',
    'apps.core.middleware.RateLimitMiddleware',
]

# Authentication Backends - Required for django-axes
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # Modern django-axes backend (replaces AxesModelBackend)
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = 'blood_donation.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Custom context processors
                'apps.core.context_processors.smart_banner_context',
                'apps.core.context_processors.notification_count_context',
                'notifications.context_processors.donation_status_popup',
            ],
        },
    },
]

WSGI_APPLICATION = 'blood_donation.wsgi.application'

# Django Channels configuration for WebSocket support
ASGI_APPLICATION = 'blood_donation.asgi.application'

# Channel layers configuration (Redis for production, in-memory for development)
if IS_RENDER:
    # Production - use Redis from environment
    REDIS_URL = config('REDIS_URL', default='')
    if REDIS_URL:
        CHANNEL_LAYERS = {
            'default': {
                'BACKEND': 'channels_redis.core.RedisChannelLayer',
                'CONFIG': {
                    'hosts': [REDIS_URL],
                },
            },
        }
    else:
        # Fallback to in-memory channel layer (not recommended for production)
        CHANNEL_LAYERS = {
            'default': {
                'BACKEND': 'channels.layers.InMemoryChannelLayer',
            },
        }
else:
    # Development - try to use Redis
    REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/1')
    try:
        import redis
        redis_client = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=2, socket_timeout=2)
        redis_client.ping()
        # Redis is available, use it for channels
        CHANNEL_LAYERS = {
            'default': {
                'BACKEND': 'channels_redis.core.RedisChannelLayer',
                'CONFIG': {
                    'hosts': [REDIS_URL],
                },
            },
        }
        logger.info("Using Redis for Channels layer")
    except Exception as e:
        # Redis not available, use in-memory channel layer
        CHANNEL_LAYERS = {
            'default': {
                'BACKEND': 'channels.layers.InMemoryChannelLayer',
            },
        }
        logger.info(f"Using in-memory channel layer (Redis not available): {e}")

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

if IS_RENDER:
    # Running on Render - use PostgreSQL
    import dj_database_url
    
    # Try DATABASE_URL first
    DATABASE_URL = config('DATABASE_URL', default='')
    
    if DATABASE_URL:
        # Add sslmode=require if not present (fixes IPv6 issues)
        if '?' not in DATABASE_URL:
            DATABASE_URL = DATABASE_URL + '?sslmode=require'
        
        DATABASES = {
            'default': dj_database_url.config(
                default=DATABASE_URL,
                conn_max_age=600,
                conn_health_checks=True,
            )
        }
        # Ensure the engine is set correctly
        DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'
        logger.info(f"Using PostgreSQL database from DATABASE_URL: {DATABASES['default'].get('NAME', 'Unknown')}")
        logger.info(f"Database host: {DATABASES['default'].get('HOST', 'Unknown')}")
    else:
        # Try individual Supabase variables
        SUPABASE_HOST = config('SUPABASE_HOST', default='')
        SUPABASE_PORT = config('SUPABASE_PORT', default='5432')
        SUPABASE_DBNAME = config('SUPABASE_DBNAME', default='postgres')
        SUPABASE_USER = config('SUPABASE_USER', default='postgres')
        SUPABASE_PASSWORD = config('SUPABASE_PASSWORD', default='')
        SUPABASE_PROJECT_REF = config('SUPABASE_PROJECT_REF', default='')
        
        if SUPABASE_HOST and SUPABASE_PASSWORD:
            # Use direct connection with SSL (most reliable for Supabase)
            clean_host = SUPABASE_HOST.strip('[]')
            
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': SUPABASE_DBNAME,
                    'USER': SUPABASE_USER,
                    'PASSWORD': SUPABASE_PASSWORD,
                    'HOST': clean_host,
                    'PORT': SUPABASE_PORT,
                    'CONN_MAX_AGE': 600,
                    'CONN_HEALTH_CHECKS': True,
                    # SSL mode REQUIRED for Supabase
                    'OPTIONS': {
                        'connect_timeout': 10,
                        'sslmode': 'require',
                    },
                }
            }
            logger.info(f"Using PostgreSQL database from SUPABASE_* variables: {SUPABASE_DBNAME}")
            logger.info(f"Database host: {clean_host}")

        else:
            # Fallback to SQLite if no database configuration
            logger.warning("No DATABASE_URL or SUPABASE_* found, using SQLite fallback")
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': BASE_DIR / 'db.sqlite3',
                }
            }

else:
    # Local development - use SQLite for now (add Supabase credentials to .env to switch)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    logger.info("⚠️ Using SQLite (Add SUPABASE_HOST and SUPABASE_PASSWORD to .env to use Supabase)")

# Cache configuration
if IS_RENDER:
    # Production cache settings (Redis)
    REDIS_URL = config('REDIS_URL', default='')
    if REDIS_URL:
        CACHES = {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': REDIS_URL,
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
else:
    # Development cache settings
    # Try to use Redis if available
    REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/1')
    try:
        import redis
        redis_client = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=2, socket_timeout=2)
        redis_client.ping()
        # Redis is available
        CACHES = {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': REDIS_URL,
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                }
            }
        }
        logger.info("Using Redis cache")
    except Exception as e:
        # Redis not available, use local memory cache
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'blood_donation_local_cache',
            }
        }
        logger.info(f"Using local memory cache (Redis not available): {e}")

# Celery Configuration
if IS_RENDER:
    # Production Celery settings
    REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    # Check if we are defaulting to localhost Redis, and if so, safely fallback to synchronous
    if 'localhost' in REDIS_URL or '127.0.0.1' in REDIS_URL:
        logger.warning('Localhost Redis detected in production/Render. Falling back to CELERY_TASK_ALWAYS_EAGER=True to bypass connection errors.')
        CELERY_TASK_ALWAYS_EAGER = True
        CELERY_BROKER_URL = 'memory://'
        CELERY_RESULT_BACKEND = 'cache+memory://'
else:
    # Development Celery settings
    # For local development, use Redis if available, otherwise fallback to memory
    REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
    try:
        import redis
        redis_client = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=2, socket_timeout=2)
        redis_client.ping()
        # Redis is available
        CELERY_BROKER_URL = REDIS_URL
        CELERY_RESULT_BACKEND = REDIS_URL
        logger.info("Using Redis for Celery")
    except Exception as e:
        # Redis not available, use memory broker
        CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='memory://')
        CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='cache+memory://')
        logger.info(f"Using memory broker for Celery (Redis not available): {e}")

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Celery Beat Scheduler
CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-otps': {
        'task': 'accounts.tasks.cleanup_expired_otps',
        'schedule': 300.0,  # Every 5 minutes
    },
    
    # ========================================================================
    # PHASE 6: STATUS WORKFLOW ENGINE TASKS
    # ========================================================================
    
    'check-expired-requests': {
        'task': 'blood_requests_app.tasks.check_expired_requests',
        'schedule': 3600.0,  # Every hour
    },
    'send-expiry-warnings': {
        'task': 'blood_requests_app.tasks.send_expiry_warnings',
        'schedule': 1800.0,  # Every 30 minutes
    },
    'update-request-status-automatically': {
        'task': 'blood_requests_app.tasks.update_request_status_automatically',
        'schedule': 900.0,  # Every 15 minutes
    },
    'notify-donors-of-nearby-emergency': {
        'task': 'blood_requests_app.tasks.notify_donors_of_nearby_emergency',
        'schedule': 600.0,  # Every 10 minutes
    },
    'cleanup-old-completed-requests': {
        'task': 'blood_requests_app.tasks.cleanup_old_completed_requests',
        'schedule': 86400.0,  # Daily at midnight
        'options': {'kwargs': {'days_old': 30}}
    },
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Check if static directory exists before adding it
import os
if os.path.exists(BASE_DIR / 'static'):
    STATICFILES_DIRS = [BASE_DIR / 'static']
else:
    STATICFILES_DIRS = []

# Serve static files with WhiteNoise
if IS_RENDER:
    # Use modern STORAGES configuration (Django 4.2+)
    # Using CompressedStaticFilesStorage (no manifest) to avoid missing file errors
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "blood_donation.storage.WhiteNoiseStaticFilesStorage",
        },
    }
else:
    # Development - use simple static files storage
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
}

# Email Configuration

# Custom password reset email template
PASSWORD_RESET_EMAIL_TEMPLATE = 'emails/password_reset_email.html'

# Email Configuration
if IS_RENDER:
    # Production email settings for Render with Brevo HTTP API
    # Using HTTP API backend since BREVO_API_KEY is an API key, not SMTP key
    
    EMAIL_BACKEND = 'accounts.backends.BrevoEmailBackend'
    BREVO_API_KEY = config('BREVO_API_KEY', default='')
    DEFAULT_FROM_EMAIL = 'hsood3560@gmail.com'
    SERVER_EMAIL = 'hsood3560@gmail.com'
    
    logger.info(f"✅ Brevo HTTP API configured for email sending")
    
    # Maps: Using FREE OpenStreetMap + Leaflet (NO API KEY REQUIRED!)
    # Optional: Google Maps API key if you prefer Google over OpenStreetMap
    GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY', default='')
    if GOOGLE_MAPS_API_KEY and GOOGLE_MAPS_API_KEY != 'your-google-maps-api-key-here':
        logger.info(f"ℹ️ Google Maps API configured (optional) - key length: {len(GOOGLE_MAPS_API_KEY)}")
    else:
        logger.info("✅ Using FREE OpenStreetMap + Leaflet (no API key required)")
    
    # WebSocket Configuration for Real-time Chat and Notifications
    # Using Django Channels for real-time features instead of Firebase
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [(config('REDIS_URL', default='redis://localhost:6379/0'), 6379)],
            },
        },
    }
    
    logger.info("✅ WebSocket configured for real-time chat and notifications using Django Channels")
    
    # Location Autocomplete API (Nominatim - FREE)
    NOMINATIM_API_URL = "https://nominatim.openstreetmap.org/search"
    NOMINATIM_USER_AGENT = "BloodDonationApp/1.0"
    
    # SITE_URL for email verification links
    SITE_URL = config('SITE_URL', default='https://bloodis-life.online')
else:
    # Development email settings
    EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.filebased.EmailBackend')
    EMAIL_FILE_PATH = BASE_DIR / 'emails'  # Store emails in a file during development
    EMAIL_HOST = config('EMAIL_HOST', default='localhost')
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='soodh674@gmail.com')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='buod vlpk ltrg awpv')
    DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='soodh674@gmail.com')
    
    # Maps: Using FREE OpenStreetMap + Leaflet (NO API KEY REQUIRED!)
    GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY', default='')
    
    # SITE_URL for email verification links (local development)
    SITE_URL = config('SITE_URL', default='http://localhost:8000')

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

CORS_ALLOW_CREDENTIALS = True

# Security Settings
if IS_RENDER:
    # Production security settings
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True  # HTTPS only in production
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
else:
    # Development settings
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_COOKIE_SECURE = False  # Allow HTTP in development
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development

# Session Security Settings
SESSION_COOKIE_AGE = 1800  # 30 minutes
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection

# Logging Configuration
# Logging Configuration
import os

# Create logs directory if it doesn't exist (for local development)
LOGS_DIR = BASE_DIR / 'logs'
if not IS_RENDER:
    LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
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

# Add file handler only in local development (not on Render)
if not IS_RENDER:
    LOGGING['handlers']['file'] = {
        'level': 'INFO',
        'class': 'logging.FileHandler',
        'filename': LOGS_DIR / 'django.log',
        'formatter': 'verbose',
    }
    LOGGING['root']['handlers'].append('file')
    LOGGING['loggers']['django']['handlers'].append('file')

# GDPR Compliance Notice
GDPR_COMPLIANCE_ENABLED = True

# Django Channels Configuration
# Note: CHANNEL_LAYERS is already configured above based on IS_RENDER
# The configuration below is deprecated and kept for reference only
# ASGI_APPLICATION = 'blood_donation.asgi.application'  # Already set above

# ========================================================================
# DEPRECATED CHANNEL_LAYERS CONFIGURATION (DO NOT USE)
# ========================================================================
# The CHANNEL_LAYERS is already configured dynamically above based on:
# - IS_RENDER environment detection
# - REDIS_URL availability
# - Development vs Production settings
# ========================================================================

# Django Axes Configuration - Login Rate Limiting (Modern Settings)
AXES_FAILURE_LIMIT = 5  # Lock out after 5 failed attempts
AXES_COOLOFF_TIME = 1  # Lock out for 1 hour (in hours, not minutes)
AXES_RESET_ON_SUCCESS = True  # Reset counter on successful login
AXES_LOCKOUT_TEMPLATE = 'axes/lockout.html'  # Custom lockout template
AXES_VERBOSE = True  # Enable verbose logging for debugging
AXES_DISABLE_ACCESS_LOG = False  # Enable access logging
# Remove deprecated AXES_ONLY_USER_FAILURES setting
# AXES_ONLY_USER_FAILURES = False  # This setting is deprecated in AXES 8.x

# Django Allauth Configuration - Email Verification
SITE_ID = 1
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # or 'optional' or 'none'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'

# Note: Email backend is already configured above based on IS_RENDER
# The configuration below is deprecated and will be overridden

# Django CAPTCHA Configuration
CAPTCHA_NOISE_FUNCTIONS = ('captcha.helpers.noise_arcs', 'captcha.helpers.noise_dots')
CAPTCHA_LENGTH = 6
CAPTCHA_FONT_SIZE = 30
CAPTCHA_WIDTH = 200
CAPTCHA_HEIGHT = 50
CAPTCHA_TIMEOUT = 300  # 5 minutes
CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.math_challenge'  # Use math challenge instead of text

# ===========================================
# SECURITY HEADERS - Production Hardening
# ===========================================
# Note: Security settings are already configured above based on IS_RENDER
# The settings below are deprecated and will be overridden by the IS_RENDER logic

# Security Middleware Settings (Already set above)
# SECURE_BROWSER_XSS_FILTER = True  # Already configured
# SECURE_CONTENT_TYPE_NOSNIFF = True  # Already configured
# X_FRAME_OPTIONS = 'DENY'  # Already configured
# SECURE_HSTS_SECONDS = 31536000  # Already configured
# SECURE_SSL_REDIRECT = False  # Already configured

# CSRF Security (Already configured above with IS_RENDER logic)
# CSRF_COOKIE_SECURE - Set based on IS_RENDER
# CSRF_COOKIE_HTTPONLY = False  # Already set above
# CSRF_COOKIE_SAMESITE = 'Lax'  # Already set above

# Session Security (Already configured above with IS_RENDER logic)
# SESSION_COOKIE_SECURE - Set based on IS_RENDER
# SESSION_COOKIE_HTTPONLY = True  # Already set above
# SESSION_COOKIE_SAMESITE = 'Lax'  # Already set above

# Additional Security Settings
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'  # Control referrer information
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'  # Prevent cross-origin attacks

# Password Validation (Stronger Passwords)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
