from aklub.models import UserProfile
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def who_am_i(request):
    up = request.user
    if request.method == "POST":
        up.first_name = request.data.get("first_name", up.first_name)
        up.last_name = request.data.get("last_name", up.last_name)
        up.nickname = request.data.get("nickname", up.nickname)
        up.save()
    return Response(
        {
            "first_name": up.first_name,
            "last_name": up.last_name,
            "nickname": up.nickname,
            "is_staff": up.is_staff,
            "is_superuser": up.is_superuser,
            "is_event_organizer": up.has_perm("events.add_event"),
            "id": up.pk,
        }
    )


def test_whoami_admin(superuser1_api_request, userprofile_superuser_1):
    from rest_framework.reverse import reverse

    url = reverse("frontend_whoami")
    result = superuser1_api_request.get(url)
    assert result.json() == {
        "first_name": "admin_first",
        "last_name": "admin_last",
        "nickname": "admin_nickname",
        "is_staff": True,
        "is_superuser": True,
        "is_event_organizer": True,
        "id": userprofile_superuser_1.pk,
    }
    result = superuser1_api_request.post(
        url,
        {
            "first_name": "admin_first_1",
            "last_name": "admin_last_1",
            "nickname": "admin_nickname_1",
            "is_staff": False,  # We're actually testing here that these don't change and you can't do this...
            "is_superuser": False,
        },
    )
    result = superuser1_api_request.get(url)
    assert result.json() == {
        "first_name": "admin_first_1",
        "last_name": "admin_last_1",
        "nickname": "admin_nickname_1",
        "is_staff": True,
        "is_superuser": True,
        "is_event_organizer": True,
        "id": userprofile_superuser_1.pk,
    }
    # Test partial update as well
    result = superuser1_api_request.post(
        url,
        {
            "first_name": "admin_first_2",
        },
    )
    result = superuser1_api_request.get(url)
    assert result.json() == {
        "first_name": "admin_first_2",
        "last_name": "admin_last_1",
        "nickname": "admin_nickname_1",
        "is_staff": True,
        "is_superuser": True,
        "is_event_organizer": True,
        "id": userprofile_superuser_1.pk,
    }


def test_whoami_anon_user(anon_api_request):
    from rest_framework.reverse import reverse

    url = reverse("frontend_whoami")
    result = anon_api_request.get(url)
    assert result.status_code == 403
