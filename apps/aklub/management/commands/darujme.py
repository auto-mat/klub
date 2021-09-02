#!/usr/bin/env python

from aklub import darujme

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Checks Darujme.cz for new payments"  # noqa

    def handle(self, *args, **options):
        darujme.check_for_new_payments(log_function=print)
