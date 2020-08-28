from aklub.models import AdministrativeUnit, Profile

from django.contrib.postgres.fields import ArrayField
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _


class PdfStorage(models.Model):
    name = models.CharField(
        verbose_name=_("Name of Pdf"),
        max_length=200,
    )
    topic = models.CharField(
        verbose_name=_("Topic of Pdf"),
        max_length=200,
    )
    author = models.ForeignKey(
        Profile,
        verbose_name=_("Author of Pdf"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    created = models.DateTimeField(
        verbose_name=_("Date of creation"),
        auto_now_add=True,
        null=True,
    )
    related_ids = ArrayField(
        models.IntegerField(),
    )
    pdf_file = models.FileField(
        upload_to='pdf_storage',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
    )
    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        verbose_name=_("administrative unit"),
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name
