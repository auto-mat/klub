# -*- coding: utf-8 -*-

import uuid
from enum import Enum

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.html import mark_safe
from django.utils.translation import ugettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField

from .validators import validate_logo_image


class SocialMedia(Enum):
    facebook = 'facebook'
    google = 'google'
    instagram = 'instagram'
    twitter = 'twitter'
    vimeo = 'vimeo'
    youtube = 'youtube'


class TemplateContent(models.Model):

    class Meta:
        verbose_name = _("Template content")
        verbose_name_plural = _("Template contents")

    created = models.DateTimeField(
        verbose_name=_("Created"),
        auto_now_add=True,
    )
    modified = models.DateTimeField(
        verbose_name=_("Modified"),
        auto_now=True,
    )
    uuid = models.UUIDField(
        verbose_name=_("Universally unique identifier"),
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    images = models.CharField(
        verbose_name=_("Images"),
        max_length=100,
        blank=True,
        null=True,
    )
    page = models.CharField(
        verbose_name=_("Pages"),
        max_length=100,
        blank=True,
        null=True,
    )
    regions = models.TextField(
        verbose_name=_("Regions"),
        blank=True,
        default='',
        null=True,
    )
    styles = JSONField(
        verbose_name=_("Styles"),
        blank=True,
        null=True,
    )


class Images(models.Model):

    class Meta:
        verbose_name = _("Images")
        verbose_name_plural = _("Images")

    created = models.DateTimeField(
        verbose_name=_("Created"),
        auto_now_add=True,
    )
    modified = models.DateTimeField(
        verbose_name=_("Modified"),
        auto_now=True,
    )
    image = models.ImageField(
        verbose_name=_("Image"),
        upload_to='images',
        height_field=None,
        width_field=None,
        max_length=100,
        null=True,
    )
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=100,
        blank=True,
        null=True,
    )
    edited_width = models.IntegerField(
        verbose_name=_("Edited width"),
        blank=True,
        null=True,
    )
    edited_crop = models.CharField(
        verbose_name=_("Edited crop"),
        max_length=80,
        blank=True,
        null=True,
    )
    edited_direction = models.CharField(
        verbose_name=_("Edited direction"),
        max_length=5,
        blank=True,
        null=True,
    )
    background_image = models.BooleanField(
        verbose_name=_("Background image"),
        default=False,
    )
    template_url = models.CharField(
        verbose_name=_("Template url"),
        max_length=350,
        blank=True,
        null=True,
    )

    def size(self):
        return [self.image.width, self.image.height]


# class FileUpload(models.Model):
#     created = models.DateTimeField(
#         auto_now_add=True,
#     )
#     owner = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#     )
#     datafile = models.FileField(
#         upload_to='files',
#     )


class CompanyUrl(models.Model):

    class Meta:
        verbose_name = _("Company url")
        verbose_name_plural = _("Company urls")

    url = models.URLField(
        verbose_name=_("Url"),
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.url or ''


class CompanyPhone(models.Model):

    class Meta:
        verbose_name = _("Company phone number")
        verbose_name_plural = _("Company phone numbers")

    phone = PhoneNumberField(
        verbose_name=_("Phone number"),
        null=True,
        blank=True,
    )

    def __str__(self):
        return str(self.phone)


class CompanyEmail(models.Model):

    class Meta:
        verbose_name = _("Company email")
        verbose_name_plural = _("Company emails")

    email = models.EmailField(
        verbose_name=_("Company email"),
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.email or ''


class CompanySocialMedia(models.Model):

    class Meta:
        verbose_name = _("Company social media")
        verbose_name_plural = _("Company social media")

    icon_name = models.CharField(
        verbose_name=_("Icon name"),
        choices=((tag.name, tag.value) for tag in SocialMedia),
        max_length=20,
        null=True,
        blank=True,
    )
    url = models.URLField(
        verbose_name=_("Url"),
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.icon_name} : {self.url}"


class TemplateFooter(models.Model):

    class Meta:
        verbose_name = _("Template footer")
        verbose_name_plural = _("Template footers")

    name = models.CharField(
        verbose_name=_("Footer name"),
        max_length=255,
        null=True,
        blank=True,
    )
    company_name = models.CharField(
        verbose_name=_("Company name"),
        max_length=80,
        null=True,
        blank=True,
    )
    address = models.CharField(
        verbose_name=_("Address"),
        max_length=80,
        null=True,
        blank=True,
    )
    phone = models.ManyToManyField(
        verbose_name=_("Phone"),
        to=CompanyPhone,
        blank=True,
    )
    email = models.ManyToManyField(
        verbose_name=_("Email"),
        to=CompanyEmail,
        blank=True,
    )
    url = models.ManyToManyField(
        verbose_name=_("Url"),
        to=CompanyUrl,
        blank=True,
    )
    social_media = models.ManyToManyField(
        verbose_name=_("Social media"),
        to=CompanySocialMedia,
        blank=True,
    )
    user = models.ForeignKey(
        verbose_name=_("User"),
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    show = models.BooleanField(
        verbose_name=_("Show"),
        default=False,
        help_text=_("Show footer"),
    )

    def __str__(self):
        return self.company_name

    def get_url(self):
        return mark_safe("<br>".join([o.url for o in self.url.all()]))
    get_url.short_description = _('Url')

    def get_email(self):
        return mark_safe("<br>".join([o.email for o in self.email.all()]))
    get_email.short_description = _('Email')

    def get_phone(self):
        return mark_safe("<br>".join([str(o.phone) for o in self.phone.all()]))
    get_phone.short_description = _('Phone number')

    def get_social_media(self):
        objs = self.social_media.all()
        return mark_safe("<br>".join([f"{o.icon_name}: {o.url}" for o in objs]))
    get_social_media.short_description = _('Social media link')


class TemplateHeader(models.Model):

    class Meta:
        verbose_name = _("Template header")
        verbose_name_plural = _("Template headers")

    name = models.CharField(
        verbose_name=_("Header name"),
        max_length=255,
        null=True,
        blank=True,
    )
    text = models.CharField(
        verbose_name=_("Header text"),
        max_length=255,
        null=True,
        blank=True,
    )
    text_horizontal_position = models.CharField(
        verbose_name=_("Header horizontal text position"),
        choices=(("left", _("Left")),
                 ("center", _("Center")),
                 ("right", _("Right"))),
        default="left",
        max_length=20,
        null=True,
        blank=True,
    )
    text_vertical_position = models.CharField(
        verbose_name=_("Header vertical text position"),
        choices=(("top", _("Top")),
                 ("middle", _("Middle")),
                 ("bottom", _("Bottom"))),
        default="middle",
        max_length=20,
        null=True,
        blank=True,
    )
    logo = models.ImageField(
        verbose_name=_("Logo image"),
        upload_to='images',
        height_field=None,
        width_field=None,
        max_length=100,
        validators=[validate_logo_image],
        help_text=_("Max. image width 300 px, and max. image file size 5 MB"),
    )
    logo_horizontal_position = models.CharField(
        verbose_name=_("Logo horizontal position"),
        choices=(
            ("left", _("Left")),
            ("center", _("Center")),
            ("right", _("Right"))),
        default="left",
        max_length=20,
        null=True,
        blank=True,
    )
    logo_position = models.CharField(
        verbose_name=_("Logo position"),
        choices=(
            ("left", _("Left")),
            ("right", _("Right"))),
        default="left",
        max_length=20,
        null=True,
        blank=True,
        help_text=_("Left or right column logo position"),
    )
    user = models.ForeignKey(
        verbose_name=_("User"),
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    show = models.BooleanField(
        verbose_name=_("Show"),
        default=False,
        help_text=_("Show header"),
    )

    def __str__(self):
        return self.name or ''
