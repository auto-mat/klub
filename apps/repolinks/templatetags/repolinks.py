from django import template

from ..models import Repo

register = template.Library()


class ReposNode(template.Node):
    def render(self, context):
        context["repos"] = Repo.objects.all()
        return ""


@register.tag
def load_repos(parser, token):
    return ReposNode()
