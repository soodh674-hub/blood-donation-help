"""
WSGI config for blood_donation project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from django.core.wsgi import get_wsgi_application
    logger.info("Django WSGI application imported successfully")
except ImportError as e:
    logger.error(f"Failed to import Django WSGI application: {e}")
    raise

try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blood_donation.settings')
    logger.info(f"DJANGO_SETTINGS_MODULE set to: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
except Exception as e:
    logger.error(f"Failed to set DJANGO_SETTINGS_MODULE: {e}")
    raise

try:
    application = get_wsgi_application()
    logger.info("WSGI application created successfully")
except Exception as e:
    logger.error(f"Failed to create WSGI application: {e}")
    logger.error(f"Settings module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    raise