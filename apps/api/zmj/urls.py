from django.urls import path

from .views import (
    CompanyTypesView,
    EventDetailView,
    RegistrationStatusView,
    RegistrationView,
    UserEventsView,
    UserProfileView,
)


urlpatterns = [
    path("user/", UserProfileView.as_view(), name="user_profile"),
    path("registration/", RegistrationView.as_view(), name="registration"),
    path(
        "registration/status/",
        RegistrationStatusView.as_view(),
        name="registration_status",
    ),
    path("company-types/", CompanyTypesView.as_view(), name="company_types"),
    path("events/", UserEventsView.as_view(), name="user_events"),
    path("events/<slug:event_slug>/", EventDetailView.as_view(), name="event_detail"),
]
