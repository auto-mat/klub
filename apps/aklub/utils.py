# -*- coding: utf-8 -*-

import datetime
import json
import os
import pathlib
from operator import itemgetter

from django.contrib import messages
from django.db import models
from django.template import loader
from django.urls import reverse
from django.utils.html import format_html_join, mark_safe
from django.utils.translation import ugettext_lazy as _

from html_template_editor.models import (
    Images, TemplateContent, TemplateFooter,
)

from . import models as aklub_models


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


def get_email_templates_names():
    """ Get email templates names """

    templates_blacklist = [
        'base.html',
        'new_empty_template.html',
        'footer.html',
        'automat_fonts.html',
    ]

    def get_templates_files():
        path = pathlib.Path(__file__).parents[0] / 'templates' / 'email_templates'
        return os.listdir(path)

    # File template
    file_templates_names = [
        (template, template) for template in [
            template.split('.')[0] for template in get_templates_files()
            if template not in templates_blacklist
        ]
    ]
    # Db templates
    db_templates_obj = TemplateContent.objects.filter(page__contains='new_empty_template')
    db_templates = set(db_templates_obj.values_list('page', flat=True))

    value = 'new_empty_template:{}'
    db_templates_names = [
        (value.format(pathlib.Path(t).name), pathlib.Path(t).name) for t in db_templates
    ]
    file_templates_names.extend(db_templates_names)

    sorted_templates = sorted(file_templates_names, key=itemgetter(1))
    sorted_templates.insert(0, ('new_empty_template', 'new_empty_template'))
    sorted_templates.insert(0, ('', '---------'))

    return sorted_templates


def get_email_template_context(template_path, template_url):
    """ Get email template context """

    template = loader.get_template(str(template_path))
    template_obj = TemplateContent.objects.filter(page=template_url)
    if (template_obj):
        content = template_obj.latest('created')
        context = {
            'page': content,
        }
        regions = json.loads(content.regions)
        context.update(regions)
    else:
        context = {}

    footer = TemplateFooter.objects.filter(show=True).first()
    if footer:
        context['footer'] = footer

    background_image = Images.objects.filter(
            template_url=template_url,
            edited_crop__isnull=False,
        ).order_by('-modified').first()
    if background_image:
        context['bg_img'] = background_image.image.url
        context['bg_img_width'] = background_image.image.width
        context['bg_img_height'] = background_image.image.height

    return template, context
