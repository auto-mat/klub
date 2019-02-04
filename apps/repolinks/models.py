from django.db import models
from django.utils.translation import ugettext_lazy as _


class Repo(models.Model):
    name = models.CharField(
        verbose_name=_("Repo name"),
        max_length=256,
    )
    account = models.CharField(
        verbose_name=_("Account"),
        max_length=256,
    )
    provider = models.CharField(
        verbose_name=_("Repo host"),
        choices=[('github', 'github')],
        default="github",
        max_length=64,
    )

    def url(self):
        if self.provider == "github":
            return "https://github.com/%s/%s" % (self.account, self.name)
