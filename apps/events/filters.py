from django.contrib import messages
from django.contrib import admin
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from rangefilter.filter import DateRangeFilter

from aklub.filters import InputFilter as InputFilterBase
from .models import OrganizationTeam


class EventYieldDateRangeFilter(DateRangeFilter):
    """
    filter which doesnt filter queryset but filters total income per date period in admin_list
    """

    title = _("Filter by Yield period")

    def queryset(self, request, queryset):
        # always return full queryset
        return queryset


class MultiSelectFilter(admin.ChoicesFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)
        self.lookup_kwarg = "%s__icontains" % field_path
        self.lookup_val = params.get(self.lookup_kwarg)


class InputFilter(InputFilterBase):
    placeholder = _("event name, event name, ...")
    list_item_separator = ","

class EventParentFilter(InputFilter):
    parameter_name = "tn_parent"
    title = _("Parent name")
    placeholder = _("event name, ...")

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            return queryset.filter(
                tn_parent__name__in=[
                    name.strip() for name in value.split(self.list_item_separator)
                ]
            )


class EventChildrenFilter(EventParentFilter):
    parameter_name = "tn_children"
    title = _("Children name")

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            return queryset.filter(
                tn_children__name__in=[
                    name.strip() for name in value.split(self.list_item_separator)
                ]
            )


class EventAncestorsFilter(EventParentFilter):
    parameter_name = "tn_ancestors_pks"
    title = _("Ancestor name")

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            ids = queryset.filter(
                name__in=[
                    name.strip() for name in value.split(self.list_item_separator)
                ]
            ).values_list("pk", flat=True)
            return queryset.filter(tn_ancestors_pks__in=list(ids))


class EventDescendantsFilter(EventParentFilter):
    parameter_name = "tn_descendants_pks"
    title = _("Descendant name")

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            ids = queryset.filter(
                name__in=[
                    name.strip() for name in value.split(self.list_item_separator)
                ]
            ).values_list("pk", flat=True)
            return queryset.filter(tn_descendants_pks__in=list(ids))


class EventInteractionFilter(EventParentFilter):
    parameter_name = "interaction__type__name"
    title = _("Interaction name")
    placeholder = _("interaction name, ...")

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            return queryset.filter(
                interaction__type__name__in=[
                    name.strip() for name in value.split(self.list_item_separator)
                ]
            )


class EventInteractionWithStatusFilter(EventParentFilter):
    parameter_name = "interaction_name_with_status"
    title = _("Interaction name with status")
    placeholder = _("inter. name|inter. status, ...")
    incorrect_filter_input_value_err_message = _(
        "Incorrect '%(filter)s' filter input value."
        " Correct format is 'interaction name|interaction status'"
        " or 'interaction name|intercation status, ...'."
    )

    def _make_query(self, values, separator="|"):
        """Make combined query

        :param list values: list of values ["interaction name|interaction status",...]
        :param str separator: list item string interaction name and
                              interaction status separator with default |
                              separator
        :retrun query
        """
        value = values.pop(0)
        interaction_name, interaction_status = value.split(separator)
        query = Q(
            interaction__type__name=interaction_name,
            interaction__status=interaction_status,
        )
        for value in values:
            interaction_name, interaction_status = value.split(separator)
            query |= Q(
                interaction__type__name=interaction_name,
                interaction__status=interaction_status,
            )
        return query

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            try:
                names = [name.strip() for name in value.split(self.list_item_separator)]
                return queryset.filter(self._make_query(values=names))
            except ValueError:
                messages.error(
                    request,
                    self.incorrect_filter_input_value_err_message
                    % {"filter": self.title},
                )


class EventUserInteractionFilter(EventParentFilter):
    parameter_name = "user_interaction_name"
    title = _("User interaction name")
    placeholder = _("user interaction name, ...")

    def _make_query(self, values):
        """Make combined query

        :param list values: list of values ["user interaction name,...]
        :retrun query
        """
        value = values.pop(0)
        query = Q(profile__interaction__type__name=value)
        for value in values:
            query |= Q(profile__interaction__type__name=value)
        return query

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            names = [name.strip() for name in value.split(self.list_item_separator)]
            query = self._make_query(values=names)
            events_ids = (
                OrganizationTeam.objects.select_related("event")
                .filter(query)
                .values_list("event__id", flat=True)
            )
            return queryset.filter(id__in=list(events_ids))
