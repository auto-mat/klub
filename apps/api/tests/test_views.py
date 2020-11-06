import datetime

from aklub.models import CompanyProfile, ProfileEmail

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from freezegun import freeze_time

from interactions.models import Interaction

from model_mommy import mommy

from .utils import app_login_mixin


"""
class GetTokenTest(TestCase):
    def test_get_client_credentials_token(self):
        app = mommy.make(
             'oauth2_provider.application',
             client_type=Application.CLIENT_CONFIDENTIAL,
             authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
             skip_authorization=False,
             client_id='xxx',
             client_secret='xxx',
        )

        data = {
            "grant_type": "client_credentials",
            "client_id": "xxx",
            "client_secret": "xxx",
        }
        url = reverse('oauth2_provider:token')

        response = self.client.post(url, data=data)
        print(response.json())
        # TODO: cleint_type error .... make it works!
        # this test work in postman,.. uh?
        self.assertEqual(response.status_code, 200)

    def test_get_password_token(self):
        pass

"""


@freeze_time("2015-5-1")
class CreateDpchUserProfileViewTest(TestCase):
    def setUp(self):
        app_login_mixin()

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
        app_login_mixin()
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
        app_login_mixin()

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
        app_login_mixin()

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
        app_login_mixin()

    def test_check_last_payments(self):
        user = mommy.make('aklub.Profile', id=22)
        unit = mommy.make('aklub.AdministrativeUnit', name='test_unit')
        money_account = mommy.make('aklub.MoneyAccount', slug='money_account_slug', administrative_unit=unit)
        event = mommy.make('aklub.Event', slug='event_slug', administrative_units=[unit, ])
        dpch = mommy.make('aklub.DonorPaymentChannel', event=event, money_account=money_account, VS=1111, user=user)
        # out of 14 days range payment
        mommy.make(
            'aklub.Payment',
            date='2015-04-3',
            amount=100,
            user_donor_payment_channel=dpch,
            type='bank-transfer',
            operation_id='32',
        )
        # credit card payment (DO NOT SHOW)
        mommy.make(
            'aklub.Payment',
            date='2015-04-18',
            amount=100,
            user_donor_payment_channel=dpch,
            type='creadit_card',
            operation_id='123',
        )
        # correct payments
        payment_2 = mommy.make(
            'aklub.Payment',
            date='2015-04-18',
            amount=100,
            user_donor_payment_channel=dpch,
            type='bank-transfer',
            operation_id='3244',
        )
        payment_3 = mommy.make(
            'aklub.Payment',
            date='2015-04-22',
            amount=100,
            user_donor_payment_channel=dpch,
            type='bank-transfer',
            operation_id='1234',
        )

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
        self.assertEqual(resp_data[0]['operation_id'], payment_2.operation_id)
        self.assertEqual(resp_data[0]['profile_id'], user.id)

        self.assertEqual(resp_data[1]['amount'], payment_3.amount)
        self.assertEqual(resp_data[1]['date'], payment_3.date)
        self.assertEqual(resp_data[1]['operation_id'], payment_3.operation_id)
        self.assertEqual(resp_data[1]['profile_id'],  user.id)


class CreateInteractionTest(TestCase):
    def setUp(self):
        app_login_mixin()

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


class CreateCreditCardPaymentTest(TestCase):
    def setUp(self):
        app_login_mixin()
        unit = mommy.make('aklub.administrativeunit', name='test_unit')
        self.event = mommy.make('aklub.event', slug='event_slug', administrative_units=[unit, ])
        self.bank_acc = mommy.make('aklub.bankaccount', bank_account='11122/111', slug='bank_slug', administrative_unit=unit)

    def test_create_payment_userprofile(self):
        user = mommy.make('aklub.UserProfile')
        email = mommy.make('aklub.ProfileEmail', email='test@test.com', user=user)
        donor_channel = mommy.make('aklub.DonorPaymentChannel', user=user, event=self.event, money_account=self.bank_acc)
        url = reverse('create_credit_card_payment')
        header = {'Authorization': 'Bearer foo'}
        data = {
            'date': '2015-04-10',
            'event': self.event.slug,
            'recipient_account': self.bank_acc.slug,
            'email': email.email,
            'amount': 123456,
            'profile_type': 'user',
            'VS': '332211',
        }
        response = self.client.post(url, data=data, **header)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['profile_id'], user.id)

        payments = donor_channel.payment_set.all()
        self.assertEqual(len(payments), 1)
        payment = payments.first()
        self.assertEqual(str(payment.date), data['date'])
        self.assertEqual(payment.recipient_account, self.bank_acc)
        self.assertEqual(payment.amount, data['amount'])
        self.assertEqual(payment.VS, data['VS'])

    def test_create_payment_companyprofile(self):
        company = mommy.make('aklub.CompanyProfile')
        company_contact = mommy.make('aklub.CompanyContact', email='test@test.com', company=company)
        donor_channel = mommy.make('aklub.DonorPaymentChannel', user=company, event=self.event, money_account=self.bank_acc)
        url = reverse('create_credit_card_payment')
        header = {'Authorization': 'Bearer foo'}
        data = {
            'date': '2021-04-10',
            'event': self.event.slug,
            'recipient_account': self.bank_acc.slug,
            'email': company_contact.email,
            'amount': 654321,
            'profile_type': 'company',
            'VS': '111',
        }
        response = self.client.post(url, data=data, **header)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['profile_id'], company.id)

        payments = donor_channel.payment_set.all()
        self.assertEqual(len(payments), 1)
        payment = payments.first()
        self.assertEqual(str(payment.date), data['date'])
        self.assertEqual(payment.recipient_account, self.bank_acc)
        self.assertEqual(payment.amount, data['amount'])
        self.assertEqual(payment.VS, data['VS'])


class RegisterUserProfileTest(TestCase):
    def setUp(self):
        unit = mommy.make('aklub.administrativeunit', name='test_unit')
        self.event = mommy.make('aklub.event', slug='event_slug', administrative_units=[unit, ])
        self.bank_acc = mommy.make('aklub.bankaccount', bank_account='11122/111', slug='bank_slug', administrative_unit=unit)

    def test_create_payment_userprofile(self):
        url = reverse('register_userprofile')
        header = {"content_type": "application/json"}
        data = {

            'email': 'tester@gmai.com',
            'telephone': '123456789',
            'first_name': 'tester',
            'last_name': 'dunnot',
            'password': 'super_ultra_7853_hard',
            "userchannels": [
                {
                    'event': self.event.slug,
                    'money_account': self.bank_acc.slug,
                    'regular_amount': 123456,
                    'regular_frequency': 'monthly',
                },
            ],
        }
        response = self.client.post(url, data=data, **header)
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        email = ProfileEmail.objects.get(email=data['email'])
        user = email.user
        dpch = user.userchannels.first()
        telephone = user.telephone_set.first()
        # response VS (cuz its read_only)
        self.assertEqual(response_data['userchannels'][0]['VS'], dpch.VS)

        self.assertEqual(email.is_primary, True)

        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.check_password(data['password']), True)

        self.assertEqual(telephone.is_primary, True)
        self.assertEqual(telephone.telephone, data['telephone'])

        self.assertEqual(dpch.event, self.event)
        self.assertEqual(dpch.money_account, self.bank_acc)
        self.assertEqual(dpch.regular_amount, data['userchannels'][0]['regular_amount'])
        self.assertEqual(dpch.regular_frequency, data['userchannels'][0]['regular_frequency'])


class ResetPasswordTest(TestCase):

    def test_reset_password(self):
        user = mommy.make('aklub.UserProfile', username="John_van_test")
        email = mommy.make('aklub.ProfileEmail', email="John@van.test", user=user)
        mommy.make('aklub.AdministrativeUnit', from_email_str="unit@test.test")
        url = reverse('reset_password_email')
        data = {'email': email.email}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        received_email = mail.outbox[0]
        self.assertEqual(received_email.to[0], email.email)
        self.assertEqual(received_email.subject, 'Obnovení hesla')
        # get reset link
        link = [string for string in received_email.body.split(" ") if "?u=" in string]
        link_splitted = link[0].replace("&", "=").replace("\n", "=").split("=")
        user_uid = link_splitted[3]
        token = link_splitted[5]
        # confirm reset password
        url = reverse('reset_password_email_confirm', kwargs={'uid': user_uid, "token": token})
        password = "new_strong_password96"
        data = {'password_1': password, 'password_2': password}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.check_password(password), True)
