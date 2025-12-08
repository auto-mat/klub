from django.urls import path

from .views import RegistrationView, UserProfileView


urlpatterns = [
    path("user/", UserProfileView.as_view(), name="user_profile"),
    path("registration/", RegistrationView.as_view(), name="registration"),
]
