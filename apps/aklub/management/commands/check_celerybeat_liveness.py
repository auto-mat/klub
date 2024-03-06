#!/usr/bin/env python

from datetime import datetime, timedelta
import pytz
import shelve

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check Celery beat liveness"  # noqa

    def handle(self, *args, **options):
        now = datetime.now(tz=pytz.utc)
        file_data = shelve.open(
            "/tmp/celerybeat-schedule"
        )  # Name of the file used by PersistentScheduler to store the last run times of periodic tasks.

        for task_name, task in file_data["entries"].items():
            try:
                assert now < task.last_run_at + task.schedule.run_every
            except AttributeError:
                assert timedelta() < task.schedule.remaining_estimate(task.last_run_at)
