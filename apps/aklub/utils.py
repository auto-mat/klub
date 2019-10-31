# -*- coding: utf-8 -*-

from django.db import models
from django.urls import reverse


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
