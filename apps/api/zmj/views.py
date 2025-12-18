from django.utils.translation import ugettext_lazy as _

from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from aklub.models import (
    CompanyProfile,
    CompanyType,
    ProfileEmail,
    Telephone,
    UserProfile,
)
from events.models import OrganizationTeam

from .serializers import (
    CompanySerializer,
    OrganizerSerializer,
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


class CompanyTypesView(APIView):
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


class UserEventsView(APIView):
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


class CompanyView(generics.GenericAPIView):
    """
    Get and update organizer company information for a specific event.

    The company is optional:
    - GET returns JSON null if no company is linked to the event yet.
    - PUT creates and links a new CompanyProfile to the event if missing, then updates it.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = CompanySerializer

    def _get_user_event_org_team(self, user, event_slug):
        """Return (event, user_org_team, error_response) ensuring user organizes the event."""
        try:
            org_team = OrganizationTeam.objects.select_related("event").get(
                profile=user, event__slug=event_slug
            )
        except OrganizationTeam.DoesNotExist:
            return None, None, Response(
                {"error": _("Event not found or you are not an organizer.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        event = org_team.event
        if not event:
            return None, None, Response(
                {"error": _("Event not found.")}, status=status.HTTP_404_NOT_FOUND
            )

        return event, org_team, None

    def _get_event_company(self, event):
        """Return the CompanyProfile linked to the event via OrganizationTeam (or None)."""
        org_team = (
            OrganizationTeam.objects.select_related("profile")
            .filter(event=event, profile__companyprofile__isnull=False)
            .first()
        )
        if not org_team:
            return None
        # `profile` is the base Profile; the child record is accessible via `.companyprofile`
        return org_team.profile.companyprofile

    def get(self, request, event_slug):
        """GET: Return company info for the event (or null if none)."""
        user = request.user
        event, _, error_response = self._get_user_event_org_team(
            user, event_slug
        )
        if error_response is not None:
            return error_response

        company = self._get_event_company(event)
        if company is None:
            return Response(None, status=status.HTTP_200_OK)

        serializer = self.get_serializer(company)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, event_slug):
        """PUT: Update company info; create+link it to the event if missing."""
        user = request.user
        event, user_org_team, error_response = self._get_user_event_org_team(
            user, event_slug
        )
        if error_response is not None:
            return error_response

        company = self._get_event_company(event)

        # If no company is linked yet, create and link it via OrganizationTeam
        if company is None:
            company = CompanyProfile.objects.create()
            # Best-effort: mirror administrative units if available
            if hasattr(event, "administrative_units") and event.administrative_units.exists():
                company.administrative_units.set(event.administrative_units.all())
            elif hasattr(user, "administrative_units") and user.administrative_units.exists():
                company.administrative_units.set(user.administrative_units.all())

            OrganizationTeam.objects.get_or_create(
                profile=company,
                event=event,
                position=user_org_team.position,
            )

        serializer = self.get_serializer(
            company, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": _("Company updated successfully.")}, status=status.HTTP_200_OK
        )


class EventOrganizersView(generics.GenericAPIView):
    """
    List + replace organizers (as a list) for a specific event.

    GET: returns a list of organizers [{id, first_name, last_name, email, telephone}, ...]
    PUT: replaces the list:
      - if item has id => update that organizer profile + primary email/telephone
      - if item has no id => create new organizer profile + contact rows
      - organizers currently linked to the event but missing from incoming list are removed from this event
    """

    permission_classes = [IsAuthenticated]

    def _get_user_event_org_team(self, user, event_slug):
        """Return (event, user_org_team, error_response) ensuring user organizes the event."""
        try:
            org_team = OrganizationTeam.objects.select_related("event").get(
                profile=user, event__slug=event_slug
            )
        except OrganizationTeam.DoesNotExist:
            return None, None, Response(
                {"error": _("Event not found or you are not an organizer.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        event = org_team.event
        if not event:
            return None, None, Response(
                {"error": _("Event not found.")}, status=status.HTTP_404_NOT_FOUND
            )

        return event, org_team, None

    def _serialize_userprofile_organizer(self, profile: UserProfile):
        try:
            email = profile.profileemail_set.get(is_primary=True).email
        except ProfileEmail.DoesNotExist:
            email_obj = profile.profileemail_set.first()
            email = email_obj.email if email_obj else None

        try:
            telephone = profile.telephone_set.get(is_primary=True).telephone
        except Telephone.DoesNotExist:
            tel_obj = profile.telephone_set.first()
            telephone = tel_obj.telephone if tel_obj else None

        return {
            "id": profile.id,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "email": email,
            "telephone": telephone,
        }

    def get(self, request, event_slug):
        user = request.user
        event, _user_org_team, error_response = self._get_user_event_org_team(
            user, event_slug
        )
        if error_response is not None:
            return error_response

        org_teams = (
            OrganizationTeam.objects.select_related("profile")
            .filter(event=event, profile__userprofile__isnull=False)
            .order_by("id")
        )

        organizers = []
        for ot in org_teams:
            organizers.append(self._serialize_userprofile_organizer(ot.profile.userprofile))

        return Response(organizers, status=status.HTTP_200_OK)

    @transaction.atomic
    def put(self, request, event_slug):
        user = request.user
        event, user_org_team, error_response = self._get_user_event_org_team(
            user, event_slug
        )
        if error_response is not None:
            return error_response

        if not isinstance(request.data, list):
            return Response(
                {"error": _("Expected a list of organizers.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrganizerSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        items = serializer.validated_data

        # Current organizers (UserProfiles only) linked to this event
        current_org_teams = OrganizationTeam.objects.filter(
            event=event, profile__userprofile__isnull=False
        )
        current_ids = set(
            current_org_teams.values_list("profile_id", flat=True)
        )

        keep_ids = set()

        for item in items:
            organizer_id = item.get("id")
            first_name = item.get("first_name")
            last_name = item.get("last_name")
            email = item.get("email")
            telephone = item.get("telephone")

            if organizer_id:
                try:
                    organizer = UserProfile.objects.get(id=organizer_id)
                except UserProfile.DoesNotExist:
                    return Response(
                        {"error": _("Organizer not found."), "id": organizer_id},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                # Ensure this organizer is currently linked to this event (prevent editing random profiles)
                if not OrganizationTeam.objects.filter(
                    event=event, profile_id=organizer.id
                ).exists():
                    return Response(
                        {
                            "error": _("Organizer is not linked to this event."),
                            "id": organizer_id,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                organizer = UserProfile.objects.create(
                    first_name=first_name or "",
                    last_name=last_name or "",
                )
                OrganizationTeam.objects.get_or_create(
                    profile=organizer,
                    event=event,
                    position=user_org_team.position,
                )

            # Update basic fields
            organizer.first_name = first_name or ""
            organizer.last_name = last_name or ""
            organizer.save()

            # Update primary email (optional)
            if email is not None:
                if email:
                    # Clear other primaries, then upsert primary
                    ProfileEmail.objects.filter(user=organizer).update(is_primary=None)
                    pe, _ = ProfileEmail.objects.get_or_create(email=email, user=organizer)
                    if not pe.is_primary:
                        pe.is_primary = True
                        pe.save()
                else:
                    ProfileEmail.objects.filter(user=organizer, is_primary=True).update(
                        is_primary=None
                    )

            # Update primary telephone (optional)
            if telephone is not None:
                if telephone:
                    Telephone.objects.filter(user=organizer).update(is_primary=None)
                    tel, _ = Telephone.objects.get_or_create(
                        telephone=telephone, user=organizer
                    )
                    if not tel.is_primary:
                        tel.is_primary = True
                        tel.save()
                else:
                    Telephone.objects.filter(user=organizer, is_primary=True).update(
                        is_primary=None
                    )

            keep_ids.add(organizer.id)

        # Remove organizers that are no longer in the list (ONLY from this event)
        remove_ids = current_ids - keep_ids
        if remove_ids:
            OrganizationTeam.objects.filter(event=event, profile_id__in=remove_ids).delete()

        # Return the updated list
        org_teams = (
            OrganizationTeam.objects.select_related("profile")
            .filter(event=event, profile__userprofile__isnull=False)
            .order_by("id")
        )
        organizers = [
            self._serialize_userprofile_organizer(ot.profile.userprofile) for ot in org_teams
        ]
        return Response(organizers, status=status.HTTP_200_OK)
