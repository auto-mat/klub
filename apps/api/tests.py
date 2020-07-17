import datetime

from aklub.models import CompanyProfile, ProfileEmail

from django.test import TestCase
from django.urls import reverse

from freezegun import freeze_time

from interactions.models import Interaction

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
        scope='read write can_create_profiles can_check_if_exist can_create_interactions can_check_last_payments',
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
        self.assertEqual(user.companycontact_set.first().email, 'company@test.com')
        self.assertEqual(user.companycontact_set.first().telephone, '111222333')
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
        self.assertCountEqual(user.companycontact_set.values_list('telephone', flat=True), ['111222333', '333222111'])
        self.assertCountEqual(user.companycontact_set.values_list('email', flat=True), ['company_new@test.com', 'company@test.com'])


class CheckEventViewTest(TestCase):
    def setUp(self):
        login_mixin()

    def test_check_if_event_exist(self):
        unit = mommy.make('aklub.AdministrativeUnit', name='test_unit')
        event = mommy.make('aklub.Event', slug='event_slug', administrative_units=[unit, ])

        url = reverse('check_event', kwargs={'slug': 'event_slug'})
        header = {'Authorization': 'Bearer foo'}
        response = self.client.get(url, **header)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['slug'], event.slug)


class CheckMoneyAccountViewTest(TestCase):
    def setUp(self):
        login_mixin()

    def test_check_if_event_exist(self):
        unit = mommy.make('aklub.administrativeunit', name='test_unit')
        money_account = mommy.make('aklub.MoneyAccount', slug='money_account_slug', administrative_unit=unit)

        url = reverse('check_moneyaccount', kwargs={'slug': 'money_account_slug'})
        header = {'Authorization': 'Bearer foo'}
        response = self.client.get(url, **header)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['slug'], money_account.slug)


@freeze_time("2015-5-1")
class CheckLastPaymentsViewTest(TestCase):
    def setUp(self):
        login_mixin()

    def test_check_last_payments(self):
        user = mommy.make('aklub.Profile', id=22)
        unit = mommy.make('aklub.AdministrativeUnit', name='test_unit')
        money_account = mommy.make('aklub.MoneyAccount', slug='money_account_slug', administrative_unit=unit)
        event = mommy.make('aklub.Event', slug='event_slug', administrative_units=[unit, ])
        dpch = mommy.make('aklub.DonorPaymentChannel', event=event, money_account=money_account, VS=1111, user=user)

        mommy.make('aklub.Payment', date='2015-04-3', amount=100, user_donor_payment_channel=dpch)  # out of 14 days range
        payment_2 = mommy.make('aklub.Payment', date='2015-04-18', amount=100, user_donor_payment_channel=dpch)
        payment_3 = mommy.make('aklub.Payment', date='2015-04-22', amount=100, user_donor_payment_channel=dpch)

        url = reverse('check_last_payments')
        header = {'Authorization': 'Bearer foo'}
        data = {
            'event': event.slug,
            'money_account': money_account.slug,
            'VS': dpch.VS,
            'amount': '100',
            'date': '2015-4-10',
        }
        response = self.client.post(url, data=data, **header)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.json()), 2)
        resp_data = sorted(response.json(), key=lambda k: k['date'])

        self.assertEqual(resp_data[0]['amount'], payment_2.amount)
        self.assertEqual(resp_data[0]['date'], payment_2.date)
        self.assertEqual(resp_data[0]['profile_id'], user.id)

        self.assertEqual(resp_data[1]['amount'], payment_3.amount)
        self.assertEqual(resp_data[1]['date'], payment_3.date)
        self.assertEqual(resp_data[1]['profile_id'],  user.id)


class CreateInteractionTest(TestCase):
    def setUp(self):
        login_mixin()

    def test_create_interaction(self):
        user = mommy.make('aklub.Profile', id=22)
        unit = mommy.make('aklub.AdministrativeUnit', name='test_unit')
        event = mommy.make('aklub.Event', slug='event_slug', administrative_units=[unit, ])

        url = reverse('create_interaction')
        header = {'Authorization': 'Bearer foo'}
        data = {
            'date': '2015-4-10T15:15',
            'event': event.slug,
            'profile_id': user.id,
            'interaction_type': 'certificate',
            'text': 'hello world',
        }
        response = self.client.post(url, data=data, **header)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

        interaction = Interaction.objects.get(user_id=user, date_from='2015-4-10T15:15')
        self.assertEqual(interaction.event, event)
        self.assertEqual(interaction.administrative_unit, unit)
        self.assertEqual(interaction.summary, data['text'])
        self.assertEqual(interaction.subject, 'vizus-certificate')
