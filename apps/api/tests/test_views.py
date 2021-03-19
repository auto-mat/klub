import datetime

from aklub.models import CompanyProfile, ProfileEmail

from django.conf import settings
from django.core import mail
from django.core.files import File
from django.test import TestCase, override_settings
from django.urls import reverse

from freezegun import freeze_time

from interactions.models import Interaction

from model_mommy import mommy

from oauth2_provider.models import Application

from .utils import app_login_mixin, user_login_mixin


class GetAccessTokenTest(TestCase):
    def test_get_client_credentials_token(self):
        app = mommy.make(
             'oauth2_provider.application',
             client_type=Application.CLIENT_CONFIDENTIAL,
             authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
             skip_authorization=False,
             client_id='xxx',
             client_secret='xxx',
        )
        mommy.make(
            'oauth2_manager.ApplicationScopeSelector',
            default_scopes=" ".join(settings.OAUTH2_PROVIDER['SCOPES'].keys()),  # get all possible scopes
            application=app,
        )

        data = {
            "grant_type": "client_credentials",
            "client_id": "xxx",
            "client_secret": "xxx",
        }
        url = reverse('oauth2_provider:token')
        headers = {'content_type': 'application/json'}
        response = self.client.post(url, data=data, **headers)

        self.assertEqual(response.status_code, 200)
        tokens = app.accesstoken_set.all()
        self.assertEqual(tokens.count(), 1)

        token = tokens.first()
        resp = response.json()
        self.assertEqual(resp['access_token'], token.token)
        self.assertEqual(resp['token_type'], 'Bearer')
        self.assertEqual(resp['scope'], token.scope)
        self.assertEqual(resp['access_token'], token.token)
        delta = token.expires.replace(microsecond=0)-token.created.replace(microsecond=0)
        self.assertEqual(int(resp['expires_in']), int(delta.total_seconds()))

    def test_get_user_password_token(self):
        user = mommy.make('aklub.UserProfile', username='tester69')
        password = 'super_ultra_7853_hard'
        user.set_password(password)
        user.save()
        app = mommy.make(
             'oauth2_provider.application',
             client_type=Application.CLIENT_CONFIDENTIAL,
             authorization_grant_type=Application.GRANT_PASSWORD,
             skip_authorization=False,
             client_id='xxx',
             client_secret='xxx',
        )
        mommy.make(
            'oauth2_manager.ApplicationScopeSelector',
            default_scopes="read write",
            application=app,
        )
        data = {
           "grant_type": "password",
           "username": user.username,
           "password": password,
           "client_id": app.client_id,
           "client_secret": app.client_secret,
          }

        url = reverse('oauth2_provider:token')
        headers = {'content_type': 'application/json'}
        response = self.client.post(url, data=data, **headers)

        self.assertEqual(response.status_code, 200)
        tokens = app.accesstoken_set.all()
        self.assertEqual(tokens.count(), 1)
        token = tokens.first()

        resp = response.json()
        self.assertEqual(resp['access_token'], token.token)
        self.assertEqual(resp['token_type'], 'Bearer')
        self.assertEqual(resp['scope'], token.scope)
        self.assertEqual(resp['access_token'], token.token)
        delta = token.expires.replace(microsecond=0)-token.created.replace(microsecond=0)
        self.assertTrue(int(resp['expires_in']), int(delta.total_seconds()))

        tokens = app.refreshtoken_set.all()
        self.assertEqual(tokens.count(), 1)
        token = tokens.first()
        self.assertEqual(resp['refresh_token'], token.token)

        self.assertEqual(user, token.user)


@freeze_time("2015-5-1")
class CreateDpchUserProfileViewTest(TestCase):
    def setUp(self):
        app_login_mixin()

        unit = mommy.make('aklub.administrativeunit', name='test_unit')
        self.event = mommy.make('events.event', slug='event_slug', administrative_units=[unit, ])
        self.bank_acc = mommy.make('aklub.bankaccount', bank_account='11122/111', slug='bank_slug', administrative_unit=unit)

    def test_post_request(self):
        url = reverse('userprofile_vs')
        header = {'Authorization': 'Bearer foo'}
        # required fields
        data = {
            'email': 'Test_User@test.coM',
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
        self.unit = mommy.make('aklub.administrativeunit', name='test_unit')
        self.event = mommy.make('events.event', slug='event_slug', administrative_units=[self.unit, ])
        self.bank_acc = mommy.make('aklub.bankaccount', bank_account='11122/111', slug='bank_slug', administrative_unit=self.unit)

    def test_post_request(self):
        url = reverse('companyprofile_vs')
        header = {'Authorization': 'Bearer foo'}
        # required fields
        data = {
            'crn': '63278260',
            'name': 'company_name',
            'email': 'Company@Test.Com',
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
            'email': 'company_neW@test.com',
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

    def test_wrong_crn_log(self):
        """
        userinput "CRN" is wrong and notificaiton for staff_member is created!
        """
        admin_user = mommy.make('aklub.UserProfile', administrated_units=[self.unit, ], is_superuser=True, is_staff=True)
        url = reverse('companyprofile_vs')
        header = {'Authorization': 'Bearer foo'}
        data = {
            'crn': '1234567',
            'name': 'company_name',
            'email': 'Company@Test.Com',
            'contact_first_name': 'tester',
            'contact_last_name': 'tester_last',
            'telephone': '111222333',
            'money_account': 'bank_slug',
            'event': 'event_slug',
            'amount': '111',
            'regular': True,
        }
        response = self.client.post(url, data=data, **header)
        self.assertEqual(response.status_code, 400)
        notifications = admin_user.notifications.all()
        self.assertEqual(notifications.count(), 1)
        notif = notifications.first()
        self.assertEqual(notif.verb, 'Wrong format of crn')
        self.assertEqual(notif.description, 'User input was: 1234567 and was not create in system')


class CheckEventViewTest(TestCase):
    def setUp(self):
        app_login_mixin()

    def test_check_if_event_exist(self):
        unit = mommy.make('aklub.AdministrativeUnit', name='test_unit')
        event = mommy.make('events.event', slug='event_slug', administrative_units=[unit, ])

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
        event = mommy.make('events.event', slug='event_slug', administrative_units=[unit, ])
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


@override_settings(SUM_LAST_YEAR_PAYMENTS=3000, SUM_LAST_MONTH_PAYMENTS=100)
class CheckLastPaymentViewTest(TestCase):
    "check if user has some payment for last_year or last_month"
    def setUp(self):
        self.user = user_login_mixin()
        unit = mommy.make('aklub.AdministrativeUnit')
        bank_acc = mommy.make('aklub.BankAccount', administrative_unit=unit, bank_account_number="123")
        event = mommy.make('events.event')
        self.dpch = mommy.make("aklub.DonorPaymentChannel", money_account=bank_acc, event=event, user=self.user)

    def test_check_last_payment_success(self):
        mommy.make('aklub.payment', date=datetime.datetime.now().date(), amount=200, user_donor_payment_channel=self.dpch)
        url = reverse('check_last_payment')
        header = {'Authorization': 'Bearer foo'}
        response = self.client.get(url, **header)
        self.assertEqual(response.status_code, 200)

    def test_check_last_payment_unsuccess(self):
        url = reverse('check_last_payment')
        header = {'Authorization': 'Bearer foo'}
        response = self.client.get(url, **header)
        self.assertEqual(response.status_code, 404)


class CreateInteractionTest(TestCase):
    def setUp(self):
        app_login_mixin()

    def test_create_interaction(self):
        user = mommy.make('aklub.Profile', id=22)
        unit = mommy.make('aklub.AdministrativeUnit', name='test_unit')
        event = mommy.make('events.event', slug='event_slug', administrative_units=[unit, ])

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
        self.event = mommy.make('events.event', slug='event_slug', administrative_units=[unit, ])
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
            'email': email.email.upper(),
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
            'email': company_contact.email.upper(),
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
        self.event = mommy.make('events.event', slug='event_slug', administrative_units=[unit, ])
        self.bank_acc = mommy.make('aklub.bankaccount', bank_account='11122/111', slug='bank_slug', administrative_unit=unit)

    def test_create_payment_userprofile(self):
        url = reverse('register_userprofile')
        header = {"content_type": "application/json"}
        data = {

            'email': 'tester@gmai.coM',
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
        email = ProfileEmail.objects.get(email=data['email'].lower())
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


class EventViewTest(TestCase):
    def setUp(self):
        app_login_mixin()
        unit = mommy.make('aklub.administrativeunit', name='test_unit')
        self.organizing_association = mommy.make(
            "events.OrganizingAssociation",
            administrative_unit=unit,
            name="some_cool_ppl",
        )
        self.location = mommy.make(
            "events.location",
            administrative_unit=unit,
            name="location_name",
            place="here",
            region="Prague",
            gps="58°, 20°",

        )
        self.event = mommy.make(
            'events.event',
            name='event_name',
            slug='event_slug',
            date_from="2020-02-02",
            date_to="2021-03-03",
            program='monuments',
            indended_for='everyone',
            location=self.location,
            organizing_associations=[self.organizing_association, ],
            age_from=10,
            age_to=99,
            start_date="2020-03-01",
            participation_fee=120,
            organization_team=[],
            entry_form_url="http://www.example.com",
            web_url="http://www.example.com",
            invitation_text_1="text_1",
            invitation_text_2="text_2",
            invitation_text_3="text_3",
            invitation_text_4="text_4",
            main_photo=File(open("apps/aklub/test_data/empty_pdf.pdf", "rb")),
            administrative_units=[unit, ],
            public_on_web=True,
        )
        self.user_1 = mommy.make(
            "aklub.userprofile",
            first_name="user",
            last_name="profilovic",
        )
        self.telephone_1 = mommy.make(
            "aklub.telephone",
            telephone="655455564",
            is_primary=True,
            user=self.user_1,
        )
        self.email_1 = mommy.make(
            "aklub.profileemail",
            email="ho@ha.com",
            is_primary=True,
            user=self.user_1,
        )
        position = mommy.make("events.OrganizationPosition", name="position")
        mommy.make(
            "events.OrganizationTeam",
            position=position,
            profile=self.user_1,
            event=self.event,
            can_be_contacted=True,
        )

    def test_event_list_view(self):
        url = reverse('event')
        header = {'Authorization': 'Bearer foo'}
        response = self.client.get(url, **header)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        data = data[0]

        self.assertEqual(data['name'], self.event.name)
        self.assertEqual(data['slug'], self.event.slug)
        self.assertEqual(data['date_from'], self.event.date_from)
        self.assertEqual(data['date_to'], self.event.date_to)
        self.assertEqual(data['program'], self.event.program)
        self.assertEqual(data['indended_for'], self.event.indended_for)

        location = data['location']
        self.assertEqual(location['name'], self.location.name)
        self.assertEqual(location['place'], self.location.place)
        self.assertEqual(location['region'], self.location.region)
        self.assertEqual(location['gps'], self.location.gps)

        organizing_associations = data['organizing_associations']
        self.assertEqual(len(organizing_associations), 1)
        organizing_associations = organizing_associations[0]
        self.assertEqual(organizing_associations['name'], self.organizing_association.name)

        self.assertEqual(data['age_from'], self.event.age_from)
        self.assertEqual(data['age_to'], self.event.age_to)
        self.assertEqual(data['start_date'], self.event.start_date)
        self.assertEqual(data['participation_fee'], self.event.participation_fee)

        organization_team = data['organization_team']
        self.assertEqual(len(organization_team), 1)
        organization_team = organization_team[0]
        self.assertEqual(organization_team["first_name"], self.user_1.first_name)
        self.assertEqual(organization_team["last_name"], self.user_1.last_name)
        self.assertEqual(organization_team["email"], self.email_1.email)
        self.assertEqual(organization_team["telephone"], self.telephone_1.telephone)

        self.assertEqual(data['entry_form_url'], self.event.entry_form_url)
        self.assertEqual(data['web_url'], self.event.web_url)
        self.assertEqual(data['invitation_text_1'], self.event.invitation_text_1)
        self.assertEqual(data['invitation_text_2'], self.event.invitation_text_2)
        self.assertEqual(data['invitation_text_3'], self.event.invitation_text_3)
        self.assertEqual(data['invitation_text_4'], self.event.invitation_text_4)

        self.assertTrue(self.event.main_photo.url in data['main_photo'])
        self.assertEqual(data['additional_photo_1'], self.event.additional_photo_1)
        self.assertEqual(data['additional_photo_2'], self.event.additional_photo_2)
        self.assertEqual(data['additional_photo_3'], self.event.additional_photo_3)
        self.assertEqual(data['additional_photo_4'], self.event.additional_photo_4)
        self.assertEqual(data['additional_photo_5'], self.event.additional_photo_5)
        self.assertEqual(data['additional_photo_6'], self.event.additional_photo_6)


class ResetPasswordTest(TestCase):
    def test_reset_password(self):
        user = mommy.make('aklub.UserProfile', username="John_van_test")
        email = mommy.make('aklub.ProfileEmail', email="john@van.test", user=user)
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
