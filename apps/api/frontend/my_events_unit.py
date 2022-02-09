import datetime

from api import views
from interactions.models import Interaction, InteractionType
from interactions.interaction_types import (
    event_interaction_category,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions, serializers, viewsets

from api.frontend.event_interaction_serializer_unit import (
    UserOwnedEventInteractionSerializer,
)


class MyEventsSet(viewsets.ModelViewSet):
    serializer_class = UserOwnedEventInteractionSerializer

    def get_queryset(self):
        return Interaction.objects.filter(
            user=self.request.user,
            type__category=event_interaction_category(),
        )

    permission_classes = [permissions.IsAuthenticated]
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
    assert cresult.status_code == 400
    assert cresult.json() == {"type__slug": ["Not an event interaction type"]}
    result = user1_api_request.get(url)
    assert result.json() == {"count": 0, "next": None, "previous": None, "results": []}
    from interactions.interaction_types import (
        event_registration_interaction_type,
    )

    erit = event_registration_interaction_type()
    cresult = user1_api_request.post(
        url,
        {
            "event": event_1.pk,
            "note": "blah blah",
            "type__slug": erit.slug,
        },
    )
    assert cresult.json()["event"] == event_1.pk
    assert cresult.json()["note"] == "blah blah"
    assert cresult.json()["type__slug"] == erit.slug
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
                "type__slug": "event_registration",
                "updated": cresult.json()["updated"],
            }
        ],
    }
