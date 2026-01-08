from django.urls import path
from django.conf.urls import include, url

from .example_serializer import router
from .views import (
    CategoriesView,
    CompanyView,
    CompanyTypesView,
    EventAgreementView,
    EventChecklistItemView,
    EventChecklistView,
    EventContentView,
    EventInvoiceView,
    EventOrganizersView,
    EventDetailView,
    EventProgramDetailView,
    EventProgramsView,
    EventPublicOnWebView,
    PublicEventDetailView,
    PublicEventListView,
    RegistrationStatusView,
    RegistrationView,
    UserEventsView,
    UserProfileView,
)


urlpatterns = [
    # Public endpoints (no authentication required)
    path("public/events/", PublicEventListView.as_view(), name="public_events_list"),
    path("public/events/<slug:event_slug>/", PublicEventDetailView.as_view(), name="public_event_detail"),
    # Authenticated endpoints
    path("user/", UserProfileView.as_view(), name="user_profile"),
    path("registration/", RegistrationView.as_view(), name="registration"),
    path(
        "registration/status/",
        RegistrationStatusView.as_view(),
        name="registration_status",
    ),
    path("company-types/", CompanyTypesView.as_view(), name="company_types"),
    path("categories/", CategoriesView.as_view(), name="categories"),
    path("events/", UserEventsView.as_view(), name="user_events"),
    path("events/<slug:event_slug>/", EventDetailView.as_view(), name="event_detail"),
    path(
        "events/<slug:event_slug>/content/",
        EventContentView.as_view(),
        name="event_content",
    ),
    path(
        "events/<slug:event_slug>/public-on-web/",
        EventPublicOnWebView.as_view(),
        name="event_public_on_web",
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
    path(
        "events/<slug:event_slug>/program/",
        EventProgramsView.as_view(),
        name="event_programs",
    ),
    path(
        "events/<slug:event_slug>/program/<int:program_id>/",
        EventProgramDetailView.as_view(),
        name="event_program_detail",
    ),
    path(
        "events/<slug:event_slug>/agreement/",
        EventAgreementView.as_view(),
        name="event_agreement",
    ),
    path(
        "events/<slug:event_slug>/invoice/",
        EventInvoiceView.as_view(),
        name="event_invoice",
    ),
    path(
        "events/<slug:event_slug>/checklist/",
        EventChecklistView.as_view(),
        name="event_checklist",
    ),
    path(
        "events/<slug:event_slug>/checklist/<int:item_id>/",
        EventChecklistItemView.as_view(),
        name="event_checklist_item",
    ),
    path("", include(router.urls), name="rest-api"),
]
