from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.utils.translation import ugettext_lazy as _

from allauth.account.views import ConfirmEmailView
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.registration.views import RegisterView
from rest_framework import status
from rest_framework.response import Response

from aklub.models import UserProfile


class CustomRegisterSerializer(RegisterSerializer):
    username = None  # Remove the username field

    def save(self, request):
        password = self.validated_data.pop("password1")
        del self.validated_data["password2"]
        user = UserProfile(**self.validated_data)
        username = user.email.split("@")[0]  # Calculate username from email
        user_number = get_user_model().objects.count()
        user.username = f"{username}@{user_number}"
        user.set_password(password)
        user.save()
        return user


class CustomRegisterView(RegisterView):
    serializer_class = CustomRegisterSerializer


class ConfirmEmailView(ConfirmEmailView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.confirm(request)
        return JsonResponse(
            {"status": "success", "message": _("Email was confirmed successfully.")},
            status=status.HTTP_200_OK,
        )
