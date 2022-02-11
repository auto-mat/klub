from rest_framework import generics

from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope
from rest_framework.permissions import IsAdminUser

from interactions.interaction_types import *
from ..serializers import CreateUserProfileInteractionSerializer


class CreateUserProfileView(generics.CreateApiView):



class UserProfileInteractionView(generics.CreateAPIView):
    permission_classes = [TokenHasReadWriteScope | IsAdminUser]
    required_scopes = ["can_create_userprofile_interaction"]

    def post(self, request, *args, **kwargs):
        serializer = self.CreateUserProfileInteractionSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        user, created = serializer.get_or_create_user_profile()


        # Get user category (participant, volunteer or member) from slug
        interaction_category = get_interaction_category(kwargs.get("user_category"))

        event = serializer.validated_data.get("event")
        user.administrative_units.add(event.administrative_units.first()),
        telephone = serializer.validated_data.get("telephone")
        if telephone:
            Telephone.objects.get_or_create(
                telephone=telephone, user=user, defaults={"is_primary": True}
            )
        email = serializer.validated_data.get("email")
        if email:
            ProfileEmail.objects.get_or_create(
                email=email, user=user, defaults={"is_primary": True}
            )

        # prepare not from fields:
        add_answer_1 = (
            f"{event.additional_question_1}:\n    {serializer.validated_data.get('additional_question_1', '-')}\n"
            if event.additional_question_1
            else "-"
        )
        add_answer_2 = (
            f"{event.additional_question_2}:\n    {serializer.validated_data.get('additional_question_2', '-')}\n"
            if event.additional_question_2
            else "-"
        )
        add_answer_3 = (
            f"{event.additional_question_3}:\n    {serializer.validated_data.get('additional_question_3', '-')}\n"
            if event.additional_question_3
            else "-"
        )
        add_answer_4 = (
            f"{event.additional_question_4}:\n    {serializer.validated_data.get('additional_question_4', '-')}\n"
            if event.additional_question_4
            else "-"
        )
        summary = f"{serializer.validated_data['note']}\n{add_answer_1}{add_answer_2}{add_answer_3}{add_answer_4}"

        interaction_type, created = InteractionType.objects.get_or_create(
            category=category,
            defaults={
                "name": _(interaction_type),
                "created_bool": True,
                "event_bool": True,
                "note_bool": True,
                "summary_bool": True,
            },
        )

        Interaction.objects.create(
            user=user,
            type=interaction_type,
            summary=_("note:") + "\n    " + summary,
            event=event,
            administrative_unit=event.administrative_units.first(),
            date_from=timezone.now(),
            subject=_(interaction_type.name),
        )

        return Response(
            self.serializer_class(serializer.validated_data).data,
            status=status.HTTP_200_OK,
        )


def test_create_userprofile_interaction(event_1, app_request):
    from rest_framework.reverse import reverse

    url = reverse("userprofile_interaction", "event_attendance")

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
    assert (
        new_user.administrative_units.first()
        == event_1.administrative_units.all().first()
    )

    assert new_user.interaction_set.count() == 1
    interaction = new_user.interaction_set.first()
    assert interaction.event == event_1
    assert interaction.administrative_unit == event_1.administrative_units.first()
    assert interaction.subject == _("Registration to event")
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
