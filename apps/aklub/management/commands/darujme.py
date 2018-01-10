#!/usr/bin/env python

from aklub import darujme
from aklub.models import Campaign

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Checks Darujme.cz for new payments'

    def handle(self, *args, **options):
        for campaign in Campaign.objects.filter(darujme_api_secret__isnull=False).exclude(darujme_api_secret=""):
            print(campaign)
            payment, skipped = darujme.create_statement_from_API(campaign)
            print(payment)
            print("Skipped: ", skipped)
