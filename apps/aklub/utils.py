# -*- coding: utf-8 -*-

import os
import pathlib

from django.db import models
from django.urls import reverse
from django.utils.html import format_html_join, mark_safe


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


class WithAdminUrl:
    def get_admin_url(self):
        return reverse(
            'admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name),
            args=[self.id],
        )


def get_email_templates_names():
    """ Get email templates names """
    templates_names = [
        (template, template) for template in [
            template.split('.')[0] for template in os.listdir(
                pathlib.PurePath(__file__).parents[0] / 'templates' / 'email_templates')
            if template not in ['base.html']
        ]
    ]

    return templates_names
