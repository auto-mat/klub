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
