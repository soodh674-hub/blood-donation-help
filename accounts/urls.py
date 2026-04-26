from django.urls import path
from . import views
from . import health_check
from . import views_location
from . import views_report

urlpatterns = [
    # Frontend pages
    path('register/', views.register_with_otp, name='register-page'),
    path('register/', views.register_with_otp, name='register'),  # Alias for template compatibility
    path('register/donor/', views.register_donor_view, name='register-donor'),
    path('login/', views.login_view, name='login-page'),
    path('login/', views.login_view, name='login'),  # Alias for template compatibility
    path('login-enhanced/', views.login_view, name='login-enhanced'),
    path('logout/', views.logout_view, name='logout'),
    
    # OTP Login endpoints
    path('otp-login-request/', views.otp_login_request, name='otp-login-request'),
    path('otp-login-verify/', views.otp_login_verify, name='otp-login-verify'),
    
    # OTP Registration endpoints
    path('otp-register-request/', views.otp_register_request, name='otp-register-request'),
    
    # Test email endpoint
    path('test-email/', views.test_email, name='test-email'),
    path('donors/', views.donor_search_page, name='donor-search-page'),
    path('search/', views.donor_search_page, name='search-donors-page'),
    path('users/', views.user_search_page, name='user-search-page'),
    path('profile/', views.profile_page, name='profile-page'),
    path('profile/', views.profile_page, name='profile'),  # Alias for template compatibility
    path('near-me/', views.near_me_page, name='near-me-page'),
    path('near-me/', views.near_me_page, name='near_me'),  # Alias for template compatibility
    path('dashboard/', views.dashboard_page, name='dashboard-page'),
    path('dashboard/', views.dashboard_page, name='dashboard'),  # Alias for template compatibility
    # TODO: Add favorites_page view
    # path('favorites/', views.favorites_page, name='favorites'),
    path('health/', health_check.health_check, name='health-check'),
    
    # Search pages
    path('search/donors/', views.donor_search_page, name='search-donors'),
    path('search/users/', views.user_search_page, name='search-users'),
    path('search/hospitals/', views.hospital_search_page, name='search-hospitals'),
    
    # Forgot password frontend pages
    path('forgot-password/', views.forgot_password_page, name='forgot_password'),
    path('verify-otp/', views.verify_otp_page, name='verify_otp'),
    path('reset-password/', views.reset_password_page, name='reset_password'),
    
    # Legal pages
    path('terms/', views.terms_of_service_page, name='terms_of_service'),
    path('privacy/', views.privacy_policy_page, name='privacy_policy'),
    
    # Settings page
    path('settings/', views.settings_page, name='settings-page'),
    path('settings/', views.settings_page, name='settings'),  # Alias for template compatibility
    
    # API endpoints (these will be under api/accounts/ due to main urls.py configuration)
    path('api/register/', views.RegisterView.as_view(), name='register-api'),
    path('api/users/search/', views.user_search_api, name='user-search-api'),
    path('api/users/<int:user_id>/', views.user_detail_api, name='user-detail-api'),
    path('api/profile/', views.ProfileView.as_view(), name='profile-api'),
    path('api/profile/<int:pk>/', views.PublicProfileView.as_view(), name='public-profile-api'),
    path('api/profile/update/', views.update_profile, name='update-profile-api'),
    path('profile/update/', views.update_profile, name='update-profile-direct'),  # Direct access without 'api/' prefix
    
    # Email verification
    
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

    # Public Profile & Follow System (Instagram-style)
    path('profile/<int:user_id>/', views.public_profile_view, name='public-profile'),
    path('toggle-follow/<int:user_id>/', views.toggle_follow, name='toggle-follow'),
    path('<int:user_id>/followers/', views.followers_list, name='followers-list'),
    path('<int:user_id>/following/', views.following_list, name='following-list'),

    # Profile completion tracking
    path('api/profile/mark-completion-seen/', views.mark_profile_completion_seen, name='mark-profile-completion-seen'),
    
    # Location autocomplete API (Nominatim - FREE)
    path('api/location/autocomplete/', views_location.location_autocomplete, name='location-autocomplete'),
    path('api/location/reverse-geocode/', views_location.reverse_geocode, name='reverse-geocode'),
    
    # Report user API (Anti-fake system)
    path('api/report-user/', views_report.report_user, name='report-user'),
    path('api/users/<int:user_id>/trust-score/', views_report.get_user_trust_score, name='trust-score'),
    
    # Donor Rating System
    path('donor/<int:donor_id>/rate/', views.donor_rating_form, name='donor-rating-form'),
    path('donor/<int:donor_id>/rate/<int:blood_request_id>/', views.donor_rating_form, name='donor-rating-form-with-request'),
    path('api/rate-donor/', views.rate_donor, name='rate-donor'),
    path('donor/<int:donor_id>/ratings/', views.donor_ratings, name='donor-ratings'),
    path('donation-history/', views.my_donation_history, name='donation-history'),
    
    # Trust Signals & Hospital Partners
    path('hospital-partners/', views.hospital_partners, name='hospital-partners'),
    path('trust-signals/', views.trust_signals, name='trust-signals'),
    path('hospital-dashboard/', views.hospital_dashboard, name='hospital-dashboard'),
    
    # Smart Donor Matching
    path('smart-match/<int:blood_request_id>/', views.smart_donor_match, name='smart-donor-match'),
    
    # 3-Step Registration with Auto-Save
    path('register/step1/', views.register_step1, name='register-step1'),
    path('register/step2/', views.register_step2, name='register-step2'),
    path('register/step3/', views.register_step3, name='register-step3'),
    
    # Email Verification
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify-email'),
]
