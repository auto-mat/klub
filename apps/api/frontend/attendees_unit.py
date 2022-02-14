import datetime

from api import views
from interactions.models import Interaction, InteractionType
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions, serializers, viewsets

from api.frontend.event_interaction_serializer_unit import (
    EventInteractionSerializer,
)


class EventInteractionSet(viewsets.ModelViewSet):
    serializer_class = EventInteractionSerializer

    def get_queryset(self):
        event = self.request.query_params.get("event", None)
        q = Interaction.objects.filter(
            type__category__slug="event_interaction",
        )
        if event is not None:
            q = q.filter(event__pk=event)
        return q

    permission_classes = [permissions.IsAdminUser]
    pagination_class = views.ResultsSetPagination


def test_normal_user(superuser1_api_request, event_1, userprofile_1):
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
