from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig
from django.utils.translation import ugettext_lazy as _

# raname/translate app name in admin
# dont forget to set path in __init__ file in specific app


class MyAdminConfig(AdminConfig):
    default_site = "project.admin.MyAdminSite"


class AklubConfig(AppConfig):
    name = "aklub"
    verbose_name = _("Basic menu")


class InteractionConfig(AppConfig):
    name = "interactions"
    verbose_name = _("Interactions")


class EventConfig(AppConfig):
    name = "events"
    verbose_name = _("Events")


class PdfStorageConfig(AppConfig):
    name = "pdf_storage"
    verbose_name = _("File Storage")


class ImportExportCeleryEdit(AppConfig):
    name = "import_export_celery_edit"

    def ready(self):
        import import_export_celery_edit.signals  # noqa
