# -*- coding: utf-8 -*-

from django.forms.widgets import Widget
from django.template import loader
from django.utils.safestring import mark_safe


class HtmlTemplateWidget(Widget):
    template_name = "form_field_html_template_widget.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None, **kwargs):
        context = super().get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)

        return mark_safe(template)
