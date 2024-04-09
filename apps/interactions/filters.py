from django.contrib import admin
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from aklub.filters import InputFilter as InputFilterBase


class InputFilter(InputFilterBase):
    list_item_separator = ","


class EventInteractionNameFilter(InputFilter):
    parameter_name = "event-of-interaction-name"
    title = _("Event of interaction")
    placeholder = _("event name, event name, ...")

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            return queryset.filter(event__name__in=self._get_input_values(value=value))


class EventInteractionId(InputFilter):
    parameter_name = "event-of-interaction-id"
    title = _("Event of interaction ID")
    placeholder = _("event id, event id, ...")

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            return queryset.filter(event__id__in=self._get_input_values(value=value))
