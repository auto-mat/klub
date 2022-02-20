import datetime

from api import views, permissions as our_permissions

from events.models import Event

from interactions.models import Interaction, InteractionType
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import mixins, permissions, serializers, viewsets

from api.frontend.event_interaction_serializer_unit import (
    EventInteractionSerializer,
)


class EventInteractionSet(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = EventInteractionSerializer

    def get_queryset(self):
        event = self.request.query_params.get("event", None)
        if event:
            event = Event.objects.get(pk=event)
        our_permissions.check_orgteam_membership(self.request.user, event)

        q = Interaction.objects.filter(
            type__category__slug="event_interaction",
        )
        if event is not None:
            q = q.filter(event=event)
        return q

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = views.ResultsSetPagination


def test_super_user(superuser1_api_request, event_1, userprofile_1):
    from rest_framework.reverse import reverse
    from interactions.interaction_types import (
        event_registration_interaction_type,
        event_attendance_interaction_type,
    )

    erit = event_registration_interaction_type()

    url = reverse("frontend_attendees-list")
    result = superuser1_api_request.get(url)
    assert result.json() == {"count": 0, "next": None, "previous": None, "results": []}

    result = superuser1_api_request.post(
        url,
        {
            "user": userprofile_1.pk,
            "event": event_1.pk,
            "note": "blah blah",
            "type__slug": "non-existant",
        },
    )
    assert result.json() == {"type__slug": ["Interaction type does not exist"]}
    result = superuser1_api_request.get(url)
    assert result.json() == {"count": 0, "next": None, "previous": None, "results": []}
    cresult = superuser1_api_request.post(
        url,
        {
            "user": userprofile_1.pk,
            "event": event_1.pk,
            "note": "blah blah",
            "type__slug": erit.slug,
        },
    )
    assert cresult.json()["event"] == event_1.pk
    assert cresult.json()["note"] == "blah blah"
    assert cresult.json()["type__slug"] == erit.slug
    result = superuser1_api_request.get(url)
    assert result.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "created": cresult.json()["created"],
                "event": event_1.pk,
                "id": cresult.json()["id"],
                "note": "blah blah",
                "type__slug": erit.slug,
                "updated": cresult.json()["updated"],
                "summary": "",
                "user": userprofile_1.pk,
            }
        ],
    }


def test_attendees_set_organizer(
    user1_api_request, organization_team_2, event_1, event_2
):
    from rest_framework.reverse import reverse

    url = reverse("frontend_attendees-list")
    result = user1_api_request.get(url)
    assert result.status_code == 403

    result = user1_api_request.get(url + "?event=%d" % event_1.pk)
    assert result.status_code == 403

    result = user1_api_request.get(url + "?event=%d" % event_2.pk)
    assert result.status_code == 200
