from api import serializers as our_serializers, views
from events.models import Event, OrganizationPosition, OrganizationTeam
from rest_framework import viewsets, permissions, mixins, serializers


class MustBeAnEventOrganizer(serializers.ValidationError):
    status_code = 403
    default_detail = {"error": "must be an event organizer"}


class EventSerializer(our_serializers.EventSerializer):
    def create(self, validated_data):
        event = super().create(validated_data)
        op, _ = OrganizationPosition.objects.get_or_create(name="Event creator")
        OrganizationTeam.objects.create(
            position=op,
            profile=self.context["request"].user,
            event=event,
        )

        return event

    class Meta:
        model = Event
        ref_name = "fronend_event_serializer"
        fields = [
            "id",
            "name",
            "date_from",
            "date_to",
            "program",
            "intended_for",
            "basic_purpose",
            "opportunity",
            "location",
            "age_from",
            "age_to",
            "start_date",
            "event_type",
            "event_type_id",
            "responsible_person",
            "participation_fee",
            "entry_form_url",
            "web_url",
            "invitation_text_short",
            "working_hours",
            "accommodation",
            "diet",
            "looking_forward_to_you",
            "registration_method",
            "administrative_units",
            "administrative_unit_name",
            "administrative_unit_web_url",
            "invitation_text_1",
            "invitation_text_2",
            "invitation_text_3",
            "invitation_text_4",
            "main_photo",
            "additional_photo_1",
            "additional_photo_2",
            "additional_photo_3",
            "additional_photo_4",
            "additional_photo_5",
            "additional_photo_6",
            "additional_question_1",
            "additional_question_2",
            "additional_question_3",
            "additional_question_4",
            "contact_person_name",
            "contact_person_email",
            "contact_person_telephone",
            "public_on_web_date_from",
            "public_on_web_date_to",
            "public_on_web",
        ]


class EventSet(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = EventSerializer

    def get_queryset(self):
        return Event.objects.all()

    def create(self, request):
        if not (request.user.is_superuser or request.user.has_perm("events.add_event")):
            raise MustBeAnEventOrganizer
        return super().create(request)

    pagination_class = views.ResultsSetPagination


def test_event_type_set_event_organizer(
    event_organizer_api_request, event_type_1, administrative_unit_1, event_organizer_1
):

    from rest_framework.reverse import reverse

    url = reverse("frontend_events-list")

    result = event_organizer_api_request.post(
        url,
        {
            "name": "Test event",
            "event_type_id": event_type_1.pk,
            "administrative_units": [administrative_unit_1.pk],
        },
    )
    assert result.status_code == 201

    event = Event.objects.get(name="Test event")
    assert event.organization_team.filter(id=event_organizer_1.pk).exists()

    result = event_organizer_api_request.get(url)
    assert result.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "accommodation": "",
                "additional_photo_1": None,
                "additional_photo_2": None,
                "additional_photo_3": None,
                "additional_photo_4": None,
                "additional_photo_5": None,
                "additional_photo_6": None,
                "additional_question_1": "",
                "additional_question_2": "",
                "additional_question_3": "",
                "additional_question_4": "",
                "administrative_unit_name": "Auto*mat",
                "administrative_unit_web_url": "www.smth.eu",
                "administrative_units": [administrative_unit_1.pk],
                "age_from": None,
                "age_to": None,
                "basic_purpose": "action",
                "contact_person_email": "",
                "contact_person_name": "",
                "contact_person_telephone": "",
                "date_from": None,
                "date_to": None,
                "diet": [],
                "entry_form_url": None,
                "event_type": {"name": "Event name", "slug": "event_name"},
                "event_type_id": event_type_1.pk,
                "id": event.pk,
                "intended_for": "everyone",
                "invitation_text_1": "",
                "invitation_text_2": "",
                "invitation_text_3": "",
                "invitation_text_4": "",
                "invitation_text_short": "",
                "location": None,
                "looking_forward_to_you": "",
                "main_photo": None,
                "name": "Test event",
                "opportunity": "",
                "participation_fee": "",
                "program": "",
                "public_on_web": False,
                "public_on_web_date_from": None,
                "public_on_web_date_to": None,
                "registration_method": "standard",
                "responsible_person": "",
                "start_date": None,
                "web_url": None,
                "working_hours": None,
            }
        ],
    }


def test_event_set_anon(anon_api_request):
    from rest_framework.reverse import reverse

    url = reverse("frontend_events-list")

    result = anon_api_request.post(url, {})
    assert result.status_code == 403

    result = anon_api_request.get(url)
    assert result.json() == {"count": 0, "next": None, "previous": None, "results": []}
