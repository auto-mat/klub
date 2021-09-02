#!/usr/bin/env python
from aklub.models import AdministrativeUnit, ProfileEmail, UserProfile

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = """ creates superuser account and account under
               administrative unit (development purpose)
           """  # noqa

    def handle(self, *args, **options):
        # create superuser
        user, created = UserProfile.objects.get_or_create(
            username=settings.DATABASES["default"]["USER"],
            email=settings.DATABASES["default"]["USER"]
            + "@"
            + settings.DATABASES["default"]["USER"]
            + ".com",
            is_superuser=True,
            is_staff=True,
        )
        user.set_password(settings.DATABASES["default"]["PASSWORD"])
        user.save()

        ProfileEmail.objects.get_or_create(
            user=user,
            email=settings.DATABASES["default"]["USER"]
            + "@"
            + settings.DATABASES["default"]["USER"]
            + ".com",
            is_primary=True,
        )
        if created:
            print(f"superuser is created => {user.username} ")
        else:
            print(f"superuser already exists=> {user.username}")
        # create admin of dump_data administrative_unit
        administrative_unit = AdministrativeUnit.objects.get_or_create(
            name="auto*mat Czech"
        )[0]
        permissions = Permission.objects.exclude(codename="can_edit_all_units")
        group, created = Group.objects.get_or_create(
            name="can_do_everything_under_administrative_unit"
        )
        group.permissions.add(*list(permissions))

        user, created = UserProfile.objects.get_or_create(
            username=settings.DATABASES["default"]["USER"] + "2",
            email=settings.DATABASES["default"]["USER"]
            + "2@"
            + settings.DATABASES["default"]["USER"]
            + ".com",
            is_staff=True,
        )
        user.administrative_units.add(administrative_unit)
        user.administrated_units.add(administrative_unit)
        user.groups.add(group)
        user.set_password(settings.DATABASES["default"]["PASSWORD"])
        user.save()

        ProfileEmail.objects.get_or_create(
            user=user,
            email=settings.DATABASES["default"]["USER"]
            + "2@"
            + settings.DATABASES["default"]["USER"]
            + ".com",
            is_primary=True,
        )
        if created:
            print(f"admin of administrative unit is created => {user.username} ")
        else:
            print(f"admin of administrative unit already exists => {user.username}")
