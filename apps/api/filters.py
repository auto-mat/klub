from django_filters import rest_framework as filters

from events.models import Event


class EventCustomFilter(filters.FilterSet):
    administrative_unit = filters.CharFilter(method='get_administrative_unit')

    class Meta:
        model = Event
        fields = ["slug"]

    def get_administrative_unit(self, queryset, name, value, *args, **kwargs):
        if name == 'administrative_unit':
            queryset = queryset.filter(administrative_units__slug=value)
        return queryset
