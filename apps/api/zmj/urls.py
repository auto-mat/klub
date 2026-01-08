from django.urls import path
from django.conf.urls import include, url

from .example_serializer import router
from .views import (
    CompanyView,
    CompanyTypesView,
    EventContentView,
    EventOrganizersView,
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
    path(
        "events/<slug:event_slug>/content/",
        EventContentView.as_view(),
        name="event_content",
    ),
    path(
        "events/<slug:event_slug>/company/",
        CompanyView.as_view(),
        name="event_company",
    ),
    path(
        "events/<slug:event_slug>/organizers/",
        EventOrganizersView.as_view(),
        name="event_organizers",
    ),
    path("", include(router.urls), name="rest-api"),
]
