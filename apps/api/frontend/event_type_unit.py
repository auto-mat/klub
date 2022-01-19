from events.models import EventType
from rest_framework import viewsets, serializers, permissions


class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType
        ref_name = "full_event_type_serializer"
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "administrative_unit",
        )


class EventTypeSet(viewsets.ModelViewSet):
    serializer_class = EventTypeSerializer

    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return EventType.objects.all()


def test_event_type_set(superuser1_api_request):
    from rest_framework.reverse import reverse

    url = reverse("frontend_event-type-list")
    result = superuser1_api_request.get(url)
    assert result.json() == []


def test_event_type_set1(superuser1_api_request, event_type_1, administrative_unit_1):
    from rest_framework.reverse import reverse

    url = reverse("frontend_event-type-list")
    result = superuser1_api_request.get(url)
    assert result.json() == [
        {
            "name": "Event name",
            "id": event_type_1.pk,
            "administrative_unit": administrative_unit_1.pk,
            "description": "some description",
            "slug": "event_name",
        }
    ]


def test_event_type_set_anon(anon_api_request):
    from rest_framework.reverse import reverse

    url = reverse("frontend_event-type-list")
    result = anon_api_request.get(url)
    assert result.json() == {"detail": "Nebyly zadány přihlašovací údaje."}
