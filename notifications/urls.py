from django.urls import path

from . import views

app_name = 'notifications'

urlpatterns = [
    # Existing notification URLs
    path("", views.notification_list, name="notifications-page"),
    path("api/list/", views.NotificationListView.as_view(), name="notification-list"),
    path("api/blood-requests/", views.get_blood_request_notifications, name="blood-request-notifications"),
    path("api/<int:pk>/read/", views.mark_notification_read, name="notification-mark-read"),
    
    # NEW: Donation status update popup feature
    path('api/update-status/', views.update_donation_status, name='update_donation_status'),
    path('list/', views.notification_list, name='notification-list-full'),
    path('<int:notification_id>/mark-read/', views.mark_notification_as_read, name='mark-notification-read'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark-all-read'),
]


