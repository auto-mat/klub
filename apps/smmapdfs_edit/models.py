from aklub.models import AdministrativeUnit

from django.db import models

from smmapdfs.models import PdfSandwichEmail, PdfSandwichFont, PdfSandwichType


class PdfSandwichTypeConnector(models.Model):
    pdfsandwichtype = models.OneToOneField(
                     PdfSandwichType,
                     on_delete=models.CASCADE,
    )

    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )


class PdfSandwichEmailConnector(models.Model):
    pdfsandwichemail = models.OneToOneField(
                     PdfSandwichEmail,
                     on_delete=models.CASCADE,
    )

    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )


class PdfSandwichFontConnector(models.Model):
    pdfsandwichfont = models.OneToOneField(
                     PdfSandwichFont,
                     on_delete=models.CASCADE,
    )

    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
