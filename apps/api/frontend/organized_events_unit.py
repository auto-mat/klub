from api import serializers, views
from events.models import Event
from rest_framework import mixins, viewsets, permissions


class OrganizedEventsSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Get and update events that the current user is organizing.
    """

    serializer_class = serializers.EventSerializer

    def get_queryset(self):
        return Event.objects.filter(organization_team__in=[self.request.user])

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = views.ResultsSetPagination


def test_event_set_anon(anon_api_request):
    from rest_framework.reverse import reverse

    url = reverse("frontend_organized_events-list")
    result = anon_api_request.get(url)
    assert result.json() == {"detail": "Nebyly zadány přihlašovací údaje."}


def test_event_set_non_organizer(superuser1_api_request, event_1, event_2):
    from rest_framework.reverse import reverse

    url = reverse("frontend_organized_events-list")
    result = superuser1_api_request.get(url)
    assert result.json() == {"count": 0, "next": None, "previous": None, "results": []}


def test_event_set_organizer(user1_api_request, organization_team_2, event_2):
    from rest_framework.reverse import reverse

    url = reverse("frontend_organized_events-list")
    result = user1_api_request.get(url)
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
                "administrative_units": [event_2.administrative_units.first().pk],
                "administrative_unit_name": "Auto*mat - slovakia",
                "administrative_unit_web_url": None,
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
                "event_type": None,
                "event_type_id": None,
                "id": event_2.pk,
                "intended_for": "everyone",
                "invitation_text_1": "",
                "invitation_text_2": "",
                "invitation_text_3": "",
                "invitation_text_4": "",
                "invitation_text_short": "",
                "location": None,
                "looking_forward_to_you": "",
                "main_photo": None,
                "name": "event_name_2",
                "opportunity": "",
                "participation_fee": "",
                "program": "",
                "public_on_web": True,
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

    event2_url = "{}{}/".format(url, event_2.pk)
    result = user1_api_request.get(event2_url)
    assert result.json() == {
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
        "administrative_units": [event_2.administrative_units.first().pk],
        "administrative_unit_name": "Auto*mat - slovakia",
        "administrative_unit_web_url": None,
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
        "event_type": None,
        "event_type_id": None,
        "id": event_2.pk,
        "intended_for": "everyone",
        "invitation_text_1": "",
        "invitation_text_2": "",
        "invitation_text_3": "",
        "invitation_text_4": "",
        "invitation_text_short": "",
        "location": None,
        "looking_forward_to_you": "",
        "main_photo": None,
        "name": "event_name_2",
        "opportunity": "",
        "participation_fee": "",
        "program": "",
        "public_on_web": True,
        "public_on_web_date_from": None,
        "public_on_web_date_to": None,
        "registration_method": "standard",
        "responsible_person": "",
        "start_date": None,
        "web_url": None,
        "working_hours": None,
    }

    result = user1_api_request.patch(
        event2_url,
        {
            "web_url": "https://example.com",
        },
    )

    patched_event_data = {
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
        "administrative_units": [event_2.administrative_units.first().pk],
        "administrative_unit_name": "Auto*mat - slovakia",
        "administrative_unit_web_url": None,
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
        "event_type": None,
        "event_type_id": None,
        "id": event_2.pk,
        "intended_for": "everyone",
        "invitation_text_1": "",
        "invitation_text_2": "",
        "invitation_text_3": "",
        "invitation_text_4": "",
        "invitation_text_short": "",
        "location": None,
        "looking_forward_to_you": "",
        "main_photo": None,
        "name": "event_name_2",
        "opportunity": "",
        "participation_fee": "",
        "program": "",
        "public_on_web": True,
        "public_on_web_date_from": None,
        "public_on_web_date_to": None,
        "registration_method": "standard",
        "responsible_person": "",
        "start_date": None,
        "web_url": "https://example.com",
        "working_hours": None,
    }

    assert result.json() == patched_event_data
    result = user1_api_request.get(event2_url)
    assert result.json() == patched_event_data

    result = user1_api_request.post(
        url,
        {
            "name": "event_name_3",
            "web_url": "https://example.com",
        },
    )
    assert result.status_code == 405
