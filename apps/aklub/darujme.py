# -*- coding: utf-8 -*-
""" Parse reports from Darujme.cz """
import datetime
import logging

from aklub.models import (
    AccountStatements,
    ApiAccount,
    DonorPaymentChannel,
    Payment,
    ProfileEmail,
    Telephone,
    UserProfile,
)
from aklub.views import get_unique_username

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime

import requests

logger = logging.getLogger(__name__)


def create_statement(response, api_account):
    payments = parse_darujme_json(response, api_account)
    if len(payments) > 0:
        a = AccountStatements(
            type="darujme", administrative_unit=api_account.administrative_unit
        )
        a.payments = payments
        a.save()
    else:
        a = None
    return a


def create_statement_from_API(api_account):
    url = api_account.darujme_url()
    response = requests.get(url)
    if response.status_code == 200:
        try:
            return create_statement(response, api_account)
        except Exception as e:  # noqa
            logger.info(f"Error while parsing url: {url} error: {e}")
            return
    else:
        logger.info(f"{url} error status not 200: {response.status_code}")
        return


def create_payments(pledge, api_account):
    is_donor = False  # check if user has any succeful payment
    new_payments = []
    for transaction in pledge["transactions"]:
        # proces only payments which are sent and doesnt exist
        if transaction["state"] != "sent_to_organization":
            logger.info(
                f"skipping payment id:{transaction['transactionId']} for {pledge['donor']['email']}  => not sent "
            )
        elif Payment.objects.filter(
            type="darujme",
            SS=pledge["pledgeId"],
            operation_id=transaction["transactionId"],
        ).exists():
            logger.info(
                f"skipping payment id:{transaction['transactionId']} for {pledge['donor']['email']}  => exists "
            )
            is_donor = True
            continue
        else:
            payment = Payment.objects.create(
                type="darujme",
                SS=pledge["pledgeId"],
                date=parse_datetime(transaction["receivedAt"]).date(),
                operation_id=transaction["transactionId"],
                amount=int(transaction["sentAmount"]["cents"] / 100),  # in cents
                account_name=f"{pledge['donor']['firstName']} {pledge['donor']['lastName']}",
                user_identification=pledge["donor"]["email"],
                recipient_account=api_account,
                custom_fields=pledge["customFields"],
            )

            new_payments.append(payment)
            is_donor = True
    return is_donor, new_payments


def create_donor_profile(pledge, api_account):  # noqa
    """
    update or create new UserProfile and DonorPaymentChannel
    """
    email, email_created = ProfileEmail.objects.get_or_create(
        email=pledge["donor"]["email"].lower(),
        defaults={"is_primary": True},
    )

    if settings.DARUJME_EMAIL_AS_USERNAME:
        username = email.email
    else:
        username = get_unique_username(email.email)

    try:
        user = UserProfile.objects.get(profileemail__email=email.email)
    except UserProfile.DoesNotExist:
        user = UserProfile()
        user.country = ""  # replace default value
    # update only if empty! maybe better handle?
    user.first_name = (
        pledge["donor"]["firstName"] if not user.first_name else user.first_name
    )
    user.last_name = (
        pledge["donor"]["lastName"] if not user.last_name else user.last_name
    )
    user.username = username if not user.username else user.username
    user.street = (
        pledge["donor"]["address"]["street"] if not user.street else user.street
    )
    user.city = pledge["donor"]["address"]["city"] if not user.city else user.city
    user.zip_code = (
        pledge["donor"]["address"]["postCode"] if not user.zip_code else user.zip_code
    )
    user.country = (
        pledge["donor"]["address"]["country"] if not user.country else user.country
    )
    user.save()

    email.user = user
    email.save()
    if email_created:
        logger.info(f"New User created email {email.email}")
    else:
        logger.info(f"Duplicate email {email.email}")
    user.administrative_units.add(api_account.administrative_unit)

    if pledge["donor"]["phone"]:
        tel_number = str(pledge["donor"]["phone"]).replace(" ", "")
        try:
            if not Telephone.objects.filter(telephone=tel_number, user=user).exists():
                new_telephone = Telephone(
                    telephone=tel_number,
                    user=user,
                )
                new_telephone.full_clean()  # check phone number validations
                new_telephone.save()
            else:
                logger.info(
                    f"Duplicate telephone {tel_number} for email: {email.email}"
                )
        except ValidationError:
            logger.info(
                f"Bad format of telephone {tel_number} for email: {email.email} => skipping"
            )

    end_of_regular_payments = pledge.get("lastTransactionExpectedOn", None)
    dpch, dpch_created = DonorPaymentChannel.objects.update_or_create(
        user=user,
        event=api_account.event,
        defaults={
            "regular_frequency": "monthly" if pledge["isRecurrent"] else None,
            "regular_payments": "regular" if pledge["isRecurrent"] else "onetime",
            "regular_amount": pledge["pledgedAmount"]["cents"] / 100,  # in cents
            "expected_date_of_first_payment": parse_datetime(
                pledge["pledgedAt"]
            ).date(),
            "end_of_regular_payments": parse_datetime(end_of_regular_payments).date()
            if end_of_regular_payments
            else None,
            "money_account": api_account,
        },
    )
    if dpch_created:
        logger.info(
            f"DonorPaymentChannel for user with email: {pledge['donor']['email']} created"
        )
    else:
        logger.info(
            f"DonorPaymentChannel for user with email: {pledge['donor']['email']} exists => updating"
        )
    return dpch


def pair_payments(dpch, user_payments):
    [
        setattr(payment, "user_donor_payment_channel_id", dpch.id)
        for payment in user_payments
    ]
    Payment.objects.bulk_create(user_payments)


def parse_darujme_json(response, api_account):
    logger.info("Darujme.cz import started at %s" % datetime.datetime.now())
    new_payments = []
    for pledge in response.json()["pledges"]:
        # skip payments where is unknows email
        if not pledge["donor"]["email"]:
            continue
        else:
            is_donor, user_payments = create_payments(pledge, api_account)

            if is_donor:
                dpch = create_donor_profile(pledge, api_account)
            else:
                continue
            pair_payments(dpch, user_payments)
            new_payments += user_payments

    return new_payments


def check_for_new_payments(log_function=None):
    if log_function is None:
        log_function = lambda _: None  # noqa
    for api_account in ApiAccount.objects.filter(is_active=True):
        log_function(api_account)
        payments = create_statement_from_API(api_account)
        log_function(payments)
