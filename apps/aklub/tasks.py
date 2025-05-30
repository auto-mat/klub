import logging
from urllib.parse import urlparse

import redis

from celery import task

from django.conf import settings
from django.core.management import call_command
from django.utils import dateformat, timezone
from django.utils.translation import ugettext_lazy as _

from notifications_edit.utils import send_notification_to_is_staff_members

from oauth2_provider.models import clear_expired

import smmapdfs.actions
from smmapdfs.models import PdfSandwichType

from . import darujme
from aklub import models
from .autocom import check
from .sync_with_daktela_app import (
    delete_contact,
    get_user_auth_token,
    sync_contacts,
)
from .darujme import parse_darujme_json
from .mailing import create_mass_communication_tasks_sync, send_communication_sync

logger = logging.getLogger(__name__)


@task()
def clear_expired_tokens():
    clear_expired()


@task()
def check_autocom_daily(user_profiles=None, action=None):
    check(user_profiles, action)


@task()
def check_darujme():
    darujme.check_for_new_payments()


@task()
def post_office_send_mail():
    call_command("send_queued_mail", processes=1)


@task()
def generate_tax_confirmations(year, profiles_ids, pdf_type_id):
    started = timezone.now()
    payed = models.Payment.objects.filter(date__year=year).exclude(type="expected")
    users = models.Profile.objects.filter(
        userchannels__payment__in=payed, id__in=profiles_ids
    ).distinct()
    pdf_type = PdfSandwichType.objects.get(id=pdf_type_id)
    unit = pdf_type.pdfsandwichtypeconnector.administrative_unit
    confirmations = []
    logger.info(f"Starting creating tax confirmation for users total: {users.count()}")
    for index, user in enumerate(users, start=1):
        try:
            logger.info(f"Creating Tax Confirmation for user: {index}) {user}")
            confirmation, created = user.make_tax_confirmation(year, unit, pdf_type)
        except Exception as e:  # noqa
            logger.info(f"Creating Tax Confirmation for user: {user} FAILED {e}!!")
        # we want to rewrite existed confirmations,
        # but we dont want to send null values to PdfSandwich cuz it raise bug and pdf is not created
        if confirmation:
            confirmations.append(confirmation)
    smmapdfs.actions.make_pdfsandwich(None, None, confirmations)
    send_notification_to_is_staff_members(
        unit,
        _("Tax Confirmation done"),
        _("Task started at  %(started)s was done for  %(users)s profiles")
        % {
            "started": dateformat.format(started, "Y-m-d H:i:s"),
            "users": users.count(),
        },
    )


@task()
def send_communication_task(
    mass_communication_id, communication_type, profile, sending_user_id
):
    send_communication_sync(
        mass_communication_id, communication_type, profile, sending_user_id
    )


@task()
def create_mass_communication_tasks(communication_id, sending_user_id):
    create_mass_communication_tasks_sync(communication_id, sending_user_id)


@task()  # noqa
def parse_account_statement(statement_id):
    statement = models.AccountStatements.objects.get(id=statement_id)
    if (
        statement.csv_file and statement.payment_set.count() == 0
    ):  # new Account statement
        try:
            if statement.type == "account":
                statement.payments = statement.parse_bank_csv_fio()

            elif statement.type == "account_cs":
                statement.payments = statement.parse_bank_csv_cs()

            elif statement.type == "account_kb":
                statement.payments = statement.parse_bank_csv_kb()

            elif statement.type == "account_csob":
                statement.payments = statement.parse_bank_csv_csob()

            elif statement.type == "account_sberbank":
                statement.payments = statement.parse_bank_csv_sberbank()

            elif statement.type == "account_raiffeisenbank":
                statement.payments = statement.parse_bank_csv_raiffeisenbank()

            elif statement.type == "darujme":
                statement.payments, statement.skipped_payments = parse_darujme_json(
                    statement.csv_file
                )
        except Exception as e:  # noqa
            logger.info(f"Error parsing csv_file: {e}")
            statement.save(parse_csv=False)
            raise
        else:
            statement.save()


@task()
def sync_with_daktela(userprofiles_pks):
    """Sync UserProfiles models instances with Daktela app

    :param list userprofiles: UserProfiles models instances id
    """
    userprofiles = models.UserProfile.objects.filter(
        pk__in=userprofiles_pks,
    )
    sync_contacts(userprofiles)


@task()
def delete_contacts_from_daktela(userprofiles_pks):
    """Delete UserProfile models instances from Daktela app Contact models

    :param list userprofiles: Interaction models instances id
    """
    userprofiles = models.UserProfile.objects.filter(
        pk__in=userprofiles_pks,
    )
    user_auth_token = get_user_auth_token()
    for userprofile in userprofiles:
        delete_contact(userprofile, user_auth_token)
    userprofiles.delete()


@task()
def check_celerybeat_liveness(set_key=True):
    """Check Celery Beat liveness with setting Redis key"""
    parsed_redis_url = urlparse(settings.REDIS_URL)
    redis_instance = redis.StrictRedis(
        host=parsed_redis_url.hostname,
        port=parsed_redis_url.port if parsed_redis_url.port else 6379,
        db=0,
    )
    if set_key:
        redis_instance.set(
            settings.CELERYBEAT_LIVENESS_REDIS_UNIQ_KEY,
            settings.CELERYBEAT_LIVENESS_REDIS_UNIQ_KEY,
            ex=120,
        )
    else:
        return redis_instance.get(settings.CELERYBEAT_LIVENESS_REDIS_UNIQ_KEY)
