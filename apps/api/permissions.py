from rest_framework import serializers, permissions


def check_orgteam_membership(user, event):
    if not user.is_superuser:
        if not event or not event.organization_team.filter(id=user.pk).exists():
            raise MustBeAMemberOfOrgTeam


class MustBeAMemberOfOrgTeam(serializers.ValidationError):
    status_code = 403
    default_detail = {"event": "Must be a member of org team"}


class IsEventOrganizer(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    def has_permission(self, request, view):
        return request.user.has_perm("events.add_event")
