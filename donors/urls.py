from django.urls import path

from . import views

urlpatterns = [
    path("search/", views.DonorSearchView.as_view(), name="donor-search"),
    path(
        "compatibility/<str:blood_group>/",
        views.compatibility_info,
        name="donor-compatibility",
    ),
    path("profile/<int:user_id>/", views.donor_profile, name="donor-profile"),
    path("recommended/", views.recommended_donors, name="recommended-donors"),
]


