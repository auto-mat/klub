from django.contrib.contenttypes.models import ContentType

from rest_framework import permissions, routers, serializers, viewsets

from aklub.models import (
    CompanyProfile,
    CompanyType,
)
from events.models import (
    Event,
)


class EventCompanyProfileListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        data = data.filter(
            polymorphic_ctype=ContentType.objects.get(
                model=CompanyProfile._meta.model_name,
            )
        ).exclude(id=self.context["request"].user.id)
        return super().to_representation(data)


class EventCompanyProfileSerializer(serializers.ModelSerializer):
    company_type = serializers.PrimaryKeyRelatedField(
        queryset=CompanyType.objects.all(),
        required=False,
        allow_null=True,
        source="type",
    )

    class Meta:
        model = CompanyProfile
        list_serializer_class = EventCompanyProfileListSerializer
        fields = [
            "id",
            "name",
            "crn",
            "tin",
            "company_type",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
        }


class EventCompanySerializer(serializers.ModelSerializer):
    organization_team = EventCompanyProfileSerializer(many=True, read_only=False)

    def update(self, instance, validated_data):
        organization_teams = validated_data.pop("organization_team")
        update_org_teams = []
        update_org_teams_fields = []
        for idx, org_team in enumerate(organization_teams):
            org_team_inst = instance.organization_team.get(
                companyprofile__id=self.data["organization_team"][idx]["id"]
            )
            for field in org_team.keys():
                setattr(org_team_inst, field, org_team[field])
                update_org_teams_fields.append(field)
            update_org_teams.append(org_team_inst)
        CompanyProfile.objects.bulk_update(
            update_org_teams,
            list(set(update_org_teams_fields)),
        )
        return instance

    class Meta:
        model = Event
        fields = ("slug", "name", "organization_team")


class EventCompanySet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Event.objects.filter(
            id=self.kwargs["pk"],
            # organization_team=self.request.user,
        ).order_by("id")

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EventCompanySerializer


router = routers.DefaultRouter()
router.register(r"event-company", EventCompanySet, basename="event-company")
