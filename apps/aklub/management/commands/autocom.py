#!/usr/bin/env python

import aklub

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Checks autocom'  # noqa

    def handle(self, *args, **options):
        aklub.autocom.check(action=u"daily")
