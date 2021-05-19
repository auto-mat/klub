from django_filters import rest_framework as filters

from events.models import Event


class EventCustomFilter(filters.FilterSet):
    administrative_unit = filters.CharFilter(method='get_administrative_unit')
    event_type_array = filters.CharFilter(method='get_event_type_array')
    program_array = filters.CharFilter(method='get_program_array')
    indended_for_array = filters.CharFilter(method='get_indended_for_array')
    type = filters.CharFilter(method='get_type') # noqa

    class Meta:
        model = Event
        fields = {
            'date_from': ['gte', 'lte', 'year'],
            'date_to': ['gte', 'lte', 'year'],
            'start_date': ['gte', 'lte', 'year'],
            'indended_for': ['exact'],
            'program': ['exact'],
            'is_internal': ['exact'],
        }

    def get_type(self, queryset, name, value, *args, **kwargs):
        # some crazy custom filters
        if name == 'type':
            if value == "klub":
                queryset = queryset.filter(is_internal=True)
            elif value == "vik":
                queryset = queryset.exclude(is_internal=True, event_type__slug="tabor")
            elif value == "tabor":
                queryset = queryset.filter(event_type__slug="tabor")
            elif value == "viktabor":
                queryset = queryset.exclude(is_internal=True)
            elif value == "ekostan":
                queryset = queryset.filter(program="eco_consulting")
            elif value == "vikekostan":
                queryset = queryset\
                    .filter(program="eco_consulting")\
                    .exclude(is_internal=True, event_type__slug="tabor")
        return queryset

    def get_administrative_unit(self, queryset, name, value, *args, **kwargs):
        if name == 'administrative_unit':
            queryset = queryset.filter(administrative_units__id=value)
        return queryset

    def get_event_type_array(self, queryset, name, value, *args, **kwargs):
        if name == 'event_type_array':
            event_type_list = value.split(",")  # slugs
            queryset = queryset.filter(event_type__slug__in=event_type_list)
        return queryset

    def get_program_array(self, queryset, name, value, *args, **kwargs):
        if name == 'program_array':
            program_list = value.split(",")  # slugs
            queryset = queryset.filter(program__in=program_list)
        return queryset

    def get_indended_for_array(self, queryset, name, value, *args, **kwargs):
        if name == 'indended_for_array':
            indended_for_list = value.split(",")  # slugs
            queryset = queryset.filter(indended_for__in=indended_for_list)
        return queryset
