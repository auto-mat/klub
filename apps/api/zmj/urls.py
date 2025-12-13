from django.urls import path

from .views import (
    CompanyTypesView,
    RegistrationStatusView,
    RegistrationView,
    UserProfileView,
)


urlpatterns = [
    path("user/", UserProfileView.as_view(), name="user_profile"),
    path("registration/", RegistrationView.as_view(), name="registration"),
    path("registration/status/", RegistrationStatusView.as_view(), name="registration_status"),
    path("company-types/", CompanyTypesView.as_view(), name="company_types"),
]
