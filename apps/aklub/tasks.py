import datetime

from celery import task

from django.core.management import call_command

import smmapdfs.actions

from . import models
from . import darujme
from . import confirmation
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

@task()
def generate_tax_confirmations():
    year = datetime.datetime.now().year - 1
    payed = models.Payment.objects.filter(date__year=year).exclude(type='expected')
    donors = models.UserProfile.objects.filter(userincampaign__payment__in=payed).order_by('last_name')
    confirmations = []
    for d in donors:
        confirmation, created = d.make_tax_confirmation(year)
        confirmations.append(confirmation)
    smmapdfs.actions.make_pdfsandwich(None, None, confirmations)
