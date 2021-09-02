from django.contrib import admin

from .models import PdfStorage


@admin.register(PdfStorage)
class AuthorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "topic",
        "author",
        "related_ids",
        "created",
        "administrative_unit",
    )
