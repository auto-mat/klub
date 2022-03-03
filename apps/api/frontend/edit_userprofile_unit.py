import datetime

from django.db.models import Q
from aklub.models import UserProfile, Telephone
from rest_framework import viewsets, serializers, permissions, mixins

from api.permissions import IsEventOrganizer


class MustSpecifyDateOfBirth(serializers.ValidationError):
    status_code = 403
    default_detail = {
        "error": "must specify date of birth in query arg `dob` in the form YYYY-MM-DD"
    }


class TelephoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Telephone
        fields = (
            "telephone",
            "note",
            "is_primary",
        )


class UserSerializer(serializers.ModelSerializer):
    telephone_set = TelephoneSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        ref_name = "edit_user_profile_serializer"
        fields = (
            "id",
            "first_name",
            "last_name",
            "nickname",
            "email",
            "telephone_set",
            "city",
            "note",
            "age_group",
            "birth_month",
            "birth_day",
            "street",
            "zip_code",
        )


class UserSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UserSerializer

    permission_classes = [permissions.IsAdminUser | IsEventOrganizer]

    def get_queryset(self):
        user_dob = self.request.query_params.get("dob", None)
        if user_dob is None:
            raise MustSpecifyDateOfBirth

        try:
            dob = datetime.date.fromisoformat(user_dob)
        except ValueError:
            raise MustSpecifyDateOfBirth

        return UserProfile.objects.filter(
            age_group=dob.year,
            birth_month=dob.month,
            birth_day=dob.day,
        )


def test_org_team_organizer(
    event_organizer_api_request,
    userprofile_2,
):
    from rest_framework.reverse import reverse

    url = (
        "/api/frontend/edit_userprofile/%d/?dob=1993-03-29" % userprofile_2.pk
    )  # Wrong birthday
    result = event_organizer_api_request.get(url)
    assert result.status_code == 404

    url = (
        "/api/frontend/edit_userprofile/%d/?dob=1993--29" % userprofile_2.pk
    )  # bad bday format
    result = event_organizer_api_request.get(url)
    assert result.status_code == 403

    url = "/api/frontend/edit_userprofile/%d/" % userprofile_2.pk  # No bday
    result = event_organizer_api_request.get(url)
    assert result.status_code == 403

    url = "/api/frontend/edit_userprofile/"  # Listing does nothing
    result = event_organizer_api_request.get(url)
    assert result.status_code == 404

    url = "/api/frontend/edit_userprofile/%d/?dob=2003-03-29" % userprofile_2.pk
    result = event_organizer_api_request.get(url)
    assert result.status_code == 200
    assert result.json() == {
        "id": userprofile_2.pk,
        "first_name": "user2_first",
        "last_name": "user2_last",
        "nickname": "user2_nickname",
        "email": None,
        "telephone_set": [],
        "city": "Prague",
        "note": "",
        "age_group": 2003,
        "birth_month": 3,
        "birth_day": 29,
        "street": "",
        "zip_code": "",
    }

    result = event_organizer_api_request.patch(url, {"first_name": "Fooo"})
    assert result.status_code == 200

    result = event_organizer_api_request.get(url)
    assert result.status_code == 200
    assert result.json() == {
        "id": userprofile_2.pk,
        "first_name": "Fooo",
        "last_name": "user2_last",
        "nickname": "user2_nickname",
        "email": None,
        "telephone_set": [],
        "city": "Prague",
        "note": "",
        "age_group": 2003,
        "birth_month": 3,
        "birth_day": 29,
        "street": "",
        "zip_code": "",
    }
