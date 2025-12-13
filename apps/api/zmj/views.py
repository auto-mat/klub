from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from aklub.models import (
    CompanyType,
    ProfileEmail,
    Telephone,
)
from events.models import OrganizationTeam

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


class RegistrationStatusView(generics.GenericAPIView):
    """
    Check if user registration is complete.

    GET: Returns registration status checking:
    - first_name is filled
    - last_name is filled
    - telephone is filled
    - user has an event with a name
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET: Check registration status"""
        user = request.user

        # Check first_name
        has_first_name = bool(user.first_name and user.first_name.strip())

        # Check last_name
        has_last_name = bool(user.last_name and user.last_name.strip())

        # Check telephone
        try:
            telephone = user.telephone_set.get(is_primary=True).telephone
            has_telephone = bool(telephone and telephone.strip())
        except Telephone.DoesNotExist:
            has_telephone = False

        # Check if user has an event with a name
        user_events = OrganizationTeam.objects.filter(profile=user).select_related(
            "event"
        )
        has_event_with_name = False

        for org_team in user_events:
            if org_team.event and org_team.event.name and org_team.event.name.strip():
                has_event_with_name = True
                break

        # Registration is complete if all checks pass
        is_complete = (
            has_first_name and has_last_name and has_telephone and has_event_with_name
        )

        return Response(
            {"is_complete": is_complete},
            status=status.HTTP_200_OK,
        )


class CompanyTypesView(generics.GenericAPIView):
    """
    Return all available company types.

    GET: Returns list of company types with id and type name.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET: Return all company types"""
        company_types = CompanyType.objects.all()

        return Response(
            [{"id": ct.id, "type": ct.type} for ct in company_types],
            status=status.HTTP_200_OK,
        )
