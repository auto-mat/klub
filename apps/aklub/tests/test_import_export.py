import datetime
import os
import pathlib
import re

from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TransactionTestCase
from django.urls import reverse

from interactions.models import Interaction

from model_mommy import mommy

from .recipes import generic_profile_recipe
from .test_admin import CreateSuperUserMixin

from ..models import ( # noqa
            BankAccount, CompanyProfile, ContentType, DonorPaymentChannel,
            Event, Payment, Preference, Profile, ProfileEmail, UserBankAccount, UserProfile,
)


class PaymentsImportExportTests(CreateSuperUserMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.client.force_login(self.superuser)

        au = mommy.make(
                    "aklub.administrativeunit",
                    name='test_unit',
                    )
        event = mommy.make(
            "events.event",
            administrative_units=[au, ],
        )
        self.bank_account = mommy.make(
                            'aklub.BankAccount',
                            id=11,
                            bank_account_number='111111/1111',
                            administrative_unit=au,
                            )
        self.donor_payment_channel = mommy.make(
                            'aklub.donorpaymentchannel',
                            money_account=self.bank_account,
                            id=11,
                            event=event,
        )

    def test_payments_import(self):
        "test payments import"
        address = reverse('admin:aklub_payment_import')
        response_address = self.client.get(address)
        self.assertEqual(response_address.status_code, 200)

        p = pathlib.PurePath(__file__)
        csv_file_create_interactions = os.path.join(p.parents[1], 'test_data', 'create_payments.csv')
        count_before = Payment.objects.count()
        with open(csv_file_create_interactions, "rb") as f:
            data = {
                'input_format': 0,
                'import_file': f,
            }
            response = self.client.post(address, data)
        self.assertEqual(response.status_code, 200)
        count_after = Payment.objects.count()
        # checking that nothing was creted during dry import
        self.assertEqual(count_before, count_after)
        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )

        file_name = [val.split('=')[-1].replace('"', '') for val in result.group(0).split(' ') if 'value' in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': 'create_payments.csv',
            'input_format': 0,
        }

        address = reverse('admin:aklub_payment_process_import')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_payment_changelist'))

        # check new payments
        payments = self.bank_account.payment_set.all()
        p1 = payments.get(amount='20000')
        self.assertEqual(p1.recipient_account, self.bank_account)
        self.assertEqual(p1.user_donor_payment_channel, None)
        self.assertEqual(p1.date,  datetime.date(2017, 12, 24))
        self.assertEqual(p1.amount, 20000)
        self.assertEqual(p1.VS, '')
        self.assertEqual(p1.VS2, '')
        self.assertEqual(p1.SS, '')
        self.assertEqual(p1.KS, '')
        self.assertEqual(p1.BIC, '')
        self.assertEqual(p1.user_identification, '')
        self.assertEqual(p1.type, 'cash')
        self.assertEqual(p1.done_by, '')
        self.assertEqual(p1.account_name, '')
        self.assertEqual(p1.bank_name, '')
        self.assertEqual(p1.transfer_note, '')
        self.assertEqual(p1.currency, '')
        self.assertEqual(p1.recipient_message, '')
        self.assertEqual(p1.operation_id, '')
        self.assertEqual(p1.transfer_type, '')
        self.assertEqual(p1.specification, '')
        self.assertEqual(p1.order_id, '')

        p2 = payments.get(amount='111')
        self.assertEqual(p2.recipient_account, self.bank_account)
        self.assertEqual(p2.user_donor_payment_channel, self.donor_payment_channel)
        self.assertEqual(p2.date, datetime.date(2018, 2, 20))
        self.assertEqual(p2.amount, 111)
        self.assertEqual(p2.VS, '1234')
        self.assertEqual(p2.VS2, '')
        self.assertEqual(p2.SS, '111')
        self.assertEqual(p2.KS, '')
        self.assertEqual(p2.BIC, '')
        self.assertEqual(p2.user_identification, '')
        self.assertEqual(p2.type, 'bank-transfer')
        self.assertEqual(p2.done_by, 'Test')
        self.assertEqual(p2.account_name, '')
        self.assertEqual(p2.bank_name, '')
        self.assertEqual(p2.transfer_note, 'have nice day!2')
        self.assertEqual(p2.currency, 'CZ')
        self.assertEqual(p2.recipient_message, 'Message Test?')
        self.assertEqual(p2.operation_id, '')
        self.assertEqual(p2.transfer_type, '')
        self.assertEqual(p2.specification, '')
        self.assertEqual(p2.order_id, '')

        p3 = payments.get(amount='10000')
        self.assertEqual(p3.recipient_account, self.bank_account)
        self.assertEqual(p3.user_donor_payment_channel, None)
        self.assertEqual(p3.date, datetime.date(2020, 2, 20))
        self.assertEqual(p3.amount, 10000)
        self.assertEqual(p3.VS, '1234')
        self.assertEqual(p3.VS2, '4321')
        self.assertEqual(p3.SS, '111')
        self.assertEqual(p3.KS, '111')
        self.assertEqual(p3.BIC, '443322')
        self.assertEqual(p3.user_identification, '')
        self.assertEqual(p3.type, 'bank-transfer')
        self.assertEqual(p3.done_by, 'Done by')
        self.assertEqual(p3.account_name, 'Testing user account')
        self.assertEqual(p3.bank_name, 'TestBANK s.r.o.')
        self.assertEqual(p3.transfer_note, 'have nice day!')
        self.assertEqual(p3.currency, 'CZ')
        self.assertEqual(p3.recipient_message, 'Test message')
        self.assertEqual(p3.operation_id, '')
        self.assertEqual(p3.transfer_type, 'Bezhotovostní příjem')
        self.assertEqual(p3.specification, '')
        self.assertEqual(p3.order_id, '')

    def test_payment_export(self):
        mommy.make(
            'aklub.payment',
            recipient_account=self.bank_account,
            amount=1000,
            VS='111',
            date=datetime.date(2020, 2, 20),
            transfer_note='export_test_note',
        )
        address = "/aklub/payment/export/"
        post_data = {
            'file_format': 0,
        }
        response = self.client.post(address, post_data)

        self.assertContains(
            response,
            '11,,2020-02-20,1000,111,,,,,,,,,,export_test_note,,,,,,,',
        )


class InteractionsImportExportTests(CreateSuperUserMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.client.force_login(self.superuser)

        self.au = mommy.make(
                'aklub.AdministrativeUnit',
                id=1,
                name='test_unit',
        )
        self.user = mommy.make(
                    'aklub.UserProfile',
                    id=1,
                    username='test_username',

        )
        mommy.make(
                'aklub.ProfileEmail',
                email='test_email@email.com',
                user=self.user,
                is_primary=True,

        )
        self.company = mommy.make(
                'aklub.CompanyProfile',
                id=3,
                username='test_companyname',
        )
        mommy.make(
                'aklub.CompanyContact',
                email='test_email@email.com',
                company=self.company,
                administrative_unit=self.au,
                is_primary=True,
        )
        self.event = mommy.make(
                'events.event',
                id=1,
                name='test_event',
        )

        category = mommy.make(
                'interactions.InteractionCategory',
                category='category',
        )
        self.int_type = mommy.make(
                'interactions.InteractionType',
                category=category,
                name='test_category',
                id=11,
        )

    def test_interaction_import(self):
        "test donor payment channel import"
        address = reverse('admin:interactions_interaction_import')
        response_address = self.client.get(address)
        self.assertEqual(response_address.status_code, 200)

        p = pathlib.PurePath(__file__)
        csv_file_create_interactions = os.path.join(p.parents[1], 'test_data', 'create_interactions.csv')
        count_before = Interaction.objects.count()
        with open(csv_file_create_interactions, "rb") as f:
            data = {
                'input_format': 0,
                'import_file': f,
            }
            response = self.client.post(address, data)
        self.assertEqual(response.status_code, 200)
        count_after = Interaction.objects.count()
        # testing that nothing was created during dry import
        self.assertEqual(count_before, count_after)
        self.assertContains(response, 'test_username', html=True)
        self.assertContains(response, 'test_email@email.com', html=True)

        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )

        file_name = [val.split('=')[-1].replace('"', '') for val in result.group(0).split(' ') if 'value' in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': 'create_interactions.csv',
            'input_format': 0,
        }

        address = reverse('admin:interactions_interaction_process_import')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:interactions_interaction_changelist'))

        # check new interactions
        int1 = Interaction.objects.get(subject='test_subject1')
        self.assertEqual(int1.user.get_email_str(), 'test_email@email.com')
        self.assertEqual(int1.user, self.user)
        self.assertEqual(int1.event, self.event)
        self.assertEqual(int1.created_by, self.user)
        self.assertEqual(int1.handled_by, self.user)
        self.assertEqual(int1.administrative_unit, self.au)
        self.assertEqual(int1.date_from.isoformat(), '2020-02-19T12:08:40+00:00')
        self.assertEqual(int1.next_communication_date.isoformat(), '2020-02-19T12:08:42+00:00')
        self.assertEqual(int1.type, self.int_type)
        self.assertEqual(int1.communication_type, 'individual')
        self.assertEqual(int1.summary, 'happy_day_summary1')
        self.assertEqual(int1.note, 'test_note1')
        self.assertEqual(int1.dispatched, 0)
        self.assertEqual(int1.rating, '1')
        self.assertEqual(int1.next_step, 'call_soon')

        int2 = Interaction.objects.get(subject='test_subject2')
        self.assertEqual(int2.user.username, 'test_username')
        self.assertEqual(int2.event, self.event)
        self.assertEqual(int2.created_by, self.user)
        self.assertEqual(int2.handled_by, self.user)
        self.assertEqual(int2.administrative_unit, self.au)
        self.assertEqual(int2.date_from.isoformat(), '2020-02-19T09:25:35+00:00')
        self.assertEqual(int2.date_to.isoformat(), '2021-02-19T09:25:35+00:00')
        self.assertEqual(int2.next_communication_date, None)
        self.assertEqual(int2.type, self.int_type)
        self.assertEqual(int2.communication_type, 'individual')
        self.assertEqual(int2.summary, 'happy_day_summary2')
        self.assertEqual(int2.note, 'test_note2')
        self.assertEqual(int2.dispatched, 1)
        self.assertEqual(int2.rating, '5')
        self.assertEqual(int2.next_step, 'call_soon')

        int3 = Interaction.objects.get(subject='test_subject3_company')
        self.assertEqual(int3.user.get_email_str(int3.administrative_unit), 'test_email@email.com')
        self.assertEqual(int3.user, self.company)
        self.assertEqual(int3.event, self.event)
        self.assertEqual(int3.created_by, self.user)
        self.assertEqual(int3.handled_by, self.user)
        self.assertEqual(int3.administrative_unit, self.au)
        self.assertEqual(int3.date_from.isoformat(), '2020-02-19T12:08:40+00:00')
        self.assertEqual(int3.date_to, None)
        self.assertEqual(int1.next_communication_date.isoformat(), '2020-02-19T12:08:42+00:00')
        self.assertEqual(int3.type, self.int_type)
        self.assertEqual(int3.communication_type, 'individual')
        self.assertEqual(int3.summary, 'happy_day_summary_company_3')
        self.assertEqual(int3.note, 'test_note3_company')
        self.assertEqual(int3.dispatched, 0)
        self.assertEqual(int3.rating, '1')
        self.assertEqual(int3.next_step, 'call_soon')


class DonorImportExportTests(CreateSuperUserMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.client.force_login(self.superuser)

        au = mommy.make(
                    'aklub.AdministrativeUnit',
                    name='test_unit',
        )
        self.bank_acc = mommy.make(
                    'aklub.BankAccount',
                    id=21,
                    administrative_unit=au,
                    bank_account_number='1111/111',
        )
        self.event1 = mommy.make(
                    'events.event',
                    id=11,
                    name='test',
        )
        self.event2 = mommy.make(
                    'events.event',
                    id=12,
                    name='test_old',
        )
        self.user = mommy.make(
                    'aklub.UserProfile',
                    username='test1',
        )
        mommy.make(
                    'aklub.ProfileEmail',
                    email='test1@test.com',
                    user=self.user,
        )
        self.company = company = mommy.make(
                    'aklub.CompanyProfile',
                    username='test_company1',
        )
        mommy.make(
                    'aklub.CompanyContact',
                    email='test1@test.com',
                    company=company,
        )
        mommy.make(
                    'aklub.DonorPaymentChannel',
                    id=101,
                    user=self.user,
                    VS=9999,
                    SS=111,
                    regular_frequency='quaterly',
                    expected_date_of_first_payment=datetime.date(2010, 2, 11),
                    regular_amount=1000,
                    regular_payments='regular',
                    money_account=self.bank_acc,
                    event=self.event2,
                    end_of_regular_payments=datetime.date(2011, 2, 11),
        )

    def test_dpch_import(self):
        "test donor payment channel import"
        address = reverse('admin:aklub_donorpaymentchannel_import')
        response_address = self.client.get(address)
        self.assertEqual(response_address.status_code, 200)

        p = pathlib.PurePath(__file__)
        csv_file_create_dpch = os.path.join(p.parents[1], 'test_data', 'test_donor_import.csv')
        count_before = DonorPaymentChannel.objects.count()
        with open(csv_file_create_dpch, "rb") as f:
            data = {
                'input_format': 0,
                'import_file': f,
            }
            response = self.client.post(address, data)
        self.assertEqual(response.status_code, 200)
        count_after = DonorPaymentChannel.objects.count()
        # testing that nothing was created during dry import
        self.assertEqual(count_before, count_after)
        self.assertContains(response, 'test1@test.com', html=True)
        self.assertContains(response, '9999/999', html=True)

        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )

        file_name = [val.split('=')[-1].replace('"', '') for val in result.group(0).split(' ') if 'value' in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': 'test_donor_import.csv',
            'input_format': 0,
        }
        address = reverse('admin:aklub_donorpaymentchannel_process_import')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_donorpaymentchannel_changelist'))

        # check new DonorPaymentChannel data (UserProfile)
        new_dpch = DonorPaymentChannel.objects.get(user=self.user, event=self.event1)

        self.assertEqual(new_dpch.money_account, self.bank_acc)
        self.assertEqual(new_dpch.event, self.event1)
        self.assertEqual(new_dpch.VS, '1234')
        self.assertEqual(new_dpch.SS, '222')
        self.assertEqual(new_dpch.regular_frequency, 'monthly')
        self.assertEqual(new_dpch.expected_date_of_first_payment, datetime.date(2016, 9, 16))
        self.assertEqual(new_dpch.regular_amount, 1000)
        self.assertEqual(new_dpch.regular_payments, 'regular')
        self.assertEqual(new_dpch.user_bank_account.bank_account_number, '9999/999')
        self.assertEqual(new_dpch.end_of_regular_payments, datetime.date(2017, 9, 16))
        # CompanyProfile
        new_dpch2 = DonorPaymentChannel.objects.get(user=self.company, event=self.event1)

        self.assertEqual(new_dpch2.money_account, self.bank_acc)
        self.assertEqual(new_dpch2.event, self.event1)
        self.assertEqual(new_dpch2.VS, '4332')
        self.assertEqual(new_dpch2.SS, '4442')
        self.assertEqual(new_dpch2.regular_frequency, 'monthly')
        self.assertEqual(new_dpch2.expected_date_of_first_payment, datetime.date(2016, 1, 12))
        self.assertEqual(new_dpch2.regular_amount, 987)
        self.assertEqual(new_dpch2.regular_payments, 'regular')
        self.assertEqual(new_dpch2.user_bank_account.bank_account_number, '9999/9992')
        self.assertEqual(new_dpch2.end_of_regular_payments, datetime.date(2017, 1, 11))

        # check updated  DonorPaymentChannel data
        dpch_update = DonorPaymentChannel.objects.get(id=101)
        self.assertEqual(dpch_update.money_account, self.bank_acc)
        self.assertEqual(dpch_update.event, self.event2)
        self.assertEqual(dpch_update.VS, '1111')
        self.assertEqual(dpch_update.SS, '333')
        self.assertEqual(dpch_update.regular_frequency, 'monthly')
        self.assertEqual(dpch_update.expected_date_of_first_payment, datetime.date(2016, 1, 11))
        self.assertEqual(dpch_update.regular_amount, 100)
        self.assertEqual(dpch_update.regular_payments, 'regular')
        self.assertEqual(dpch_update.user_bank_account.bank_account_number, '9999/999')
        self.assertEqual(dpch_update.end_of_regular_payments, datetime.date(2017, 1, 11))

    def test_dpch_export(self):
        address = "/aklub/donorpaymentchannel/export/"
        post_data = {
            'file_format': 0,
        }
        response = self.client.post(address, post_data)
        self.assertContains(
            response,
            'test1@test.com,,12,21,9999,111,test1,quaterly,2010-02-11,1000,regular,2011-02-11',
        )


class AdminImportExportTests(CreateSuperUserMixin, TransactionTestCase):
    fixtures = ['conditions', 'users', 'communications']

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.client.force_login(self.superuser)

        au = mommy.make(
            'aklub.AdministrativeUnit',
            name='test',
        )
        mommy.make(
            'aklub.BankAccount',
            id=32,
            administrative_unit=au,
            bank_account_number='2233445566/0100',
        )
        mommy.make(
            'aklub.BankAccount',
            id=33,
            administrative_unit=au,
            bank_account_number='3333333333/0300',
        )

    def get_request(self, params=None):
        request = self.factory.get('/', params)
        request.user = self.superuser
        return request

    def post_request(self, post_data={}, params=None):
        request = self.factory.post('/', data=post_data)
        request.user = self.superuser
        request._dont_enforce_csrf_checks = True
        request.session = 'session'
        request._messages = FallbackStorage(request)
        return request

    def create_profiles(self):
        profiles_data = [
            {
                'type': 'user',
                'model_name': UserProfile._meta.model_name,
                'vs': '140147010',
                'extra_fields': {
                    'sex': 'male',
                    'title_before': 'Ing.',
                    'title_after': 'Phdr.',
                    'first_name': 'Foo',
                    'last_name': 'Bar',
                },
            },
            {
                'type': 'company',
                'model_name': CompanyProfile._meta.model_name,
                'vs': '150157010',
                'extra_fields': {
                    'crn': '11223344',
                    'tin': '55667788',
                    'name': 'Company',
                },
            },
        ]
        # event = mommy.make(
        #     'events.event',
        #     name='Klub přátel Auto*Matu',
        #     created='2015-12-16',
        #     slug='klub',
        #     allow_statistics=True,
        #     darujme_api_id=38571205,
        #     darujme_project_id=38571205,
        #     acquisition_campaign=True,
        #     enable_signing_petitions=True,
        #     enable_registration=True,
        #     darujme_name='Klub přátel Auto*Matu',
        # )
        administrative_units = ['AU1', 'AU2']
        event = Event.objects.get(pk=2)
        for index, profile_type in enumerate(profiles_data):
            model_name = profile_type['model_name']
            generic_profile_recipe._model = 'aklub.{}'.format(model_name)
            fields = {
                'username': 'test.{}'.format(model_name),
                'email': 'test.{0}@{0}.test'.format(model_name),
            }
            fields.update(profile_type['extra_fields'])
            user = generic_profile_recipe.make(**fields)
            administrative_unit = mommy.make(
                'aklub.AdministrativeUnit',
                id=index,
                name=administrative_units[index],
            )
            user.administrated_units.add(administrative_unit)
            inter_category = mommy.make('interactions.interactioncategory', category='testcategory')
            inter_type = mommy.make('interactions.interactiontype', category=inter_category, name='test2type')
            mommy.make(
                'interactions.Interaction',
                dispatched=False,
                date_from='2016-2-9',
                user=user,
                type=inter_type,
                administrative_unit=administrative_unit,
            )
            mommy.make(
                'aklub.TaxConfirmation',
                user_profile=user,
                year=2014,
                amount=2014,
            )
            mommy.make(
                'aklub.DonorPaymentChannel',
                user=user,
                expected_date_of_first_payment=datetime.datetime.strptime('2015-12-16', '%Y-%m-%d'),
                no_upgrade=False,
                registered_support='2015-12-16T18:22:30.128',
                regular_amount=100,
                regular_frequency='monthly',
                regular_payments='regular',
                event=event,
                VS=profile_type['vs'],
            )
            mommy.make(
                'aklub.Preference',
                user=user,
                administrative_unit=administrative_unit,
                newsletter_on=True,
                call_on=True,
                challenge_on=True,
                letter_on=True,
                send_mailing_lists=False,
                public=False,
            )
            user.administrative_units.add(administrative_unit)
            mommy.make(
                'aklub.BankAccount',
                administrative_unit=administrative_unit,
                bank_account_number='2233445566/0100',
            )
            if user.is_userprofile():
                mommy.make(
                    'aklub.ProfileEmail',
                    email=user.email,
                    user=user,
                )
            else:
                mommy.make(
                    'aklub.CompanyContact',
                    email=user.email,
                    company=user,
                    )

    def test_user_profile_export(self):
        """ Test UserProfileAdmin admin model export """
        self.create_profiles()
        address = reverse('admin:aklub_userprofile_export')
        post_data = {
            'file_format': 0,
        }
        response = self.client.post(address, post_data)

        self.assertContains(
            response,
            ''.join(
                [
                    '0,test.userprofile@userprofile.test,,',
                    '"VS:140147010\nevent:Klub přátel Auto*Matu\nbank_accout:\nuser_bank_account:\n\n",',
                    'test.userprofile,2016-09-16 16:22:30,,,en,,Praha 4,Česká republika,,1,,,Česká republika,',
                    ',,False,,False,True,True,True,True,Ing.,Foo,Bar,Phdr.,male,,,',
                ],
            ),
        )

    def test_company_profile_export(self):
        """ Test CompanyProfileAdmin admin model export """
        self.create_profiles()
        address = reverse('admin:aklub_companyprofile_export')
        post_data = {
            'file_format': 0,
        }
        response = self.client.post(address, post_data)
        self.assertContains(
            response,
            ''.join(
                [
                    '1,test.companyprofile@companyprofile.test,-,',
                    '"VS:150157010\nevent:Klub přátel Auto*Matu\nbank_accout:\nuser_bank_account:\n\n",',
                    'test.companyprofile,2016-09-16 16:22:30,,,en,,Praha 4,Česká republika,,1,,,Česká republika,',
                    ',,False,,False,True,True,True,True,Company,11223344,55667788',
                ],
            ),
        )

    def test_userprofile_import(self):
        """ Test UserProfile admin model import """
        administrative_units = ['AU1', 'AU2']
        for index, au in enumerate(administrative_units, 1):
            mommy.make(
                'aklub.AdministrativeUnit',
                id=index,
                name=administrative_units[index - 1],
            )

        p = pathlib.PurePath(__file__)
        csv_file = 'create_user_profiles.csv'
        csv_file_create_user_profiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_userprofile_import')
        profiles_count_before = Profile.objects.count()
        with open(csv_file_create_user_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
        profiles_count_after = Profile.objects.count()
        # checking that new profiles were not created during dry import
        self.assertEqual(profiles_count_before, profiles_count_after)
        self.assertContains(
            response,
            'test.userprofile@userprofile.test',
            html=True,
        )
        self.assertContains(
            response,
            'male',
            html=True,
        )

        # Create model
        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )
        file_name = [val.split('=')[-1].replace('"', '') for val in result.group(0).split(' ') if 'value' in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': csv_file_create_user_profiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_userprofile_process_import')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_userprofile_changelist'))

        user_profile = Profile.objects.filter(email='test.userprofile@userprofile.test')
        self.assertEqual(user_profile.count(), 1)
        self.assertEqual(user_profile[0].sex, 'male')
        donor = DonorPaymentChannel.objects.filter(user=user_profile[0])
        self.assertEqual(donor.count(), 1)
        self.assertEqual(donor[0].VS, '150157010')
        self.assertEqual(donor[0].event.name, 'Zažít město jinak')
        bank_account = BankAccount.objects.filter(bank_account_number='2233445566/0100')
        self.assertEqual(bank_account.count(), 1)
        self.assertEqual(donor[0].money_account, bank_account[0])
        user_bank_account = UserBankAccount.objects.filter(bank_account_number='9988776655/0100')
        self.assertEqual(user_bank_account.count(), 1)
        self.assertEqual(donor[0].user_bank_account, user_bank_account[0])
        self.assertEqual(user_profile[0].polymorphic_ctype, ContentType.objects.get(model='userprofile'))
        self.assertEqual(user_profile[0].username, 'test.userprofile')
        self.assertEqual(user_profile[0].title_before, 'Ing.')
        self.assertEqual(user_profile[0].title_after, 'Phdr.')
        self.assertEqual(user_profile[0].first_name, 'First_name_userprofile')
        self.assertEqual(user_profile[0].last_name, 'Last_name_userprofile')
        self.assertEqual(user_profile[0].country, 'Česká republika')
        self.assertEqual(user_profile[0].correspondence_country, 'Slovakia')
        preference = Preference.objects.filter(user=user_profile[0])
        self.assertEqual(preference.count(), 1)
        self.assertEqual(preference[0].send_mailing_lists, True)
        self.assertEqual(preference[0].letter_on, True)
        self.assertEqual(user_profile[0].administrative_units.all().values_list('name')[0], ('AU2',))

        # Update model (should not update)
        p = pathlib.PurePath(__file__)
        csv_file = 'update_user_profiles.csv'
        csv_file_update_user_profiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_userprofile_import')
        profiles_count_before = Profile.objects.count()
        with open(csv_file_update_user_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        profiles_count_after = Profile.objects.count()
        # checking that new profiles were not created during dry import
        self.assertEqual(profiles_count_before, profiles_count_after)
        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )
        file_name = [val.split("=")[-1].replace('"', '') for val in result.group(0).split(" ") if "value" in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': csv_file_update_user_profiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_userprofile_process_import')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_userprofile_changelist'))

        user_profile = Profile.objects.filter(email='test.userprofile@userprofile.test')
        self.assertEqual(user_profile.count(), 1)
        self.assertEqual(user_profile[0].sex, 'male')
        donor = DonorPaymentChannel.objects.filter(user=user_profile[0])
        self.assertEqual(donor.count(), 1)
        self.assertEqual(donor[0].VS, '150157010')
        self.assertEqual(donor[0].event.name, 'Zažít město jinak')
        bank_account = BankAccount.objects.filter(bank_account_number='2233445566/0100')
        self.assertEqual(bank_account.count(), 1)
        self.assertEqual(donor[0].money_account, bank_account[0])
        user_bank_account = UserBankAccount.objects.filter(bank_account_number='1111111111/0100')
        self.assertEqual(user_bank_account.count(), 1)
        self.assertEqual(user_profile[0].polymorphic_ctype, ContentType.objects.get(model='userprofile'))
        self.assertEqual(user_profile[0].username, 'test.userprofile')
        self.assertEqual(user_profile[0].title_before, 'Ing.')
        preference_count = Preference.objects.filter(user=user_profile[0]).count()
        self.assertEqual(preference_count, 2)
        preference = Preference.objects.filter(user=user_profile[0], administrative_unit=1)
        self.assertEqual(preference[0].send_mailing_lists, False)
        self.assertEqual(preference[0].letter_on, False)
        self.assertEqual(set(user_profile[0].administrative_units.all().values_list('name')), {('AU1',), ('AU2',)})

    def test_userprofile_minimal_fields_import(self):
        """ Test UserProfile admin model minimal fields import """
        p = pathlib.PurePath(__file__)
        csv_file = 'create_user_profiles_minimal_fields.csv'
        csv_file_create_user_profiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_userprofile_import')
        profiles_count_before = Profile.objects.count()
        with open(csv_file_create_user_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
        profiles_count_after = Profile.objects.count()
        # checking that new profiles were not created during dry import
        self.assertEqual(profiles_count_before, profiles_count_after)

        self.assertContains(
            response,
            'male',
            html=True,
        )
        self.assertContains(
            response,
            'female',
            html=True,
        )

        # Create model
        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )
        file_name = [val.split('=')[-1].replace('"', '') for val in result.group(0).split(' ') if 'value' in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': csv_file_create_user_profiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_userprofile_process_import')
        number_of_new_user_profiles = 4
        user_profile_count = UserProfile.objects.count() + number_of_new_user_profiles
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_userprofile_changelist'))
        self.assertEqual(user_profile_count, UserProfile.objects.count())

    def test_companyprofile_minimal_fields_import(self):
        """ Test CompanyProfile admin model minimal fields import """
        p = pathlib.PurePath(__file__)
        csv_file = 'create_company_profiles_minimal_fields.csv'
        csv_file_create_company_profiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_companyprofile_import')
        profiles_count_before = Profile.objects.count()
        with open(csv_file_create_company_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
        profiles_count_after = Profile.objects.count()
        # checking that new profiles were not created during dry import
        self.assertEqual(profiles_count_before, profiles_count_after)
        self.assertContains(
            response,
            '22670319',
            html=True,
        )
        self.assertContains(
            response,
            '45772428',
            html=True,
        )

        # Create model
        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )
        file_name = [val.split('=')[-1].replace('"', '') for val in result.group(0).split(' ') if 'value' in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': csv_file_create_company_profiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_companyprofile_process_import')
        number_of_new_company_profiles = 4
        company_profile_count = CompanyProfile.objects.count() + number_of_new_company_profiles
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_companyprofile_changelist'))
        self.assertEqual(company_profile_count, CompanyProfile.objects.count())

    def test_companyprofile_import(self):
        """ Test CompanyProfile admin model import """
        administrative_units = ['AU1', 'AU2']
        for index, au in enumerate(administrative_units, 1):
            mommy.make(
                'aklub.AdministrativeUnit',
                id=index,
                name=administrative_units[index - 1],
            )

        p = pathlib.PurePath(__file__)
        csv_file = 'create_company_profiles.csv'
        csv_file_create_companyprofiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_companyprofile_import')
        profiles_count_before = Profile.objects.count()
        with open(csv_file_create_companyprofiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
        profiles_count_after = Profile.objects.count()
        # checking that new profiles were not created during dry import
        self.assertEqual(profiles_count_before, profiles_count_after)
        self.assertContains(
            response,
            'test.companyprofile@companyprofile.test',
            html=True,
        )
        self.assertContains(
            response,
            '22670319',
            html=True,
        )
        self.assertContains(
            response,
            '111222333',
            html=True,
        )
        self.assertContains(
            response,
            'Company',
            html=True,
        )
        # Create model
        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )
        file_name = [val.split('=')[-1].replace('"', '') for val in result.group(0).split(' ') if 'value' in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': csv_file_create_companyprofiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_companyprofile_process_import')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_companyprofile_changelist'))

        company_profile = Profile.objects.filter(email='test.companyprofile@companyprofile.test')
        self.assertEqual(company_profile.count(), 1)
        self.assertEqual(company_profile[0].crn, '22670319')
        self.assertEqual(company_profile[0].tin, 'CZ22670319')
        self.assertEqual(company_profile[0].name, 'Company')
        donor = DonorPaymentChannel.objects.filter(user=company_profile[0])
        self.assertEqual(donor.count(), 1)
        self.assertEqual(donor[0].VS, '1960243939')
        self.assertEqual(donor[0].event.name, 'Zažít město jinak')
        bank_account = BankAccount.objects.filter(bank_account_number='2233445566/0100')
        self.assertEqual(bank_account.count(), 1)
        self.assertEqual(donor[0].money_account, bank_account[0])
        user_bank_account = UserBankAccount.objects.filter(bank_account_number='5554443331/0900')
        self.assertEqual(user_bank_account.count(), 1)
        self.assertEqual(donor[0].user_bank_account, user_bank_account[0])
        self.assertEqual(company_profile[0].polymorphic_ctype, ContentType.objects.get(model='companyprofile'))
        self.assertEqual(company_profile[0].username, 'test.companyprofile')
        preference = Preference.objects.filter(user=company_profile[0])
        self.assertEqual(preference.count(), 1)
        self.assertEqual(preference[0].send_mailing_lists, True)
        self.assertEqual(preference[0].letter_on, True)
        self.assertEqual(company_profile[0].administrative_units.all().values_list('name')[0], ('AU2',))
        company_contact = company_profile[0].companycontact_set.first()
        self.assertEqual(company_contact.email, 'test.companyprofile@companyprofile.test')
        self.assertEqual(company_contact.telephone, '111222333')
        self.assertEqual(company_contact.is_primary, None)
        self.assertEqual(company_contact.contact_first_name, "")
        self.assertEqual(company_contact.contact_last_name, "")

        # Update model (shoud not update)
        p = pathlib.PurePath(__file__)
        csv_file = 'update_company_profiles.csv'
        csv_file_update_company_profiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_companyprofile_import')
        profiles_count_before = Profile.objects.count()
        with open(csv_file_update_company_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        profiles_count_after = Profile.objects.count()
        # checking that new profiles were not created during dry import
        self.assertEqual(profiles_count_before, profiles_count_after)
        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )
        file_name = [val.split("=")[-1].replace('"', '') for val in result.group(0).split(" ") if "value" in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': csv_file_update_company_profiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_companyprofile_process_import')
        response = self.client.post(address, post_data)

        self.assertRedirects(response, expected_url=reverse('admin:aklub_companyprofile_changelist'))

        company_profile = Profile.objects.filter(email='test.companyprofile@companyprofile.test')
        self.assertEqual(company_profile.count(), 1)
        self.assertEqual(company_profile[0].crn, '22670319')
        self.assertEqual(company_profile[0].tin, 'CZ22670319')
        self.assertEqual(company_profile[0].name, 'Company')
        donor = DonorPaymentChannel.objects.filter(user=company_profile[0])
        self.assertEqual(donor.count(), 1)
        self.assertEqual(donor[0].event.name, 'Zažít město jinak')
        bank_account = BankAccount.objects.filter(bank_account_number='3333333333/0300')
        self.assertEqual(bank_account.count(), 1)
        self.assertEqual(donor[0].money_account, bank_account[0])
        user_bank_account = UserBankAccount.objects.filter(bank_account_number='5554443331/0900')
        self.assertEqual(user_bank_account.count(), 1)
        self.assertEqual(donor[0].user_bank_account, user_bank_account[0])
        self.assertEqual(company_profile[0].polymorphic_ctype, ContentType.objects.get(model='companyprofile'))
        self.assertEqual(company_profile[0].username, 'test.companyprofile')
        preference_count = Preference.objects.filter(user=company_profile[0]).count()
        self.assertEqual(preference_count, 2)
        preference = Preference.objects.filter(user=company_profile[0], administrative_unit=1)
        self.assertEqual(preference[0].send_mailing_lists, False)
        self.assertEqual(preference[0].letter_on, False)
        self.assertEqual(list(company_profile[0].administrative_units.all().values_list('name').order_by('name')), [('AU1',), ('AU2',)])
