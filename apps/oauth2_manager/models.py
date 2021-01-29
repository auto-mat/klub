from django.db import models


class ApplicationScopeSelector(models.Model):
    default_scopes = models.TextField(
        verbose_name=("scope"),
        help_text=("Additing scopes to current app"),
        blank=True,
    )
    application = models.OneToOneField(
        'oauth2_provider.Application',
        on_delete=models.CASCADE,
        blank=True,
    )

    def __str__(self):
        return f"default_scopes id: {self.id}"
