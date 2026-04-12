import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blood_donation.settings')

app = Celery('blood_donation')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Celery Beat Schedule
app.conf.beat_schedule = {
    'send-donation-reminders': {
        'task': 'notifications.tasks.send_donation_reminders',
        'schedule': 86400.0,  # Every 24 hours
    },
    'cleanup-expired-requests': {
        'task': 'requests.tasks.cleanup_expired_requests',
        'schedule': 3600.0,  # Every hour
    },
    'update-donor-availability': {
        'task': 'donors.tasks.update_donor_availability',
        'schedule': 43200.0,  # Every 12 hours
    },
    'generate-daily-analytics': {
        'task': 'analytics.tasks.generate_daily_analytics',
        'schedule': 86400.0,  # Every 24 hours
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