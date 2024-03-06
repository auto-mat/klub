#!/usr/bin/env python

import sys
from urllib.parse import urlparse

import redis

from django.conf import settings
from django.core.management.base import BaseCommand

from aklub.tasks import check_celerybeat_liveness


class Command(BaseCommand):
    help = "Check Celery beat liveness"  # noqa

    def handle(self, *args, **options):
        if not check_celerybeat_liveness(set_key=False):
            sys.exit(1)
