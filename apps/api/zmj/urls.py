from django.urls import path

from .views import UserProfileView


urlpatterns = [
    path("user/", UserProfileView.as_view(), name="user_profile"),
]
