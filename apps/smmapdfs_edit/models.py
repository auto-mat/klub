from aklub.models import AdministrativeUnit

from django.db import models
from django.utils.translation import ugettext_lazy as _

from smmapdfs.models import PdfSandwichEmail, PdfSandwichType


class PdfSandwichTypeConnector(models.Model):
    PROFILE_TYPE = [
        ("company_profile", _("Company profile")),
        ("user_profile", _("User profile")),
    ]
    pdfsandwichtype = models.OneToOneField(
        PdfSandwichType,
        on_delete=models.CASCADE,
    )
    profile_type = models.CharField(
        max_length=50,
        choices=PROFILE_TYPE,
        default="user_profile",
    )
    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        on_delete=models.CASCADE,
    )


class PdfSandwichEmailConnector(models.Model):
    pdfsandwichemail = models.OneToOneField(
        PdfSandwichEmail,
        on_delete=models.CASCADE,
    )

    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        on_delete=models.CASCADE,
    )
