#!/usr/bin/env python

from django.core.management.base import BaseCommand
import aklub


class Command(BaseCommand):
    help = 'Checks autocom'

    def handle(self, *args, **options):
        aklub.autocom.check(action=u"daily")
