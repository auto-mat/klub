from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='get_link_element')
def get_link_element(value, arg):
    if arg == 'list':
        links = []
        for i in value:
            links.append(
                mark_safe(f"<a href=\"{i}\" target=\"_blank\">{i}</a>"),
            )
        return links
    elif arg == 'str':
        return mark_safe(
            f"<a href=\"{value}\" target=\"_blank\">{value}</a>")
