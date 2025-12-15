from django.utils.translation import ugettext_lazy as _

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
    UpdateEventSerializer,
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


class UserEventsView(generics.GenericAPIView):
    """
    Return all events that the authenticated user organizes.

    GET: Returns list of events with basic information.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET: Return all events user organizes"""
        user = request.user

        # Get all OrganizationTeam entries for this user
        org_teams = OrganizationTeam.objects.filter(profile=user).select_related(
            "event"
        )

        events_data = []
        for org_team in org_teams:
            event = org_team.event
            if not event:
                continue

            event_data = {
                "id": event.id,
                "slug": event.slug,
                "name": event.name,
            }

            events_data.append(event_data)

        return Response(events_data, status=status.HTTP_200_OK)


class EventDetailView(generics.GenericAPIView):
    """
    Get and update event information for events that the user organizes.

    GET: Returns event details (name, date, place, latitude, longitude,
         space_area, space_type, space_rent, activities) by slug.
    PUT: Update event details (name, date, place, latitude, longitude) by slug.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UpdateEventSerializer

    def _get_user_event(self, user, event_slug):
        """Helper method to get event if user organizes it"""
        try:
            org_team = OrganizationTeam.objects.select_related(
                "event", "event__location"
            ).get(profile=user, event__slug=event_slug)
        except OrganizationTeam.DoesNotExist:
            return None, Response(
                {"error": _("Event not found or you are not an organizer.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        event = org_team.event
        if not event:
            return None, Response(
                {"error": _("Event not found.")}, status=status.HTTP_404_NOT_FOUND
            )

        return event, None

    def get(self, request, event_slug):
        """GET: Return event details by slug"""
        user = request.user
        event, error_response = self._get_user_event(user, event_slug)
        if error_response:
            return error_response

        # Build response data
        event_data = {
            "name": event.name,
            "date": event.start_date.isoformat() if event.start_date else None,
            "place": None,
            "latitude": None,
            "longitude": None,
            "space_area": event.space_area,
            "space_type": event.space_type,
            "space_rent": event.space_rent,
            "activities": event.activities,
        }

        # Add location info if available
        if event.location:
            event_data["place"] = event.location.place
            event_data["latitude"] = event.location.gps_latitude
            event_data["longitude"] = event.location.gps_longitude

        return Response(event_data, status=status.HTTP_200_OK)

    def put(self, request, event_slug):
        """PUT: Update event information"""
        user = request.user
        event, error_response = self._get_user_event(user, event_slug)
        if error_response:
            return error_response

        serializer = self.get_serializer(event, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": _("Event updated successfully.")}, status=status.HTTP_200_OK
        )
