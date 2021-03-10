import datetime
from random import randint

from aklub.models import (
    AdministrativeUnit, BankAccount, CompanyContact, CompanyProfile,
    DonorPaymentChannel, Payment, ProfileEmail, Telephone,
    UserBankAccount, UserProfile,
)

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from events.models import Event

from faker import Faker

from interactions.models import Interaction, InteractionType

import unidecode


class Command(BaseCommand):
    """Generate fake users/companies profiles data"""
    help = 'Generate fake users/companies profiles data' # noqa

    def add_arguments(self, parser):
        parser.add_argument(
            'number_of_users',
            nargs='?',
            default=100,
            type=int,
            help=_('Number of users'),
        )
        parser.add_argument(
            'number_of_companies',
            nargs='?',
            default=100,
            type=int,
            help=_('Number of companies'),
        )
        parser.add_argument(
            'max_dpch_payments',
            nargs='?',
            default=20,
            type=int,
            help=_('Max. DPCH payments'),
        )
        parser.add_argument(
            'language',
            nargs='?',
            default='cz_CZ',
            type=str,
            help=_('Language'),
        )

    def handle(self, *args, **kwargs):
        self._number_of_users = kwargs['number_of_users']
        self._number_of_companies = kwargs['number_of_companies']
        self._max_payments_to_dpch = kwargs['max_dpch_payments']

        self._fake = Faker(kwargs['language'])

        self._generate_administrative_units()
        self._generate_users_profiles()
        self._generate_companies_profiles()

    def _get_bank_acc_number(self):
        """Get bank account"""
        return f"{randint(1000000000, 9999999999)}/{randint(1000, 9999)}"

    def _generate_dpch_with_payments(
            self, unit, user, user_bank_account, max_payments_to_dpch,
    ):
        """Generate DPCH with payments

        :param unit obj: AdministrativeUnit model instance obj
        :param user obj: UserProfile/CompanyProfile model instance obj
        :param user_bank_account obj: UserBankAccount model instance obj
        :param max_payments_to_dpch int: max payments to DPCH
        """
        money_account = unit.moneyaccount_set.first()
        # for every unit we generate donor payment channel
        amount = randint(1, 10)*100
        dpch = DonorPaymentChannel.objects.create(
            user=user,
            money_account=money_account,
            event=unit.event_set.first(),
            user_bank_account=user_bank_account,
            regular_amount=amount,
            regular_frequency='monthly',
        )
        # add payments and match with dpch!
        payments = []
        # we dont want to have all payments on same days
        date = datetime.datetime.now() - datetime.timedelta(
            days=randint(0, 40),
        )
        for num in range(0, randint(1, max_payments_to_dpch)):
            pay = Payment(
                recipient_account=money_account,
                amount=amount,
                user_donor_payment_channel=dpch,
                VS=dpch.VS,
                date=date,
            )
            payments.append(pay)
            # - month
            date = date - datetime.timedelta(days=30)

        Payment.objects.bulk_create(payments)

    def _generate_interactions(self, unit, user, max_payments_to_dpch):
        """Generate instructions

        :param unit obj: AdministrativeUnit model instance obj
        :param user obj: UserProfile/CompanyProfile model instance obj
        :param max_payments_to_dpch int: max payments to DPCH
        """
        interactions = []
        inter_type = InteractionType.objects.get(slug='email-auto')

        for num in range(0, max_payments_to_dpch):
            inter = Interaction(
                date_from=datetime.datetime.now() - datetime.timedelta(
                    days=randint(0, 500),
                    seconds=randint(1000, 10000),
                ),
                administrative_unit=unit,
                note=self._fake.text(),
                summary=self._fake.text(),
                type=inter_type,
                subject=f"{self._fake.word()} {self._fake.word()}",
                user=user,
            )
            interactions.append(inter)

        Interaction.objects.bulk_create(interactions)

    def _generate_administrative_units(self):
        """Generate administrative units"""
        # create units
        self._administrative_units = [
            AdministrativeUnit.objects.get_or_create(
                name='auto*mat Czech',
            )[0],
            AdministrativeUnit.objects.get_or_create(
                name='auto*mat Slovakia',
            )[0],
            AdministrativeUnit.objects.get_or_create(
                name='auto*mat Poland',
            )[0],
        ]
        for unit in self._administrative_units:
            # create bank accounts
            BankAccount.objects.get_or_create(
                administrative_unit=unit,
                defaults={'bank_account_number': self._get_bank_acc_number()},
            )
            # create events
            event, _ = Event.objects.get_or_create(
                administrative_units__id=unit.id,
                defaults={
                    'name': f"Event -> {unit.name}",
                    'variable_symbol_prefix': str(randint(10001, 88888)),
                },
            )
            if _:
                event.administrative_units.add(unit)

    def _generate_users_profiles(self):
        """Generate users profiles"""
        # generate user profiles
        for number in range(0, self._number_of_users):
            profile = self._fake.profile()
            user = UserProfile.objects.create(
                first_name=profile['name'].split(' ')[0],
                last_name=profile['name'].split(' ')[1],
                sex='male' if profile['sex'] == 'M' else 'female',
                age_group=self._fake.date_time().year,
                birth_month=self._fake.date_time().month,
                birth_day=self._fake.date_time().day,
                street=f"{self._fake.street_name()} {randint(1, 500)}",
                city=self._fake.city_name(),
                zip_code=self._fake.postcode(),
            )
            user.administrative_units.set(
                self._administrative_units[:randint(1, 3)],
            )
            ProfileEmail.objects.get_or_create(
                is_primary=True,
                email=unidecode.unidecode(
                    f"{user.first_name}{user.last_name}{randint(1, 5)}@"
                    f"{self._fake.email().split('@')[1]}"
                ).lower(),
                defaults={'user': user},
            )
            Telephone.objects.get_or_create(
                is_primary=True,
                telephone=self._fake.phone_number().replace(' ', ''),
                defaults={'user': user},
            )
            user_bank_account = UserBankAccount.objects.create(
                bank_account_number=self._get_bank_acc_number(),
            )
            for unit in user.administrative_units.all():
                self._generate_dpch_with_payments(
                    unit, user, user_bank_account,
                    self._max_payments_to_dpch,
                )
                self._generate_interactions(
                    unit, user, int(self._max_payments_to_dpch / 3),
                )

    def _generate_companies_profiles(self):
        """Generate companies profiles"""
        # generate companies
        for number in range(0, self._number_of_companies):
            profile = self._fake.profile()
            company = CompanyProfile.objects.create(
                name=profile['company'],
                street=f"{self._fake.street_name()} {randint(1, 500)}",
                city=self._fake.city_name(),
                zip_code=self._fake.postcode(),
            )

            company.administrative_units.set(
                self._administrative_units[:randint(1, 3)],
            )

            for unit in company.administrative_units.all():
                profile = self._fake.profile()
                CompanyContact.objects.get_or_create(
                    is_primary=True,
                    email=unidecode.unidecode(
                        f"{profile['name'].split(' ')[0]}"
                        f"{profile['name'].split(' ')[1]}"
                        f"{str(randint(1, 5))}@"
                        f"{self._fake.email().split('@')[1]}"
                    ).lower(),
                    telephone=self._fake.phone_number().replace(' ', ''),
                    contact_first_name=profile['name'].split(' ')[0],
                    contact_last_name=profile['name'].split(' ')[1],
                    administrative_unit=unit,
                    defaults={'company': company},
                )
            user_bank_account = UserBankAccount.objects.create(
                bank_account_number=self._get_bank_acc_number(),
            )
            for unit in company.administrative_units.all():
                self._generate_dpch_with_payments(
                    unit, company, user_bank_account,
                    self._max_payments_to_dpch,
                )
                self._generate_interactions(
                    unit, company, int(self._max_payments_to_dpch / 3),
                )
