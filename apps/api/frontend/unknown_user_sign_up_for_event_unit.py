from rest_framework import generics

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from aklub.models import UserProfile

from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from events.models import Event
from interactions.models import Interaction

from interactions.interaction_types import *
from ..serializers import GetOrCreateUserprofile, get_or_create_user_profile_fields


class SignUpForEventSerializer(
    GetOrCreateUserprofile,
):
    additional_question_1 = serializers.CharField(required=False, allow_blank=True)
    additional_question_2 = serializers.CharField(required=False, allow_blank=True)
    additional_question_3 = serializers.CharField(required=False, allow_blank=True)
    additional_question_4 = serializers.CharField(required=False, allow_blank=True)
    skills = serializers.CharField(required=False, allow_blank=True)
    event = serializers.SlugRelatedField(
        required=True,
        queryset=Event.objects.filter(slug__isnull=False),
        slug_field="id",
    )

    class Meta:
        model = UserProfile
        fields = get_or_create_user_profile_fields + [
            "event",
            "skills",
            "additional_question_1",
            "additional_question_2",
            "additional_question_3",
            "additional_question_4",
        ]


class SignUpForEventView(generics.CreateAPIView):
    permission_classes = [TokenHasReadWriteScope | IsAuthenticated]
    required_scopes = ["can_create_userprofile_interaction"]
    serializer_class = SignUpForEventSerializer

    def post(self, request, *args, **kwargs):
        serializer = SignUpForEventSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        user, created = serializer.get_or_create_user_profile()

        event = serializer.validated_data.get("event")
        user.administrative_units.add(event.administrative_units.first()),

        summary = f"{serializer.validated_data['note']}\n"

        for n in range(1, 5):
            question = event.__getattribute__("additional_question_%d" % n)
            if question:
                answer = serializer.validated_data.get(
                    "additional_question_%d" % n, "-"
                )
                summary += f"{question}:\n    {answer}\n"

        interaction_type = event_registration_interaction_type()
        Interaction.objects.create(
            user=user,
            type=interaction_type,
            summary=_("note:") + "\n    " + summary,
            event=event,
            administrative_unit=event.administrative_units.first(),
            date_from=timezone.now(),
            subject=interaction_type.name,
        )

        return Response(
            {"user_id": user.pk},
            status=status.HTTP_200_OK,
        )


def test_sign_up_for_event(event_1, app_request):
    from rest_framework.reverse import reverse
    from freezegun import freeze_time

    url = reverse("unknown_user_sign_up_for_event")

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
        "additional_question_1": "answer_1",
        "additional_question_2": "answer_2",
        "additional_question_3": "answer_3",
        "additional_question_4": "answer_4",
        "event": event_1.id,
    }
    current_date = timezone.now()
    with freeze_time(current_date):
        response = app_request.post(url, post_data)
    assert response.status_code == 200

    new_user = UserProfile.objects.get(profileemail__email=post_data["email"])
    assert new_user.pk == response.json()["user_id"]
    assert new_user.first_name == post_data["first_name"]
    assert new_user.last_name == post_data["last_name"]
    assert new_user.age_group == post_data["age_group"]
    assert new_user.birth_month == post_data["birth_month"]
    assert new_user.birth_day == post_data["birth_day"]
    assert new_user.street == post_data["street"]
    assert new_user.city == post_data["city"]
    assert new_user.zip_code == post_data["zip_code"]
    assert (
        new_user.administrative_units.first()
        == event_1.administrative_units.all().first()
    )

    assert new_user.interaction_set.count() == 1
    interaction = new_user.interaction_set.first()
    assert interaction.event == event_1
    assert interaction.administrative_unit == event_1.administrative_units.first()
    assert interaction.subject == "Registrace do akci"
    assert interaction.date_from == current_date
    assert (
        interaction.summary
        == "note:\n    iam alergic to bees\nhe_1?:\n    answer_1\nhe_2?:\n    answer_2\nhe_3?:\n    answer_3\nhe_4?:\n    answer_4\n"
    )

    # second registration => user recognized and only new interaction is created!
    post_data["additional_question_1"] = "new_answer_1"
    post_data["additional_question_2"] = "new_answer_2"
    post_data["additional_question_3"] = "new_answer_3"
    post_data["additional_question_4"] = "new_answer_4"

    response = app_request.post(url, post_data)
    assert response.status_code == 200
    assert new_user.interaction_set.count() == 2
