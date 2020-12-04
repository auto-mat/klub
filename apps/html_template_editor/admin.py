from django import forms
from django.contrib import admin


from .models import (
    CompanyEmail, CompanyPhone, CompanySocialMedia,
    CompanyUrl, TemplateFooter, TemplateHeader,
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


class TemplateFooterAdminForm(forms.ModelForm):
    class Meta:
        model = TemplateFooter
        exclude = (
            'url',
            'phone',
            'email',
            'social_media',
            'user',
        )

    def save(self, commit=True):
        instance = super(TemplateFooterAdminForm, self).save(commit=False)
        instance.user = self.user
        if commit:
            instance.save()
        return instance


@admin.register(TemplateFooter)
class TemplateFooterAdminInline(admin.ModelAdmin):
    form = TemplateFooterAdminForm
    list_display = (
        'company_name',
        'address',
        'get_phone',
        'get_email',
        'get_url',
        'get_social_media',
        'user',
        'show',
    )
    list_filter = (
        'name',
        'company_name',
        'user',
        'show',
    )
    inlines = [
        CompanyPhoneAdminInline,
        CompanyUrlAdminInline,
        CompanyEmailAdminInline,
        CompanySocialMediaAdminInline,
    ]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.user = request.user
        return form


class TemplateHeaderAdminForm(forms.ModelForm):
    class Meta:
        model = TemplateHeader
        exclude = ('user',)

    def save(self, commit=True):
        instance = super(TemplateHeaderAdminForm, self).save(commit=False)
        instance.user = self.user
        if commit:
            instance.save()
        return instance


@admin.register(TemplateHeader)
class TemplateHeaderAdminInline(admin.ModelAdmin):
    form = TemplateHeaderAdminForm
    list_display = (
        'name',
        'text',
        'logo',
        'user',
        'show',
    )
    list_filter = (
        'name',
        'text',
        'user',
        'show',
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.user = request.user
        return form
