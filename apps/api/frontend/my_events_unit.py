import datetime

from api import views
from interactions.models import Interaction, InteractionType
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions, serializers, viewsets


class TypeDoesNotExist(serializers.ValidationError):
    status_code = 405
    default_detail = {"type__slug": "Interaction type does not exist"}


class EventInteractionSerializer(serializers.ModelSerializer):
    type__slug = serializers.CharField(source="type.slug")

    def validate(self, data):
        validated_data = super().validate(data)

        validated_data["user"] = self.context["request"].user
        try:
            validated_data["type"] = InteractionType.objects.get(
                slug=data["type"]["slug"]
            )
        except InteractionType.DoesNotExist:
            raise TypeDoesNotExist

        validated_data["administrative_unit"] = validated_data[
            "event"
        ].event_type.administrative_unit
        validated_data["date_from"] = validated_data["event"].start_date
        if validated_data["date_from"] is None:
            validated_data["date_from"] = datetime.date.today()
        return validated_data

    class Meta:
        model = Interaction
        fields = (
            "id",
            "event",
            "note",
            "updated",
            "created",
            "type__slug",
            "note",
        )


class MyEventsSet(viewsets.ModelViewSet):
    serializer_class = EventInteractionSerializer

    def get_queryset(self):
        return Interaction.objects.filter(user=self.request.user)

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
