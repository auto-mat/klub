from django.db.models.signals import post_save
from django.dispatch import receiver

from import_export_celery.models import ExportJob

from import_export_celery_edit.models import ExportConnector


@receiver([post_save], sender=ExportJob)
def add_administrative_unit(sender, instance, **kwargs):
    """
    a little hack
    - the job is saved right after export action, then redirect to change page is done.
    - The administrative unit is not saved and because of that, user do not see the change page
    - This post save takes action of it and add connector with administrative unit if not set!
    """
    if not hasattr(instance, 'exportconnector'):
        au = instance.author.administrative_units.first()
        if au:
            ExportConnector.objects.create(
                administrative_unit=au,
                exportjob=instance,
            )
