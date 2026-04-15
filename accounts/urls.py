from django.urls import path
from . import views
from . import health_check

urlpatterns = [
    # Frontend pages
    path('register/', views.donor_registration_view, name='register-page'),
    path('register/donor/', views.register_donor_view, name='register-donor'),
    path('login/', views.login_view, name='login-page'),
    path('logout/', views.logout_view, name='logout'),
    path('donors/', views.donor_search_page, name='donor-search-page'),
    path('search/', views.donor_search_page, name='search-donors-page'),
    path('users/', views.user_search_page, name='user-search-page'),
    path('profile/', views.profile_page, name='profile-page'),
    path('near-me/', views.near_me_page, name='near-me-page'),
    path('dashboard/', views.dashboard_page, name='dashboard-page'),
    path('health/', health_check.health_check, name='health-check'),
    
    # Search pages
    path('search/donors/', views.donor_search_page, name='search-donors'),
    path('search/users/', views.user_search_page, name='search-users'),
    
    # Forgot password frontend pages
    path('forgot-password/', views.forgot_password_page, name='forgot_password'),
    path('verify-otp/', views.verify_otp_page, name='verify_otp'),
    path('reset-password/', views.reset_password_page, name='reset_password'),
    
    # Legal pages
    path('terms/', views.terms_of_service_page, name='terms_of_service'),
    path('privacy/', views.privacy_policy_page, name='privacy_policy'),
    
    # Settings page
    path('settings/', views.settings_page, name='settings-page'),
    
    # API endpoints (these will be under api/accounts/ due to main urls.py configuration)
    path('api/register/', views.RegisterView.as_view(), name='register-api'),
    path('api/users/search/', views.user_search_api, name='user-search-api'),
    path('api/users/<int:user_id>/', views.user_detail_api, name='user-detail-api'),
    path('api/profile/', views.ProfileView.as_view(), name='profile-api'),
    path('api/profile/<int:pk>/', views.PublicProfileView.as_view(), name='public-profile-api'),
    path('api/profile/update/', views.update_profile, name='update-profile-api'),
    path('profile/update/', views.update_profile, name='update-profile-direct'),  # Direct access without 'api/' prefix
    
    # Email verification
    path('verify-email/', views.verify_email, name='verify-email'),
    
    # Password reset API endpoints
    path('api/forgot-password/', views.forgot_password, name='forgot-password-api'),
    path('api/verify-otp/', views.verify_otp, name='verify-otp-api'),
    path('api/reset-password/', views.reset_password, name='reset-password-api'),
    
    # Settings API endpoints
    path('api/settings/update/', views.update_user_settings, name='update-settings-api'),
    path('api/settings/change-password/', views.change_password, name='change-password-api'),

    # Phase 2: Profile editing
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('remove-profile-photo/', views.remove_profile_photo, name='remove_profile_photo'),

    # Phase 2: Favorites
    path('favorites/', views.favorites_list, name='favorites_list'),
    path('toggle-favorite/<int:donor_id>/', views.toggle_favorite_donor, name='toggle_favorite'),

]