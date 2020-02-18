
from django.contrib import admin

from .models import (
    CompanyEmail, CompanyPhone, CompanySocialMedia,
    CompanyUrl, TemplateFooter,
)

# Register your models here.


@admin.register(CompanyPhone)
class CompanyPhoneAdmin(admin.ModelAdmin):
    pass


@admin.register(CompanyUrl)
class CompanyUrlAdmin(admin.ModelAdmin):
    pass


@admin.register(CompanyEmail)
class CompanyEmailAdmin(admin.ModelAdmin):
    pass


@admin.register(CompanySocialMedia)
class CompanySocialMediaAdmin(admin.ModelAdmin):
    pass


class CompanyPhoneAdminInline(admin.StackedInline):
    model = TemplateFooter.phone.through
    extra = 0


class CompanyUrlAdminInline(admin.StackedInline):
    model = TemplateFooter.url.through
    extra = 0


class CompanyEmailAdminInline(admin.StackedInline):
    model = TemplateFooter.email.through
    extra = 0


class CompanySocialMediaAdminInline(admin.StackedInline):
    model = TemplateFooter.social_media.through
    extra = 0


@admin.register(TemplateFooter)
class TemplateFooterAdminInline(admin.ModelAdmin):
    list_display = (
        'company_name',
        'address',
        'get_phone',
        'get_email',
        'get_url',
        'get_social_media',
        'show',
    )
    exclude = (
        'url',
        'phone',
        'email',
        'social_media',
    )
    inlines = [
        CompanyPhoneAdminInline,
        CompanyUrlAdminInline,
        CompanyEmailAdminInline,
        CompanySocialMediaAdminInline,
    ]
