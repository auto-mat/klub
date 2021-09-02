from django.contrib import admin

from oauth2_provider.admin import ApplicationAdmin
from oauth2_provider.models import Application

from .models import ApplicationScopeSelector


class ApplicationScopeSelectorInline(admin.TabularInline):
    model = ApplicationScopeSelector
    can_delete = False
    extra = 1

    def has_changed(self):
        """Must return True if we want to save unchanged inlines
        or raise validation errors"""
        return True


admin.site.unregister(Application)


@admin.register(Application)
class ApplicationAdminWithScopesAdmin(ApplicationAdmin):
    """
    add scopes class to admin
    """

    inlines = [ApplicationScopeSelectorInline]
