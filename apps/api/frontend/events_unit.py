from api import serializers
from events.models import Event
from rest_framework import viewsets, permissions


class EventSet(viewsets.ModelViewSet):
    serializer_class = serializers.EventSerializer

    def get_queryset(self):
        return Event.objects.all()

    permission_classes = [permissions.IsAdminUser]


def test_event_set_anon(anon_api_request):
    from rest_framework.reverse import reverse

    url = reverse("frontend_events-list")
    result = anon_api_request.get(url)
    assert result.json() == {"detail": "Nebyly zadány přihlašovací údaje."}
