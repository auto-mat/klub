import datetime

from aklub.models import CompanyProfile, ProfileEmail

from django.test import TestCase
from django.urls import reverse

from freezegun import freeze_time

from model_mommy import mommy

from oauth2_provider.models import Application


def login_mixin():
    app = mommy.make(
         'oauth2_provider.application',
         name="Test Application",
         client_type=Application.CLIENT_CONFIDENTIAL,
         authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
    )

    mommy.make(
        'oauth2_provider.accesstoken',
        token='foo',
        application=app,
        expires=datetime.datetime.now() + datetime.timedelta(days=999),
        scope='read write',
    )


@freeze_time("2015-5-1")
class CreateDpchUserProfileViewTest(TestCase):

    def setUp(self):
        login_mixin()

        unit = mommy.make('aklub.administrativeunit', name='test_unit')
        self.event = mommy.make('aklub.event', slug='event_slug', administrative_units=[unit, ])
        self.bank_acc = mommy.make('aklub.bankaccount', bank_account='11122/111', slug='bank_slug', administrative_unit=unit)

    def test_post_request(self):
        url = reverse('userprofile_vs')
        header = {'Authorization': 'Bearer foo'}
        # required fields
        data = {
            'email': 'test_user@test.com',
            'first_name': 'test_name',
            'last_name': 'test_last_name',
            'telephone': '111222333',
            'money_account': 'bank_slug',
            'event': 'event_slug',
            'amount': '111',
            'regular': True,
        }
        response = self.client.post(url, data=data, **header)
        self.assertEqual(response.status_code, 200)
        user = ProfileEmail.objects.get(email='test_user@test.com').user

        dpch = user.userchannels.first()
        self.assertEqual(dpch.VS, response.json()['VS'])
        self.assertEqual(dpch.expected_date_of_first_payment, datetime.date(2015, 5, 4))
        self.assertEqual(dpch.regular_payments, 'regular')
        self.assertEqual(dpch.regular_amount, 111)
        self.assertEqual(dpch.event, self.event)
        self.assertEqual(dpch.money_account, self.bank_acc)

        self.assertEqual(user.first_name, 'test_name')
        self.assertEqual(user.last_name, 'test_last_name')

        self.assertEqual(user.telephone_set.first().telephone, '111222333')
        # update fields
        data_update = {
            'street': 'street_name',
            'city': 'city_name',
            'zip_code': '111 22',
            'birth_day': '11',
            'birth_month': '2',
            'age_group': '1999',
            'sex': 'male',
            'telephone': '333222111',
        }
        data.update(data_update)
        response = self.client.post(url, data=data, **header)
        self.assertEqual(response.status_code, 200)

        user = ProfileEmail.objects.get(email='test_user@test.com').user
        # same VS
        self.assertEqual(dpch.VS, response.json()['VS'])
        # updated data
        self.assertEqual(user.street, 'street_name')
        self.assertEqual(user.city, 'city_name')
        self.assertEqual(user.zip_code, '111 22')
        self.assertEqual(user.birth_day, 11)
        self.assertEqual(user.birth_month, 2)
        self.assertEqual(user.age_group, 1999)
        self.assertEqual(user.sex, 'male')
        self.assertCountEqual(user.telephone_set.values_list('telephone', flat=True), ['111222333', '333222111'])


@freeze_time("2015-5-1")
class CreateDpchCompanyProfileViewTest(TestCase):
    def setUp(self):
        login_mixin()
        unit = mommy.make('aklub.administrativeunit', name='test_unit')
        self.event = mommy.make('aklub.event', slug='event_slug', administrative_units=[unit, ])
        self.bank_acc = mommy.make('aklub.bankaccount', bank_account='11122/111', slug='bank_slug', administrative_unit=unit)

    def test_post_request(self):
        url = reverse('companyprofile_vs')
        header = {'Authorization': 'Bearer foo'}
        # required fields
        data = {
            'crn': '63278260',
            'name': 'company_name',
            'email': 'company@test.com',
            'contact_first_name': 'tester',
            'contact_last_name': 'tester_last',
            'telephone': '111222333',
            'money_account': 'bank_slug',
            'event': 'event_slug',
            'amount': '111',
            'regular': True,
        }
        response = self.client.post(url, data=data, **header)
        self.assertEqual(response.status_code, 200)
        user = CompanyProfile.objects.get(crn='63278260')

        dpch = user.userchannels.first()
        self.assertEqual(dpch.VS, response.json()['VS'])
        self.assertEqual(dpch.expected_date_of_first_payment, datetime.date(2015, 5, 4))
        self.assertEqual(dpch.regular_payments, 'regular')
        self.assertEqual(dpch.regular_amount, 111)
        self.assertEqual(dpch.event, self.event)
        self.assertEqual(dpch.money_account, self.bank_acc)

        self.assertEqual(user.name, 'company_name')
        self.assertEqual(user.profileemail_set.first().email, 'company@test.com')
        self.assertEqual(user.telephone_set.first().telephone, '111222333')
        # update fields
        data_update = {
            'street': 'street_name',
            'city': 'city_name',
            'zip_code': '111 22',
            'email': 'company_new@test.com',
            'telephone': '333222111',
        }
        data.update(data_update)
        response = self.client.post(url, data=data, **header)
        self.assertEqual(response.status_code, 200)
        # same VS
        self.assertEqual(dpch.VS, response.json()['VS'])
        user = CompanyProfile.objects.get(crn='63278260')
        # updated data
        self.assertEqual(user.street, 'street_name')
        self.assertEqual(user.city, 'city_name')
        self.assertEqual(user.zip_code, '111 22')
        self.assertCountEqual(user.telephone_set.values_list('telephone', flat=True), ['111222333', '333222111'])
