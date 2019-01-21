from celery import task

from django.core.management import call_command

from . import darujme
from .autocom import check
#from .mailing import send_communication_sync


@task()
def check_autocom_daily():
    check(action="daily")


@task()
def check_darujme():
    darujme.check_for_new_payments()


@task()
def post_office_send_mail():
    call_command('send_queued_mail', processes=1)


@task()
def send_communication_task(mass_communication_id, communication_type, userincampaign_id, sending_user_id, save):
    print("sending to %s" % userincampaign_id)
    send_communication_sync(mass_communication_id, communication_type, userincampaign_id, sending_user_id, save)
