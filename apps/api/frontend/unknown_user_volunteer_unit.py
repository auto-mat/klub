from rest_framework import generics

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from django.conf import settings

from aklub.models import UserProfile, AdministrativeUnit

from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope
from rest_framework import serializers
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from events.models import Event, Location
from interactions.models import Interaction

from interactions.interaction_types import *
from ..serializers import GetOrCreateUserprofile, get_or_create_user_profile_fields


class MultiSelectField(serializers.MultipleChoiceField):
    def to_representation(self, value):
        return list(super().to_representation(value))


class VolunteerSerializer(
    GetOrCreateUserprofile,
):
    administrative_unit = serializers.SlugRelatedField(
        required=True,
        queryset=AdministrativeUnit.objects.filter(),
        slug_field="id",
    )
    skills = serializers.CharField(required=False, allow_blank=True)
    summary = serializers.CharField(required=False, allow_blank=True)
    location = serializers.SlugRelatedField(
        required=False,
        queryset=Location.objects.filter(),
        slug_field="id",
    )
    event = serializers.SlugRelatedField(
        required=False,
        queryset=Event.objects.filter(),
        slug_field="id",
    )
    program_of_interest = MultiSelectField(
        required=False,
        choices=settings.ORGANIZATION_FINANCE_PROGRAM_TYPES,
    )

    class Meta:
        model = UserProfile
        fields = get_or_create_user_profile_fields + [
            "administrative_unit",
            "skills",
            "event",
            "summary",
            "location",
            "program_of_interest",
        ]


class VolunteerView(generics.CreateAPIView):
    permission_classes = [TokenHasReadWriteScope | IsAdminUser]
    required_scopes = ["can_create_userprofile_interaction"]

    def post(self, request, *args, **kwargs):
        serializer = VolunteerSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        user, created = serializer.get_or_create_user_profile()

        event = serializer.validated_data.get("event")
        administrative_unit = serializer.validated_data.get("administrative_unit")
        user.administrative_units.add(administrative_unit),

        interaction_type = volunteer_interaction_type()
        Interaction.objects.create(
            user=user,
            type=interaction_type,
            administrative_unit=administrative_unit,
            date_from=timezone.now(),
            subject=interaction_type.name,
            summary=serializer.validated_data.get("summary", ""),
            program_of_interest=serializer.validated_data.get("program_of_interest"),
        )

        return Response(
            VolunteerSerializer(serializer.validated_data).data,
            status=status.HTTP_200_OK,
        )


def test_volunteer(event_1, location_1, administrative_unit_1, app_request):
    from rest_framework.reverse import reverse
    from freezegun import freeze_time

    url = reverse("unknown_user_volunteer")

    post_data = {
        "first_name": "John",
        "last_name": "Dock",
        "telephone": "720000000",
        "email": "john@rock.com",
        "note": "iam alergic to bees",
        "age_group": 2012,
        "birth_month": 12,
        "birth_day": 12,
        "street": "Belmont Avenue 2414",
        "city": "New York",
        "zip_code": "10458",
        "administrative_unit": administrative_unit_1.pk,
        "skills": "cooking",
    }
    current_date = timezone.now()
    with freeze_time(current_date):
        response = app_request.post(url, post_data)
    assert response.status_code == 200
    # we do not really care about data response

    new_user = UserProfile.objects.get(profileemail__email=post_data["email"])
    assert new_user.first_name == post_data["first_name"]
    assert new_user.last_name == post_data["last_name"]
    assert new_user.age_group == post_data["age_group"]
    assert new_user.birth_month == post_data["birth_month"]
    assert new_user.birth_day == post_data["birth_day"]
    assert new_user.street == post_data["street"]
    assert new_user.city == post_data["city"]
    assert new_user.zip_code == post_data["zip_code"]
    assert new_user.administrative_units.first() == administrative_unit_1

    assert new_user.interaction_set.count() == 1
    interaction = new_user.interaction_set.first()
    assert interaction.administrative_unit == administrative_unit_1
    assert interaction.subject == "Nabídka o pomoci"
    assert interaction.date_from == current_date

    # second registration => user recognized and only new interaction is created!
    post_data["event"] = event_1.pk

    response = app_request.post(url, post_data)
    assert response.status_code == 200
    assert new_user.interaction_set.count() == 2

    # second registration => user recognized and only new interaction is created!
    del post_data["event"]
    post_data["program_of_interest"] = ["zmj", "lab"]

    response = app_request.post(url, post_data)
    assert response.status_code == 200
    assert new_user.interaction_set.count() == 3

    interaction = new_user.interaction_set.last()
    interaction.program_of_interest = ["zmj", "lab"]

    # second registration => user recognized and only new interaction is created!
    del post_data["program_of_interest"]
    post_data["location"] = location_1.pk

    response = app_request.post(url, post_data)
    assert response.status_code == 200
    assert new_user.interaction_set.count() == 4
