from django.contrib import admin
from django.utils.translation import ugettext as _

from notifications.admin import NotificationAdmin
from notifications.models import Notification

admin.site.unregister(Notification)


def mark_as_read_action(modeladmin, request, queryset):
    queryset.mark_all_as_read()


mark_as_read_action.short_description = _("Mark selected as read")


@admin.register(Notification)
class _NotificationAdmin(NotificationAdmin):
    """
    Use this list only as some list of Notifications
    """

    list_display = (
        "timestamp",
        "verb",
        "description",
        "level",
        "unread",
    )
    fields = list_display
    readonly_fields = list_display
    list_filter = ("unread", "level")
    actions = (mark_as_read_action,)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(recipient=request.user)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False
