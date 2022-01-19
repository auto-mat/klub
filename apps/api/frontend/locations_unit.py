from api.serializers import LocationSerializer
from events.models import Location
from rest_framework import viewsets, serializers, permissions


class LocationSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer

    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Location.objects.all()


def test_location_set(superuser1_api_request):
    from rest_framework.reverse import reverse

    url = reverse("frontend_locations-list")
    result = superuser1_api_request.get(url)
    assert result.json() == []


def test_location_set1(superuser1_api_request, location_1):
    from rest_framework.reverse import reverse

    url = reverse("frontend_locations-list")
    result = superuser1_api_request.get(url)
    assert result.json() == [
        {
            "name": "location_name",
            "place": "here",
            "region": "Prague",
            "gps_latitude": 52.15151,
            "gps_longitude": 35.11515,
            "id": location_1.pk,
        }
    ]


def test_location_set_anon(anon_api_request):
    from rest_framework.reverse import reverse

    url = reverse("frontend_locations-list")
    result = anon_api_request.get(url)
    assert result.json() == {"detail": "Nebyly zadány přihlašovací údaje."}
