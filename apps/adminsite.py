from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

# raname/translate app name in admin
# dont forget to set path in __init__ file in specific app


class AklubConfig(AppConfig):
    name = 'aklub'
    verbose_name = _("Basic menu")


class InteractionConfig(AppConfig):
    name = 'interactions'
    verbose_name = _("Interactions")


class PdfStorageConfig(AppConfig):
    name = 'pdf_storage'
    verbose_name = _("File Storage")
