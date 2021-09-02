from django.contrib import admin

from .models import Repo


class RepoAdmin(admin.ModelAdmin):
    list_display = ("name", "account", "provider")


admin.site.register(Repo, RepoAdmin)
