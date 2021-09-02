import datetime

from aklub.models import ApiAccount, DonorPaymentChannel, Payment

from django.conf import settings
from django.core.cache import cache
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

import requests

from .exceptions import DarujmeConnectionException


def get_or_create_dpch(serializer, profile):
    dpch, created = DonorPaymentChannel.objects.get_or_create(
        event=serializer.validated_data["event"],
        user=profile,
        defaults={
            "money_account": serializer.validated_data["money_account"],
        },
    )
    if created:
        dpch.expected_date_of_first_payment = (
            datetime.date.today() + datetime.timedelta(days=3)
        )
        if serializer.validated_data.get("regular"):
            dpch.regular_payments = "regular"
        else:
            dpch.regular_payments = "onetime"
        dpch.regular_amount = serializer.validated_data["amount"]
        dpch.save()
    return dpch


def check_last_month_year_payment(user):  # noqa
    user = user.get_real_instance()
    if user.is_staff:
        return True

    # check cache first
    found_payment = cache.get(f"{user.id}_paid_section") or False

    if not found_payment:
        # get sum of all payments for last month and last year
        payments_sum = Payment.objects.filter(
            user_donor_payment_channel__user=user,
        ).aggregate(
            sum_last_month=Coalesce(
                Sum(
                    "amount",
                    filter=Q(
                        date__gte=timezone.now().date()
                        - timezone.timedelta(days=40),  # 10 days delay
                    ),
                ),
                0,
            ),
            sum_last_year=Coalesce(
                Sum(
                    "amount",
                    filter=Q(
                        date__gte=timezone.now().date()
                        - timezone.timedelta(days=375),  # 10 days delay
                    ),
                ),
                0,
            ),
        )

        if (
            payments_sum["sum_last_month"] >= settings.SUM_LAST_MONTH_PAYMENTS
            or payments_sum["sum_last_year"] >= settings.SUM_LAST_YEAR_PAYMENTS
        ):
            found_payment = True

        # checking darujme for first payment (that one which is not in out DB)
        for dpch in user.userchannels.all():
            if found_payment:
                break
            api = dpch.money_account
            if isinstance(api, ApiAccount) and dpch.payment_total == 0:
                # we are checking only newcomers => so we check if user confirmed it on darujme
                # filtering from pledgeDate => so from the day, user filled form on darujme and our registered support.
                url = (
                    "https://www.darujme.cz/api/v1/organization/{0}/pledges-by-filter/"
                    "?apiId={1}&apiSecret={2}&projectId={3}&fromPledgedDate={4}".format(
                        api.api_organization_id,
                        api.api_id,
                        api.api_secret,
                        api.project_id,
                        dpch.registered_support.date(),
                    )
                )

                response = requests.get(url)
                if response.status_code != 200:
                    raise DarujmeConnectionException()
                for pledge in response.json()["pledges"]:
                    if pledge["donor"]["email"] == user.get_email_str():
                        transactions = pledge["transactions"]
                        for transaction in transactions:

                            if transaction["state"] in [
                                "success",
                                "sent_to_organization",
                                "success_money_on_account",
                            ]:
                                # we are checking if the user just "donated", we dont know how many... but we let him in.
                                found_payment = True
                                break
        if found_payment:
            cache.set(
                f"{user.id}_paid_section", True, timeout=60 * 60 * 3
            )  # set cache for 3 hours
    return found_payment
