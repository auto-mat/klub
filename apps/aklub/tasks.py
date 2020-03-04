from celery import task

from django.core.management import call_command

import smmapdfs.actions
from smmapdfs.models import PdfSandwichType

from . import darujme
from . import models
from .autocom import check
from .darujme import parse_darujme
from .mailing import create_mass_communication_tasks_sync, send_communication_sync


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
def generate_tax_confirmations(year, profiles_ids, pdf_type_id):

    payed = models.Payment.objects.filter(date__year=year).exclude(type='expected')
    users = models.Profile.objects.filter(userchannels__payment__in=payed, id__in=profiles_ids).distinct()
    pdf_type = PdfSandwichType.objects.get(id=pdf_type_id)
    unit = pdf_type.pdfsandwichtypeconnector.administrative_unit
    confirmations = []
    for user in users:
        confirmation, created = user.make_tax_confirmation(year, unit, pdf_type)
        confirmations.append(confirmation)

    smmapdfs.actions.make_pdfsandwich(None, None, confirmations)


@task()
def send_communication_task(mass_communication_id, communication_type, userincampaign_id, sending_user_id):
    print("sending to %s" % userincampaign_id)
    send_communication_sync(mass_communication_id, communication_type, userincampaign_id, sending_user_id)


@task()
def create_mass_communication_tasks(communication_id, sending_user_id):
    create_mass_communication_tasks_sync(communication_id, sending_user_id)


@task()
def parse_account_statement(statement_id):
    statement = models.AccountStatements.objects.get(id=statement_id)
    if statement.csv_file and statement.payment_set.count() == 0:  # new Account statement
        if statement.type == 'account':
            statement.payments = statement.parse_bank_csv_fio()

        elif statement.type == 'account_cs':
            statement.payments = statement.parse_bank_csv_cs()

        elif statement.type == 'account_kb':
            statement.payments = statement.parse_bank_csv_kb()

        elif statement.type == 'account_csob':
            statement.payments = statement.parse_bank_csv_csob()

        elif statement.type == 'account_sberbank':
            statement.payments = statement.parse_bank_csv_sberbank()

        elif statement.type == 'darujme':
            statement.payments, statement.skipped_payments = parse_darujme(statement.csv_file)
    statement.save()
