from __future__ import absolute_import

import os

from celery import Celery

from dotenv import load_dotenv

load_dotenv()

from project.test_celery_liveness import LivenessProbe


# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

from django.conf import settings  # noqa

app = Celery("apps")

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object("django.conf:settings")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.steps["worker"].add(LivenessProbe)
