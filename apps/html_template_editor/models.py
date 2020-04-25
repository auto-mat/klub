# -*- coding: utf-8 -*-

import uuid

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.functional import lazy
from django.utils.html import mark_safe
from django.utils.translation import ugettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField

from .utils import get_social_media_icons_names
from .validators import validate_logo_image


class TemplateContent(models.Model):

    created = models.DateTimeField(
        auto_now_add=True,
    )
    modified = models.DateTimeField(
        auto_now=True,
    )
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    images = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    page = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    regions = models.TextField(
        blank=True,
        default='',
        null=True,
    )
    styles = JSONField(
        blank=True,
        null=True,
    )


class Images(models.Model):

    created = models.DateTimeField(
        auto_now_add=True,
    )
    modified = models.DateTimeField(
        auto_now=True,
    )
    image = models.ImageField(
        upload_to='images',
        height_field=None,
        width_field=None,
        max_length=100,
        null=True,
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    edited_width = models.IntegerField(
        blank=True,
        null=True,
    )
    edited_crop = models.CharField(
        max_length=80,
        blank=True,
        null=True,
    )
    edited_direction = models.CharField(
        max_length=5,
        blank=True,
        null=True,
    )
    background_image = models.BooleanField(
        default=False,
    )
    template_url = models.CharField(
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
        return self.url


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
        verbose_name_plural = _("Company email")

    email = models.EmailField(
        verbose_name=_("Company email"),
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.email


class CompanySocialMedia(models.Model):

    class Meta:
        verbose_name = _("Social media")
        verbose_name_plural = _("Social media")

    icon_name = models.CharField(
        verbose_name=_("Icon name"),
        choices=(),
        max_length=20,
        null=True,
        blank=True,
    )
    url = models.URLField(
        verbose_name=_("Url"),
        null=True,
        blank=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field('icon_name').choices = lazy(
            get_social_media_icons_names,
        )()

    def __str__(self):
        return f'{self.icon_name} : {self.url}'


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
        settings.AUTH_USER_MODEL,
        models.SET_NULL,
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

    def get_email(self):
        return mark_safe("<br>".join([o.email for o in self.email.all()]))

    def get_phone(self):
        return mark_safe("<br>".join([str(o.phone) for o in self.phone.all()]))

    def get_social_media(self):
        objs = self.social_media.all()
        return mark_safe("<br>".join([f"{o.icon_name}: {o.url}" for o in objs]))


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
        settings.AUTH_USER_MODEL,
        models.SET_NULL,
        blank=True,
        null=True,
    )
    show = models.BooleanField(
        verbose_name=_("Show"),
        default=False,
        help_text=_("Show header"),
    )

    def __str__(self):
        return self.name
