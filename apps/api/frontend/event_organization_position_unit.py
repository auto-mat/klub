from events.models import OrganizationPosition
from rest_framework import viewsets, serializers


class OrganizationPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationPosition
        fields = (
            "id",
            "name",
            "description",
        )


class OrganizationPositionSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrganizationPositionSerializer

    def get_queryset(self):
        return OrganizationPosition.objects.all()


def test_event_type_set_anon(anon_api_request, organization_position_1):
    from rest_framework.reverse import reverse

    url = reverse("frontend_event-organization-position-list")
    result = anon_api_request.get(url)
    assert result.status_code == 200
    assert result.json() == [
        {'description': '', 'id': organization_position_1.pk, 'name': 'position'}
    ]
