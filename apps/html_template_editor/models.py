# -*- coding: utf-8 -*-

import uuid

# from django.contrib.auth import get_user_model
from django.db import models

# User = get_user_model()


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
