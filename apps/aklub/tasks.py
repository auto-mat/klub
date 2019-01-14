from celery import task
from django.core.management import call_command

from . import darujme
from .autocom import check



@task()
def check_autocom_daily():
    check(action="daily")


@task()
def check_darujme():
    darujme.check_for_new_payments()

@task()
def post_office_send_mail():
    call_command('send_queued_mail', processes=1)
