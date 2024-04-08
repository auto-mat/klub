from django import forms
from django.template import loader
from django.utils.safestring import mark_safe


class EventChildrensTreeWidget(forms.widgets.Widget):
    """Render event childrens descendants tree"""

    template_name = "widgets/event_childrens_tree_widget.html"

    class Media:
        css = {
            "all": ["css/descendants_tree.css"]
        }

    def __init__(self, *args, **kwargs):
        self._attrs = kwargs.pop("attrs")
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs=None):
        return {
            "widget": {
                "name": name,
                "value": value,
                "attrs": attrs,

            }
        }

    def render(self, name, value, attrs=None, renderer=None):
        if value:
            value = value.get_descendants_tree()
            attrs.update(self._attrs)
            context = self.get_context(name, value, attrs)
            template = loader.get_template(self.template_name).render(context)
            return mark_safe(template)
        return "-"
