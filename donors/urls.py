from django.urls import path

from . import views

urlpatterns = [
    path("search/", views.DonorSearchView.as_view(), name="donor-search"),
    path("search-page/", views.DonorSearchView.as_view(), name="donor_search_page"),  # Alias for template compatibility
    path(
        "compatibility/<str:blood_group>/",
        views.compatibility_info,
        name="donor-compatibility",
    ),
    path("profile/", views.donor_profile_redirect, name="donor-profile-redirect"),  # Redirect for /donors/profile/ without ID
    path("profile/<int:user_id>/", views.donor_profile, name="donor-profile"),
    path("recommended/", views.recommended_donors, name="recommended-donors"),
]


