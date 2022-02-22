from django.db.models import Q
from aklub.models import UserProfile, Telephone
from rest_framework import viewsets, serializers, permissions

from api.permissions import IsEventOrganizer


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
        fields = (
            "id",
            "first_name",
            "last_name",
            "nickname",
            "email",
            "telephone_set",
            "city",
        )


class UserSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer

    permission_classes = [permissions.IsAdminUser | IsEventOrganizer]

    def get_queryset(self):
        search = self.request.query_params.get("q", None)
        q = UserProfile.objects.all()
        if search is not None:
            q = q.filter(
                Q(first_name__icontains=search)
                | (
                    Q(first_name__in=search.split(" "))
                    & Q(last_name__in=search.split(" "))
                )
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(nickname__icontains=search)
                | Q(maiden_name__icontains=search)
            )
        return q


def test_user_set(
    superuser1_api_request, userprofile_superuser_1, userprofile_superuser_2
):
    from rest_framework.reverse import reverse

    url = reverse("frontend_users-list")
    result = superuser1_api_request.get(url)
    assert result.json() == [
        {
            "email": None,
            "first_name": "admin_2",
            "id": userprofile_superuser_2.pk,
            "last_name": "admin_2",
            "nickname": "",
            "telephone_set": [],
            "city": "",
        },
        {
            "email": None,
            "first_name": "admin_first",
            "id": userprofile_superuser_1.pk,
            "last_name": "admin_last",
            "nickname": "admin_nickname",
            "telephone_set": [],
            "city": "",
        },
    ]

    result = superuser1_api_request.get(url + "?q=admin_first")
    assert result.json() == [
        {
            "email": None,
            "first_name": "admin_first",
            "id": userprofile_superuser_1.pk,
            "last_name": "admin_last",
            "nickname": "admin_nickname",
            "telephone_set": [],
            "city": "",
        },
    ]
    result = superuser1_api_request.get(url + "?q=admin_first admin_last")
    assert result.json() == [
        {
            "email": None,
            "first_name": "admin_first",
            "id": userprofile_superuser_1.pk,
            "last_name": "admin_last",
            "nickname": "admin_nickname",
            "telephone_set": [],
            "city": "",
        },
    ]


def test_user_set1(
    superuser1_api_request,
    userprofile_superuser_1,
    userprofile_superuser_2,
    userprofile_1,
    profileemail_2,
    telephone_2,
):
    from rest_framework.reverse import reverse

    url = reverse("frontend_users-list")
    result = superuser1_api_request.get(url)
    assert sorted(result.json(), key=lambda v: v["id"]) == sorted(
        [
            {
                "email": "ho@ha.com",
                "first_name": "admin_2",
                "id": userprofile_superuser_2.pk,
                "last_name": "admin_2",
                "nickname": "",
                "telephone_set": [
                    {"telephone": "655455564", "is_primary": True, "note": ""}
                ],
                "city": "",
            },
            {
                "email": None,
                "first_name": "admin_first",
                "id": userprofile_superuser_1.pk,
                "last_name": "admin_last",
                "nickname": "admin_nickname",
                "telephone_set": [],
                "city": "",
            },
            {
                "email": None,
                "first_name": "user_first",
                "id": userprofile_1.pk,
                "last_name": "user_last",
                "nickname": "user_nickname",
                "telephone_set": [],
                "city": "Prague",
            },
        ],
        key=lambda v: v["id"],
    )
    result = superuser1_api_request.get(url + "?q=admin_first user_last")
    assert result.json() == []
    result = superuser1_api_request.get(url + "?q=ho@ha.com")
    assert result.json() == [
        {
            "email": "ho@ha.com",
            "first_name": "admin_2",
            "id": userprofile_superuser_2.pk,
            "last_name": "admin_2",
            "nickname": "",
            "city": "",
            "telephone_set": [
                {"telephone": "655455564", "is_primary": True, "note": ""}
            ],
        }
    ]


def test_search_users_set_normal_user(user1_api_request):
    from rest_framework.reverse import reverse

    url = reverse("frontend_users-list")
    result = user1_api_request.get(url)
    assert result.json() == {"detail": "K této akci nemáte oprávnění."}


def test_search_users_set_anon(anon_api_request):
    from rest_framework.reverse import reverse

    url = reverse("frontend_users-list")
    result = anon_api_request.get(url)
    assert result.json() == {"detail": "Nebyly zadány přihlašovací údaje."}
