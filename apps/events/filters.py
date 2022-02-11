from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from rangefilter.filter import DateRangeFilter


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
