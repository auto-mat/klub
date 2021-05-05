# -*- coding: utf-8 -*-
import datetime
import operator
from functools import reduce

from django.contrib import messages
from django.contrib.admin.utils import lookup_needs_distinct
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.urls import reverse
from django.utils.html import format_html_join, mark_safe
from django.utils.translation import ugettext_lazy as _

from . import models as aklub_models

def annotation_friendly_search_results(self, request, queryset, search_term): # noqa
    """
    - fully copied from django.... used nested select insteed of classic one
    - should be used if search is made by FK for example: userprofile__telephone...
    - why? because if not, django joins search tables and annotation result is multiplicated :(
    - see below
    """
    # Apply keyword searches.
    def construct_search(field_name):
        if field_name.startswith('^'):
            return "%s__istartswith" % field_name[1:]
        elif field_name.startswith('='):
            return "%s__iexact" % field_name[1:]
        elif field_name.startswith('@'):
            return "%s__search" % field_name[1:]
        # Use field_name if it includes a lookup.
        opts = queryset.model._meta
        lookup_fields = field_name.split(LOOKUP_SEP)
        # Go through the fields, following all relations.
        prev_field = None
        for path_part in lookup_fields:
            if path_part == 'pk':
                path_part = opts.pk.name
            try:
                field = opts.get_field(path_part)
            except FieldDoesNotExist:
                # Use valid query lookups.
                if prev_field and prev_field.get_lookup(path_part):
                    return field_name
            else:
                prev_field = field
                if hasattr(field, 'get_path_info'):
                    # Update opts to follow the relation.
                    opts = field.get_path_info()[-1].to_opts
        # Otherwise, use the field with icontains.
        return "%s__icontains" % field_name

    use_distinct = False
    search_fields = self.get_search_fields(request)
    if search_fields and search_term:
        orm_lookups = [
            construct_search(str(search_field))
            for search_field in search_fields]
        for bit in search_term.split():
            or_queries = [
                models.Q(**{orm_lookup: bit})
                for orm_lookup in orm_lookups]
            # THIS IS CHANGED!!!!
            # queryset = queryset.filter(reduce(operator.or_, or_queries))
            filtered_ids = self.model.objects.filter(reduce(operator.or_, or_queries)).values_list("id", flat=True)
            queryset = queryset.filter(id__in=filtered_ids)
            # ^^^^^^^
        use_distinct |= any(lookup_needs_distinct(self.opts, search_spec) for search_spec in orm_lookups)

    return queryset, use_distinct


def sweet_text(generator):
    """
    breakto diff lines
    accepts generator:
    example:
    (str(pay.ammount),) for pay in payments))
    return :
    1000,
    2000,
    3000
    """
    return format_html_join(mark_safe(',<br/>'), "<nobr>{}</nobr>", generator)


def create_model(
        name, fields=None, app_label='',
        module='', options=None, parent_class=(models.Model,),):
    """ Create specified model """
    class Meta:
        pass

    if app_label:
        setattr(Meta, 'app_label', app_label)

    if options is not None:
        for key, value in options.items():
            setattr(Meta, key, value)

    attrs = {'__module__': module, 'Meta': Meta}

    if fields:
        attrs.update(fields)

    model = type(name, parent_class, attrs)

    return model


def edit_donor_annotate_filter(self, request):
    """
    additional info for annotate filters
    """
    donor_filter = {}
    if request.GET.get('userchannels__event__id__in'):
        self.filtered_events = request.GET['userchannels__event__id__in'].split(',')
        donor_filter['userchannels__event_id__in'] = self.filtered_events
    else:
        self.filtered_events = []
    return donor_filter


def check_annotate_filters(list_display, request, filter_kwargs):
    """
    Create additional annotate to queryset if specific list order is active
    """
    if request.GET.get('o'):
        # check ordering fields (-1 cuz of list indexing)
        order_filter_fields = [list_display[int(index)-1] for index in request.GET.get('o').replace('-', "").split('.')]
        if 'donor_delay' in order_filter_fields:
            filter_kwargs = {'order_payment_delay': models.Value(None, models.DurationField())}
            if not request.GET.get('userchannels__event__id__in'):
                messages.warning(request, _('Please select event before sort by donor delay'))
            else:
                event_id = request.GET['userchannels__event__id__in'].split(',')[0]
                donor_channels = aklub_models.DonorPaymentChannel.objects.filter(
                    event_id=event_id,
                    user=models.OuterRef('id'),
                ).annotate(
                    duration_sort=models.Case( # noqa
                        models.When(
                            ~models.Q(expected_regular_payment_date=None),
                            then=models.F("expected_regular_payment_date") - datetime.date.today(),
                        ),
                        default=None,
                        output_field=models.DurationField(),
                    )
                )
                filter_kwargs.update({'order_payment_delay': models.Subquery(donor_channels.values('duration_sort'))})
                return filter_kwargs
    return filter_kwargs


def check_annotate_subqueries(self, request):
    """
    working around bug
    allow make aggregation from multiple tables
    https://code.djangoproject.com/ticket/10060?fbclid=IwAR3bRzdagRmDsNtyMPIwsRTPVDr-4VkHZlkdAtHDKXFEN00ufJnY1TBSGqc
    this cant be done like : next_communication_date=Max('interaction__next_communication_date'), in queryset
    """
    from interactions.models import Interaction
    if request.user.has_perm('aklub.can_edit_all_units'):
        unit_filter = {}
    else:
        unit_filter = {'administrative_unit__in': self.user_administrated_units}

    next_com = Interaction.objects\
        .filter(user=models.OuterRef('pk'), **unit_filter)\
        .order_by("-next_communication_date")
    annotate_kwargs = {
        'next_communication_date': models.Subquery(next_com.values('next_communication_date')[:1], output_field=models.DateTimeField()),
    }
    return annotate_kwargs


class WithAdminUrl:
    def get_admin_url(self):
        return reverse(
            'admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name),
            args=[self.id],
        )
