from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from aklub.models import (
    ProfileEmail,
    Telephone,
)

from .serializers import (
    RegistrationSerializer,
    UpdateUserProfileSerializer,
)


class UserProfileView(generics.GenericAPIView):
    """
    Get and update authenticated user's profile information.

    GET: Retrieve user info (firstname, lastname, email, telephone, sex, language).
    PUT: Update user profile information.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UpdateUserProfileSerializer

    def get(self, request):
        """GET: Retrieve user info"""
        user = request.user

        try:
            email = user.profileemail_set.get(is_primary=True).email
        except ProfileEmail.DoesNotExist:
            email_obj = user.profileemail_set.first()
            email = email_obj.email if email_obj else None

        try:
            telephone = user.telephone_set.get(is_primary=True).telephone
        except Telephone.DoesNotExist:
            telephone_obj = user.telephone_set.first()
            telephone = telephone_obj.telephone if telephone_obj else None

        return Response(
            {
                "firstname": user.first_name,
                "lastname": user.last_name,
                "email": email,
                "telephone": telephone,
                "sex": user.sex,
                "language": user.language,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        """PUT: Update user profile"""
        user = self.request.user
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)


class RegistrationView(generics.GenericAPIView):
    """
    Registration endpoint for authenticated users.
    
    POST: Save registration information.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = RegistrationSerializer

    def post(self, request):
        """POST: Save registration information"""
        user = request.user
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Registration information saved successfully"},
            status=status.HTTP_200_OK,
        )
