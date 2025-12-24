from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from aklub.models import (
    CompanyProfile,
    CompanyType,
    Preference,
    ProfileEmail,
    Telephone,
    UserProfile,
)
from events.models import (
    Category,
    Event,
    EventChecklistItem,
    OrganizationTeam,
)

from .serializers import (
    AgreementSignedUploadSerializer,
    AgreementStatusSerializer,
    CompanySerializer,
    EventChecklistItemSerializer,
    EventContentSerializer,
    EventProgramSerializer,
    InvoiceStatusSerializer,
    OrganizerSerializer,
    RegistrationSerializer,
    UpdateEventSerializer,
    UpdateUserProfileSerializer,
)


class EventAccessMixin:
    """Mixin providing helper methods for accessing events that the user organizes."""

    def _get_user_event(self, user, event_slug):
        """Helper method to get event if user organizes it"""
        try:
            org_team = OrganizationTeam.objects.select_related("event").get(
                profile=user, event__slug=event_slug
            )
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


class UserProfileView(generics.GenericAPIView):
    """
    Get and update authenticated user's profile information.

    GET: Retrieve user info (firstname, lastname, email, telephone, sex, language, 
         send_mailing_lists, newsletter_on).
    PUT: Update user profile information (all fields).
    PATCH: Partially update user profile information (only provided fields).
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

        # Get preference values (from first administrative unit)
        send_mailing_lists = None
        newsletter_on = None
        admin_unit = user.administrative_units.first()
        if admin_unit:
            try:
                preference = Preference.objects.get(user=user, administrative_unit=admin_unit)
                send_mailing_lists = preference.send_mailing_lists
                newsletter_on = preference.newsletter_on
            except Preference.DoesNotExist:
                # Use defaults if preference doesn't exist
                send_mailing_lists = True  # Default from model
                newsletter_on = False  # Default from model

        return Response(
            {
                "firstname": user.first_name,
                "lastname": user.last_name,
                "email": email,
                "telephone": telephone,
                "sex": user.sex,
                "language": user.language,
                "send_mailing_lists": send_mailing_lists,
                "newsletter_on": newsletter_on,
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

    def patch(self, request):
        """PATCH: Partially update user profile"""
        user = self.request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
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


class CategoriesView(APIView):
    """
    Return all available categories.

    GET: Returns list of categories with id, name, slug, and description.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET: Return all categories"""
        categories = Category.objects.all()
        return Response(
            [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "slug": cat.slug,
                    "description": cat.description or "",
                }
                for cat in categories
            ],
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


class CompanyView(EventAccessMixin, generics.GenericAPIView):
    """
    Get and update organizer company information for a specific event.

    The company is optional:
    - GET returns JSON null if no company is linked to the event yet.
    - PUT creates and links a new CompanyProfile to the event if missing, then updates it.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = CompanySerializer

    def _get_event_company(self, event):
        """Return the CompanyProfile linked to the event via OrganizationTeam (or None)."""
        org_team = (
            OrganizationTeam.objects.select_related("profile")
            .filter(
                event=event,
                profile__polymorphic_ctype__model=CompanyProfile._meta.model_name,
            )
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


class EventOrganizersView(EventAccessMixin, generics.GenericAPIView):
    """
    List + replace organizers (as a list) for a specific event.

    GET: returns a list of organizers [{id, first_name, last_name, email, telephone}, ...]
    PUT: replaces the list:
      - if item has id => update that organizer profile + primary email/telephone
      - if item has no id => create new organizer profile + contact rows
      - organizers currently linked to the event but missing from incoming list are removed from this event
    """

    permission_classes = [IsAuthenticated]

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
            .filter(
                event=event,
                profile__polymorphic_ctype__model=UserProfile._meta.model_name,
            )
            .exclude(profile_id=user.id)  # Exclude the authenticated user
            .order_by("id")
        )

        organizers = []
        for ot in org_teams:
            # ot.profile is already a UserProfile instance due to polymorphic filtering
            # but we need to ensure it's the correct type for accessing userprofile methods
            if isinstance(ot.profile, UserProfile):
                organizers.append(self._serialize_userprofile_organizer(ot.profile))
            else:
                # Fallback: get the UserProfile instance explicitly
                user_profile = UserProfile.objects.get(id=ot.profile.id)
                organizers.append(self._serialize_userprofile_organizer(user_profile))

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
            event=event,
            profile__polymorphic_ctype__model=UserProfile._meta.model_name,
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

            # Update basic fields (only if provided)
            if first_name is not None:
                organizer.first_name = first_name or ""
            if last_name is not None:
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

        # Always keep the authenticated user as an organizer (prevent self-removal)
        keep_ids.add(user.id)

        # Remove organizers that are no longer in the list (ONLY from this event)
        # Exclude the authenticated user from removal
        remove_ids = current_ids - keep_ids
        if remove_ids:
            OrganizationTeam.objects.filter(
                event=event, profile_id__in=remove_ids
            ).exclude(profile_id=user.id).delete()

        # Return the updated list (excluding the authenticated user)
        org_teams = (
            OrganizationTeam.objects.select_related("profile")
            .filter(
                event=event,
                profile__polymorphic_ctype__model=UserProfile._meta.model_name,
            )
            .exclude(profile_id=user.id)  # Exclude the authenticated user
            .order_by("id")
        )
        organizers = []
        for ot in org_teams:
            # ot.profile is already a UserProfile instance due to polymorphic filtering
            if isinstance(ot.profile, UserProfile):
                organizers.append(self._serialize_userprofile_organizer(ot.profile))
            else:
                # Fallback: get the UserProfile instance explicitly
                user_profile = UserProfile.objects.get(id=ot.profile.id)
                organizers.append(self._serialize_userprofile_organizer(user_profile))
        return Response(organizers, status=status.HTTP_200_OK)


class EventContentView(EventAccessMixin, generics.GenericAPIView):
    """
    Get and update event content for a specific event.

    GET: Returns event content (main_photo URL, description, url + title, url1 + title1, url2 + title2).
    PUT: Updates event content fields.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = EventContentSerializer

    def get(self, request, event_slug):
        """GET: Return event content"""
        user = request.user
        event, error_response = self._get_user_event(user, event_slug)
        if error_response:
            return error_response

        serializer = self.get_serializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, event_slug):
        """PUT: Update event content"""
        user = request.user
        event, error_response = self._get_user_event(user, event_slug)
        if error_response:
            return error_response

        serializer = self.get_serializer(event, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": _("Event content updated successfully.")},
            status=status.HTTP_200_OK,
        )


class EventPublicOnWebView(EventAccessMixin, APIView):
    """
    Check if event content is public on web.

    GET: Returns the public_on_web boolean flag.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, event_slug):
        """GET: Return public_on_web flag"""
        user = request.user
        event, error_response = self._get_user_event(user, event_slug)
        if error_response:
            return error_response

        return Response(
            {"public_on_web": event.public_on_web},
            status=status.HTTP_200_OK,
        )


class EventProgramsView(EventAccessMixin, APIView):
    """
    Manage programs (child events) for an event.

    GET /events/<slug>/programs/: List all programs for the event
    POST /events/<slug>/programs/: Create a new program
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, event_slug):
        """GET: Return all programs (child events) for the event"""
        user = request.user
        event, error_response = self._get_user_event(user, event_slug)
        if error_response:
            return error_response

        programs = event.tn_children.all().order_by('datetime_from')
        serializer = EventProgramSerializer(programs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, event_slug):
        """POST: Create a new program (child event) for the event"""
        user = request.user
        event, error_response = self._get_user_event(user, event_slug)
        if error_response:
            return error_response

        serializer = EventProgramSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        program = serializer.create(serializer.validated_data, event)

        return Response(
            EventProgramSerializer(program).data,
            status=status.HTTP_201_CREATED,
        )


class EventProgramDetailView(EventAccessMixin, APIView):
    """
    Get, update, or delete a specific program (child event).

    GET /events/<slug>/programs/<id>/: Get program details
    PUT /events/<slug>/programs/<id>/: Update program
    PATCH /events/<slug>/programs/<id>/: Partially update program
    DELETE /events/<slug>/programs/<id>/: Delete program
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, event_slug, program_id):
        """GET: Return program details"""
        user = request.user
        event, error_response = self._get_user_event(user, event_slug)
        if error_response:
            return error_response

        try:
            program = event.tn_children.get(id=program_id)
        except Event.DoesNotExist:
            return Response(
                {"error": _("Program not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EventProgramSerializer(program)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, event_slug, program_id):
        """PUT: Update program"""
        return self._update_program(request, event_slug, program_id, partial=False)

    def patch(self, request, event_slug, program_id):
        """PATCH: Partially update program"""
        return self._update_program(request, event_slug, program_id, partial=True)

    def delete(self, request, event_slug, program_id):
        """DELETE: Delete program"""
        user = request.user
        event, error_response = self._get_user_event(user, event_slug)
        if error_response:
            return error_response

        try:
            program = event.tn_children.get(id=program_id)
        except Event.DoesNotExist:
            return Response(
                {"error": _("Program not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        program.delete()
        return Response(
            {"message": _("Program deleted successfully.")},
            status=status.HTTP_200_OK,
        )

    def _update_program(self, request, event_slug, program_id, partial=False):
        """Helper method to update program"""
        user = request.user
        event, error_response = self._get_user_event(user, event_slug)
        if error_response:
            return error_response

        try:
            program = event.tn_children.get(id=program_id)
        except Event.DoesNotExist:
            return Response(
                {"error": _("Program not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EventProgramSerializer(program, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_program = serializer.update(program, serializer.validated_data)

        return Response(
            EventProgramSerializer(updated_program).data,
            status=status.HTTP_200_OK,
        )


class EventAgreementView(EventAccessMixin, generics.GenericAPIView):
    """
    Get and update event agreement status and files.

    GET: Returns agreement status and conditional PDF files:
        - Always: status
        - If status = "sent" or "rejected": pdf_file
        - If status = "completed": pdf_file_completed
    
    POST: Upload signed agreement PDF (pdf_file_signed)
        - Only allowed when status is "sent" or "rejected"
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, event_slug):
        """GET: Return agreement status and conditional PDF files"""
        user = request.user
        event, error_response = self._get_user_event(user, event_slug)
        if error_response:
            return error_response

        # Get the most recent agreement for this event, or return None
        agreement = event.agreements.order_by("-created").first()
        
        if not agreement:
            return Response(
                {"status": None, "pdf_file": None, "pdf_file_completed": None},
                status=status.HTTP_200_OK,
            )

        serializer = AgreementStatusSerializer(agreement)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, event_slug):
        """POST: Upload signed agreement PDF"""
        user = request.user
        event, error_response = self._get_user_event(user, event_slug)
        if error_response:
            return error_response

        # Get the most recent agreement for this event
        agreement = event.agreements.order_by("-created").first()
        
        if not agreement:
            return Response(
                {"error": _("No agreement found for this event.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if status allows uploading signed file
        if agreement.status not in ["sent", "rejected"]:
            return Response(
                {
                    "error": _(
                        "Cannot upload signed agreement. Agreement status must be 'sent' or 'rejected'."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AgreementSignedUploadSerializer(
            agreement, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": _("Signed agreement uploaded successfully.")},
            status=status.HTTP_200_OK,
        )


class EventInvoiceView(EventAccessMixin, generics.GenericAPIView):
    """
    Get event invoice status and file.

    GET: Returns invoice status and conditional PDF file:
        - Always: status
        - If status = "sent", "reminded", or "overdue": pdf_file
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, event_slug):
        """GET: Return invoice status and conditional PDF file"""
        user = request.user
        event, error_response = self._get_user_event(user, event_slug)
        if error_response:
            return error_response

        # Get the most recent invoice for this event, or return None
        invoice = event.invoices.order_by("-created").first()
        
        if not invoice:
            return Response(
                {"status": None, "pdf_file": None},
                status=status.HTTP_200_OK,
            )

        serializer = InvoiceStatusSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EventChecklistView(EventAccessMixin, generics.GenericAPIView):
    """
    Get and manage checklist items for an event.

    GET: Returns two arrays:
        - predefined: checklist items with custom=False (read-only)
        - custom: checklist items with custom=True (editable)
    PUT: Replace the list of custom checklist items (list replacement pattern):
        - Items with 'id' are updated
        - Items without 'id' are created
        - Custom items present in the event but not in the payload are deleted
    """

    permission_classes = [IsAuthenticated]
    serializer_class = EventChecklistItemSerializer

    def get(self, request, event_slug):
        """GET: Return predefined and custom checklist items as separate arrays"""
        user = request.user
        event, error_response = self._get_user_event(user, event_slug)
        if error_response:
            return error_response

        # Get predefined items (custom=False)
        predefined_items = event.checklist_items.filter(custom=False).order_by("id")
        predefined_serializer = EventChecklistItemSerializer(predefined_items, many=True)

        # Get custom items (custom=True)
        custom_items = event.checklist_items.filter(custom=True).order_by("id")
        custom_serializer = EventChecklistItemSerializer(custom_items, many=True)

        return Response(
            {
                "predefined": predefined_serializer.data,
                "custom": custom_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def put(self, request, event_slug):
        """PUT: Replace the list of custom checklist items for the event"""
        user = request.user
        event, error_response = self._get_user_event(user, event_slug)
        if error_response:
            return error_response

        if not isinstance(request.data, list):
            return Response(
                {"error": _("Expected a list of checklist items.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EventChecklistItemSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        items = serializer.validated_data

        # Current custom checklist items linked to this event
        current_custom_items = EventChecklistItem.objects.filter(
            event=event, custom=True
        )
        current_ids = set(current_custom_items.values_list("id", flat=True))

        keep_ids = set()

        for item in items:
            item_id = item.get("id")
            name = item.get("name")
            checked = item.get("checked", False)

            if item_id:
                try:
                    checklist_item = EventChecklistItem.objects.get(
                        id=item_id, event=event, custom=True
                    )
                except EventChecklistItem.DoesNotExist:
                    return Response(
                        {
                            "error": _("Checklist item not found."),
                            "id": item_id,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                # Create new custom checklist item
                checklist_item = EventChecklistItem.objects.create(
                    event=event,
                    name=name,
                    checked=checked,
                    custom=True,
                )

            # Update fields
            checklist_item.name = name
            checklist_item.checked = checked
            checklist_item.save()

            keep_ids.add(checklist_item.id)

        # Remove custom items that are no longer in the list
        remove_ids = current_ids - keep_ids
        if remove_ids:
            EventChecklistItem.objects.filter(
                event=event, id__in=remove_ids, custom=True
            ).delete()

        return Response(
            { "message": _("Checklist items updated successfully.")},
            status=status.HTTP_200_OK,
        )


class EventChecklistItemView(EventAccessMixin, generics.GenericAPIView):
    """
    Update the checked status of a checklist item by ID.

    PATCH: Update the checked status of a checklist item (works for both predefined and custom items).
    """

    permission_classes = [IsAuthenticated]

    def _get_checklist_item(self, user, event_slug, item_id):
        """Helper method to get checklist item if user organizes the event"""
        event, error_response = self._get_user_event(user, event_slug)
        if error_response:
            return None, None, error_response

        try:
            item = EventChecklistItem.objects.get(id=item_id, event=event)
            return event, item, None
        except EventChecklistItem.DoesNotExist:
            return (
                None,
                None,
                Response(
                    {"error": _("Checklist item not found.")},
                    status=status.HTTP_404_NOT_FOUND,
                ),
            )

    def patch(self, request, event_slug, item_id):
        """PATCH: Toggle the checked status of a checklist item"""
        user = request.user
        event, item, error_response = self._get_checklist_item(
            user, event_slug, item_id
        )
        if error_response:
            return error_response

        # Get the checked value from request, default to toggling if not provided
        checked = request.data.get("checked")
        if checked is None:
            # If not provided, toggle the current value
            checked = not item.checked

        # Update the checked status
        item.checked = checked
        item.save()

        serializer = EventChecklistItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_200_OK)

