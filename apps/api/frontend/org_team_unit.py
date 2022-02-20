import datetime

from api import views, permissions as our_permissions

from events.models import OrganizationTeam, Event, OrganizationPosition
from aklub.models import Profile

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import mixins, permissions, serializers, viewsets


class WithEventMixin:
    def get_event(self):
        try:
            request = self.request
        except:
            request = self.context["request"]
        event = request.query_params.get("event", None)
        if not event:
            raise our_permissions.MustBeAMemberOfOrgTeam

        event = Event.objects.get(pk=event)
        our_permissions.check_orgteam_membership(request.user, event)
        return event


class OrganizationTeamSerializer(WithEventMixin, serializers.ModelSerializer):
    profile_id = serializers.PrimaryKeyRelatedField(
        source="profile", queryset=Profile.objects.all()
    )
    position_id = serializers.PrimaryKeyRelatedField(
        source="position", queryset=OrganizationPosition.objects.all()
    )
    position_name = serializers.CharField(
        source="position.name",
        required=False,
    )

    def create(self, validated_data):
        event = self.get_event()
        return OrganizationTeam.objects.create(
            event = event,
            position = validated_data["position"],
            profile = validated_data["profile"],
        )

    class Meta:
        model = OrganizationTeam
        fields = (
            "id",
            "profile_id",
            "position_id",
            "position_name",
        )


class OrganizationTeamSet(
    WithEventMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = OrganizationTeamSerializer


    def get_queryset(self):
        event = self.get_event()
        return OrganizationTeam.objects.filter(event=event)

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = views.ResultsSetPagination


def test_org_team_organizer(
        user1_api_request, organization_team_2, event_1, event_2, organization_position_1, userprofile_1
):
    from rest_framework.reverse import reverse

    url = reverse("frontend_orgteam-list")
    result = user1_api_request.get(url)
    assert result.status_code == 403

    result = user1_api_request.get(url + "?event=%d" % event_1.pk)
    assert result.status_code == 403

    result = user1_api_request.get(url + "?event=%d" % event_2.pk)
    assert result.status_code == 200

    result = user1_api_request.post(
        url + "?event=%d" % event_2.pk,
        {
            "profile_id": userprofile_1.pk,
            "position_id": organization_position_1.pk,
        }
    )
    assert result.status_code == 201
    id = result.json()["id"]
    assert OrganizationTeam.objects.get(pk=id).position == organization_position_1
