import datetime

from api import views
from interactions.models import Interaction, InteractionType
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions, serializers, viewsets

from api.frontend.event_interaction_serializer_unit import (
    EventTypeDoesNotExist,
    EventInteractionSerializer,
)


class EventInteractionsSet(viewsets.ModelViewSet):
    serializer_class = EventInteractionSerializer

    def get_queryset(self):
        event = self.request.query_params.get("event", None)
        q = Interaction.objects.all()
        if event is not None:
            q = q.filter(event__pk=event)
        return q

    permission_classes = [permissions.IsAdminUser]
    pagination_class = views.ResultsSetPagination


def test_normal_user(user1_api_request, event_1, interaction_type_1):
    from rest_framework.reverse import reverse

    url = reverse("frontend_my_events-list")
    result = user1_api_request.get(url)
    assert result.json() == {"count": 0, "next": None, "previous": None, "results": []}

    result = user1_api_request.post(
        url,
        {
            "event": event_1.pk,
            "note": "blah blah",
            "type__slug": "non-existant",
        },
    )
    assert result.json() == {"type__slug": ["Interaction type does not exist"]}
    result = user1_api_request.get(url)
    assert result.json() == {"count": 0, "next": None, "previous": None, "results": []}
    cresult = user1_api_request.post(
        url,
        {
            "event": event_1.pk,
            "note": "blah blah",
            "type__slug": interaction_type_1.slug,
        },
    )
    assert cresult.json() == {
        "created": cresult.json()["created"],
        "event": event_1.pk,
        "id": cresult.json()["id"],
        "note": "blah blah",
        "type__slug": "interaction-type-slug",
        "updated": cresult.json()["updated"],
    }
    result = user1_api_request.get(url)
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
                "type__slug": "interaction-type-slug",
                "updated": cresult.json()["updated"],
            }
        ],
    }
