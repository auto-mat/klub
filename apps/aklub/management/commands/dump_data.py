import datetime
from random import randint

from aklub.models import (
            AdministrativeUnit, BankAccount, CompanyProfile,
            DonorPaymentChannel, Event, Payment, ProfileEmail, Telephone, UserBankAccount,
            UserProfile, CompanyContact
            )
from aklub.views import generate_variable_symbol

from django.core.management.base import BaseCommand

from faker import Faker

from interactions.models import Interaction, InteractionType

import unidecode


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('number_of_users', nargs='?', default=100, type=int)
        parser.add_argument('number_of_companies', nargs='?', default=100, type=int)
        parser.add_argument('max_dpch_payments', nargs='?', default=20, type=int)
        parser.add_argument('language', nargs='?', default='cz_CZ', type=str)

    def handle(self, *args, **kwargs): # noqa
        def get_bank_acc_number():
            return str(randint(1000000000, 9999999999)) + '/' + str(randint(1000, 9999))

        def generate_dpch_with_payments(unit, user, user_bank_account, max_payments_to_dpch):
            money_account = unit.moneyaccount_set.first()
            # for every unit we generate donor payment channel
            amount = randint(1, 10)*100
            vs = generate_variable_symbol()
            dpch = DonorPaymentChannel.objects.create(
                                        user=user,
                                        money_account=money_account,
                                        event=unit.event_set.first(),
                                        user_bank_account=user_bank_account,
                                        regular_amount=amount,
                                        regular_frequency='monthly',
                                        VS=vs,
                                        )
            # add payments and match with dpch!
            payments = []
            # we dont want to have all payments on same days
            date = datetime.datetime.now() - datetime.timedelta(days=randint(0, 40))
            for num in range(0, randint(0, max_payments_to_dpch)):
                pay = Payment(
                        recipient_account=money_account,
                        amount=amount,
                        user_donor_payment_channel=dpch,
                        VS=vs,
                        date=date,
                        )
                payments.append(pay)
                # - month
                date = date - datetime.timedelta(days=30)
            Payment.objects.bulk_create(payments)

        def generate_interactions(unit, user, max_payments_to_dpch):
            interactions = []
            inter_type = InteractionType.objects.get(slug='email-auto')
            for num in range(0, max_payments_to_dpch):
                inter = Interaction(
                            date_from=datetime.datetime.now() - datetime.timedelta(days=randint(0, 500), seconds=randint(1000, 10000)),
                            administrative_unit=unit,
                            note=fake.text(),
                            summary=fake.text(),
                            type=inter_type,
                            subject=fake.word() + ' ' + fake.word(),
                            user=user,
                      )
                interactions.append(inter)
            Interaction.objects.bulk_create(interactions)

        number_of_users = kwargs['number_of_users']
        number_of_companies = kwargs['number_of_companies']
        max_payments_to_dpch = kwargs['max_dpch_payments']

        fake = Faker(kwargs['language'])
        # create units
        administrative_units = [
                        AdministrativeUnit.objects.get_or_create(name='auto*mat Czech')[0],
                        AdministrativeUnit.objects.get_or_create(name='auto*mat Slovakia')[0],
                        AdministrativeUnit.objects.get_or_create(name='auto*mat Poland')[0],
        ]

        for unit in administrative_units:
            # create bank accounts
            BankAccount.objects.get_or_create(
                            administrative_unit=unit,
                            defaults={'bank_account_number': get_bank_acc_number()},
                            )
            # create events
            event, _ = Event.objects.get_or_create(
                            administrative_units__id=unit.id,
                            defaults={'name': f'Event -> {unit.name}'},
            )
            if _:
                event.administrative_units.add(unit)
        # generate user profiles
        for number in range(0, number_of_users):
            profile = fake.profile()
            user = UserProfile.objects.create(
                            first_name=profile['name'].split(' ')[0],
                            last_name=profile['name'].split(' ')[1],
                            sex='male' if profile['sex'] == 'M' else 'female',
                            age_group=fake.date_time().year,
                            birth_month=fake.date_time().month,
                            birth_day=fake.date_time().day,
                            street=f'{fake.street_name()} {randint(1,500)}',
                            city=fake.city_name(),
                            zip_code=fake.postcode(),
                            )
            user.administrative_units.set(administrative_units[:randint(1, 3)])
            ProfileEmail.objects.get_or_create(
                        is_primary=True,
                        email=unidecode.unidecode(
                                    user.first_name + user.last_name + str(randint(1, 5)) + '@' +
                                    fake.email().split('@')[1],
                                    ).lower(),
                        defaults={'user': user},
                        )
            Telephone.objects.get_or_create(
                        is_primary=True,
                        telephone=fake.phone_number().replace(' ', ''),
                        defaults={'user': user},
                        )
            user_bank_account = UserBankAccount.objects.create(bank_account_number=get_bank_acc_number())
            for unit in user.administrative_units.all():
                generate_dpch_with_payments(unit, user, user_bank_account, max_payments_to_dpch)
                generate_interactions(unit, user, int(max_payments_to_dpch/3))

        # generate companies
        for number in range(0, number_of_companies):
            profile = fake.profile()
            company = CompanyProfile.objects.create(
                        name=profile['company'],
                        street=f'{fake.street_name()} {randint(1,500)}',
                        city=fake.city_name(),
                        zip_code=fake.postcode(),
            )

            company.administrative_units.set(administrative_units[:randint(1, 3)])

            for unit in company.administrative_units.all():
                profile = fake.profile()
                CompanyContact.objects.get_or_create(
                    is_primary=True,
                    email=unidecode.unidecode(
                                profile['name'].split(' ')[0] + profile['name'].split(' ')[1] +
                                str(randint(1, 5)) + '@' + fake.email().split('@')[1],
                                ).lower(),
                    telephone=fake.phone_number().replace(' ', ''),
                    contact_first_name=profile['name'].split(' ')[0],
                    contact_last_name=profile['name'].split(' ')[1],
                    administrative_unit=unit,
                    defaults={'company': company},

                )
            user_bank_account = UserBankAccount.objects.create(bank_account_number=get_bank_acc_number())
            for unit in company.administrative_units.all():
                generate_dpch_with_payments(unit, company, user_bank_account, max_payments_to_dpch)
                generate_interactions(unit, company, int(max_payments_to_dpch/3))
