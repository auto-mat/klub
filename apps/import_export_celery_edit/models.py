from aklub.models import AdministrativeUnit

from django.db import models

from import_export_celery.models import ExportJob, ImportJob


class ImportConnector(models.Model):
    importjob = models.OneToOneField(
        ImportJob,
        on_delete=models.CASCADE,
    )

    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        on_delete=models.CASCADE,
        null=True,
    )


class ExportConnector(models.Model):
    exportjob = models.OneToOneField(
        ExportJob,
        on_delete=models.CASCADE,
    )

    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        on_delete=models.CASCADE,
        null=True,
    )
