
import datetime
import os
import pathlib
import re

from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
from django.urls import reverse

from model_mommy import mommy

from .recipes import generic_profile_recipe
from .test_admin import CreateSuperUserMixin

from ..models import ( # noqa
            BankAccount, CompanyProfile, ContentType, DonorPaymentChannel,
            Event, Interaction, Preference, Profile, ProfileEmail, UserBankAccount, UserProfile,
)


class InteractionsImportExportTests(CreateSuperUserMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.client.force_login(self.superuser)

        self.user = mommy.make(
                    'aklub.UserProfile',
                    id=1,
                    username='test_user',

        )
        mommy.make(
                'aklub.ProfileEmail',
                email='test_user@test.com',
                user=self.user,
                is_primary=True,

        )
        self.au = mommy.make(
                'aklub.AdministrativeUnit',
                id=1,
                name='test_unit',
        )
        self.event = mommy.make(
                'aklub.Event',
                id=1,
                name='test_event',
        )

    def test_interaction_import(self):
        "test donor payment channel import"
        address = reverse('admin:aklub_interaction_import')
        response_address = self.client.get(address)
        self.assertEqual(response_address.status_code, 200)

        p = pathlib.PurePath(__file__)
        csv_file_create_interactions = os.path.join(p.parents[1], 'test_data', 'create_interactions.csv')

        with open(csv_file_create_interactions, "rb") as f:
            data = {
                'input_format': 0,
                'import_file': f,
            }
            response = self.client.post(address, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test_user', html=True)
        self.assertContains(response, 'test_user@test.com', html=True)

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

        address = reverse('admin:aklub_interaction_process_import')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_interaction_changelist'))

        # check new interactions
        int1 = Interaction.objects.get(subject='sub1')
        self.assertEqual(int1.created_by, self.user)
        self.assertEqual(int1.handled_by, self.user)
        self.assertEqual(int1.administrative_unit, self.au)
        self.assertEqual(int1.date.isoformat(), '2019-12-10T08:59:22+00:00')
        self.assertEqual(int1.method, 'email')
        self.assertEqual(int1.type, 'individual')
        self.assertEqual(int1.summary, 'text1')
        self.assertEqual(int1.note, 'Note1')
        self.assertEqual(int1.send, 0)
        self.assertEqual(int1.dispatched, 0)

        int2 = Interaction.objects.get(subject='sub2')
        self.assertEqual(int2.created_by, self.user)
        self.assertEqual(int2.handled_by, self.user)
        self.assertEqual(int2.administrative_unit, self.au)
        self.assertEqual(int2.date.isoformat(), '2017-12-10T08:59:22+00:00')
        self.assertEqual(int2.method, 'phonecall')
        self.assertEqual(int2.type, 'mass')
        self.assertEqual(int2.summary, 'text2')
        self.assertEqual(int2.note, 'Note2')
        self.assertEqual(int2.send, 0)
        self.assertEqual(int2.dispatched, 0)


class DonorImportExportTests(CreateSuperUserMixin, TestCase):
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
                    administrative_unit=au,
                    bank_account_number='1111/111',
        )
        self.event1 = mommy.make(
                    'aklub.Event',
                    name='test',
        )
        self.event2 = mommy.make(
                    'aklub.Event',
                    name='test_old',
        )
        user = mommy.make(
                    'aklub.UserProfile',
                    username='test1',
        )
        mommy.make(
                    'aklub.ProfileEmail',
                    email='test1@test.com',
                    user=user,
        )
        mommy.make(
                    'aklub.DonorPaymentChannel',
                    id=101,
                    user=user,
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

    def test_profile_import(self):
        "test donor payment channel import"
        address = reverse('admin:aklub_donorpaymentchannel_import')
        response_address = self.client.get(address)
        self.assertEqual(response_address.status_code, 200)

        p = pathlib.PurePath(__file__)
        csv_file_create_dpch = os.path.join(p.parents[1], 'test_data', 'test_donor_import.csv')

        with open(csv_file_create_dpch, "rb") as f:
            data = {
                'input_format': 0,
                'import_file': f,
            }
            response = self.client.post(address, data)
        self.assertEqual(response.status_code, 200)
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

        # check new DonorPaymentChannel data
        email = ProfileEmail.objects.get(email='test1@test.com')
        new_dpch = DonorPaymentChannel.objects.get(user=email.user, event=self.event1)

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
            'test1@test.com,,test_old,1111/111,9999,111,test1,quaterly,2010-02-11,1000,regular,2011-02-11',
        )


class AdminImportExportTests(CreateSuperUserMixin, TestCase):
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
            administrative_unit=au,
            bank_account_number='2233445566/0100',
        )
        mommy.make(
            'aklub.BankAccount',
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
        #     'aklub.Event',
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
            mommy.make(
                'aklub.Interaction',
                dispatched=False,
                date='2016-2-9',
                user=user,
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
            mommy.make(
                'aklub.ProfileEmail',
                email=user.email,
                user=user,
            )

    def test_profile_export(self):
        """ Test ProfileAdmin admin model export """
        self.create_profiles()
        address = reverse('admin:aklub_profile_export')
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
                    ',,False,,False,True,True,True,True,,,,male,Phdr.,Foo,Bar,Ing.,,,userprofile,',
                ],
            ),
        )
        self.assertContains(
            response,
            ''.join(
                [
                    '1,test.companyprofile@companyprofile.test,,',
                    '"VS:150157010\nevent:Klub přátel Auto*Matu\nbank_accout:\nuser_bank_account:\n\n",',
                    'test.companyprofile,2016-09-16 16:22:30,,,en,,Praha 4,Česká republika,,1,,,Česká republika,',
                    ',,False,,False,True,True,True,True,Company,11223344,55667788,,,,,,,,companyprofile,',
                ],
            ),
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
                    '1,test.companyprofile@companyprofile.test,,',
                    '"VS:150157010\nevent:Klub přátel Auto*Matu\nbank_accout:\nuser_bank_account:\n\n",',
                    'test.companyprofile,2016-09-16 16:22:30,,,en,,Praha 4,Česká republika,,1,,,Česká republika,',
                    ',,False,,False,True,True,True,True,Company,11223344,55667788',
                ],
            ),
        )

    def test_profile_import(self):
        """ Test Profile admin model import """
        administrative_units = ['AU1', 'AU2']
        for index, au in enumerate(administrative_units, 1):
            mommy.make(
                'aklub.AdministrativeUnit',
                id=index,
                name=administrative_units[index - 1],
            )

        p = pathlib.PurePath(__file__)
        csv_file_create_profiles = p.parents[1] / 'test_data' / 'create_profiles.csv'
        address = reverse('admin:aklub_profile_import')
        with open(csv_file_create_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'test.companyprofile@companyprofile.test',
            html=True,
        )
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
        self.assertContains(
            response,
            '22670319',
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
            'original_file_name': csv_file_create_profiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_profile_process_import')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_profile_changelist'))

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
        preference = Preference.objects.filter(user=user_profile[0])
        self.assertEqual(preference.count(), 1)
        self.assertEqual(preference[0].send_mailing_lists, True)
        self.assertEqual(preference[0].letter_on, True)

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
        preference = Preference.objects.filter(user=user_profile[0])
        self.assertEqual(preference.count(), 1)
        self.assertEqual(preference[0].send_mailing_lists, True)
        self.assertEqual(preference[0].letter_on, True)

        # Update model
        p = pathlib.PurePath(__file__)
        csv_file_update_profiles = p.parents[1] / 'test_data' / 'update_profiles.csv'
        address = reverse('admin:aklub_profile_import')
        with open(csv_file_update_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)

        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )
        file_name = [val.split("=")[-1].replace('"', '') for val in result.group(0).split(" ") if "value" in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': csv_file_create_profiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_profile_process_import')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_profile_changelist'))

        user_profile = Profile.objects.filter(email='test.userprofile@userprofile.test')
        self.assertEqual(user_profile.count(), 1)
        self.assertEqual(user_profile[0].sex, 'female')
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
        self.assertEqual(user_profile[0].title_before, 'Mgr.')
        preference = Preference.objects.filter(user=user_profile[0])
        self.assertEqual(preference.count(), 1)
        self.assertEqual(preference[0].send_mailing_lists, False)
        self.assertEqual(preference[0].letter_on, False)

        company_profile = Profile.objects.filter(email='test.companyprofile@companyprofile.test')
        self.assertEqual(company_profile.count(), 1)
        self.assertEqual(company_profile[0].crn, '22670319')
        self.assertEqual(company_profile[0].tin, 'CZ22670319')
        self.assertEqual(company_profile[0].name, 'Update Company')
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
        preference = Preference.objects.filter(user=company_profile[0])
        self.assertEqual(preference.count(), 1)
        self.assertEqual(preference[0].send_mailing_lists, False)
        self.assertEqual(preference[0].letter_on, False)

    def test_profile_minimal_fields_import(self):
        """ Test Profile admin model minimal fields import """
        p = pathlib.PurePath(__file__)
        csv_file = 'create_profiles_minimal_fields.csv'
        csv_file_create_profiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_profile_import')
        with open(csv_file_create_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '22670319',
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
            'original_file_name': csv_file_create_profiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_profile_process_import')
        number_of_new_profiles = 2
        profile_count = Profile.objects.count() + number_of_new_profiles
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_profile_changelist'))
        self.assertEqual(profile_count, Profile.objects.count())

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
        with open(csv_file_create_user_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
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
        preference = Preference.objects.filter(user=user_profile[0])
        self.assertEqual(preference.count(), 1)
        self.assertEqual(preference[0].send_mailing_lists, True)
        self.assertEqual(preference[0].letter_on, True)
        self.assertEqual(user_profile[0].administrative_units.all().values_list('name')[0], ('AU2',))

        # Update model
        p = pathlib.PurePath(__file__)
        csv_file = 'update_user_profiles.csv'
        csv_file_update_user_profiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_userprofile_import')
        with open(csv_file_update_user_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)

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
        self.assertEqual(user_profile[0].sex, 'female')
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
        self.assertEqual(user_profile[0].title_before, 'Mgr.')
        preference_count = Preference.objects.filter(user=user_profile[0]).count()
        self.assertEqual(preference_count, 2)
        preference = Preference.objects.filter(user=user_profile[0], administrative_unit=1)
        self.assertEqual(preference[0].send_mailing_lists, False)
        self.assertEqual(preference[0].letter_on, False)
        self.assertEqual(list(user_profile[0].administrative_units.all().values_list('name')), [('AU1',), ('AU2',)])

    def test_userprofile_minimal_fields_import(self):
        """ Test UserProfile admin model minimal fields import """
        p = pathlib.PurePath(__file__)
        csv_file = 'create_user_profiles_minimal_fields.csv'
        csv_file_create_user_profiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_userprofile_import')
        with open(csv_file_create_user_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
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
        with open(csv_file_create_company_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
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
        with open(csv_file_create_companyprofiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
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
        # Update model
        p = pathlib.PurePath(__file__)
        csv_file = 'update_company_profiles.csv'
        csv_file_update_company_profiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_companyprofile_import')
        with open(csv_file_update_company_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)

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
        self.assertEqual(company_profile[0].name, 'Update Company')
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
        self.assertEqual(list(company_profile[0].administrative_units.all().values_list('name')), [('AU1',), ('AU2',)])
