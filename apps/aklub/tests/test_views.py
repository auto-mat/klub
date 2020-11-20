# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2017 o.s. Auto*Mat
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import django
from django.conf import settings
from django.core import mail
from django.core.cache import cache
try:
    from django.urls import reverse
except ImportError:  # Django<2.0
    from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from interactions.models import PetitionSignature

from model_mommy import mommy

from .test_admin import CreateSuperUserMixin
from .utils import print_response  # noqa
from ..models import DonorPaymentChannel, ProfileEmail, UserProfile


class ClearCacheMixin(object):
    def tearDown(self):
        super().tearDown()
        cache.clear()


@override_settings(
    MANAGERS=(('Manager', 'manager@test.com'),),
)
class ViewsTests(CreateSuperUserMixin, ClearCacheMixin, TestCase):
    #fixtures = ['conditions', 'users', 'communications', 'dashboard_stats']

    def setUp(self):
        super().setUp()
        self.client.force_login(self.superuser)
        self.unit = mommy.make(
            "aklub.AdministrativeUnit",
            name='test',
            slug="test",
        )
        self.event = mommy.make(
            'aklub.event',
            administrative_units=[self.unit, ],
            slug='klub',
            enable_registration=True,
        )
        self.money = mommy.make(
            'aklub.BankAccount',
            administrative_unit=self.unit,
            bank_account_number='12345/123',
            bank_account='test',
            slug='12345123',
        )

        # check if autocom is running.
        inter_category = mommy.make('interactions.interactioncategory', category='emails')
        inter_type = mommy.make('interactions.interactiontype', category=inter_category, send_email=True)

        named_cond = mommy.make('flexible_filter_conditions.NamedCondition', name="some-random-name")
        condition = mommy.make('flexible_filter_conditions.Condition', operation="and", negate=False, named_condition=named_cond)
        self.term_cond = mommy.make(
            'flexible_filter_conditions.TerminalCondition',
            variable="action",
            operation="=",
            value="some-random-value",
            condition=condition,
        )
        mommy.make(
            "aklub.AutomaticCommunication",
            method_type=inter_type,
            condition=named_cond,
            event=self.event,
            template='Template',
            subject='It works!',
            only_once=True,
            dispatch_auto=True,
            administrative_unit=self.unit,
        )

        self.regular_post_data = {
            'userprofile-email': 'test@test.cz',
            'userprofile-first_name': 'Testing',
            'userprofile-last_name': 'User',
            'userprofile-telephone': 111222333,
            'userincampaign-regular_frequency': 'monthly',
            'userincampaign-regular_amount': '321',
            'userincampaign-event': 'klub',
            'userincampaign-money_account': '12345123',
            'userincampaign-payment_type': 'bank-transfer',
        }

        self.post_data_darujme = {
            "recurringfrequency": "28",  # mothly
            "ammount": "200",
            "payment_data____jmeno": "test_name",
            "payment_data____prijmeni": "test_surname",
            "payment_data____email": "test@email.cz",
            "payment_data____telefon": "123456789",
            "userincampaign-event": 'klub',
            "userincampaign-money_account": '12345123',
            "userincampaign-payment_type": "bank-transfer",
        }
        self.register_withotu_payment = {
            "age_group": "2010",
            "sex": "male",
            "first_name": "tester",
            "last_name": "testing",
            "telephone": "123456789",
            "email": "test@test.com",
            "street": "woah",
            "city": "memer",
            "zip_code": "987 00",
        }

    def test_regular_new_user_and_dpch(self):
        """
        regular form create new data and sent autocom new-user-bank-transfer
        """
        # autocom set up
        self.term_cond.value = 'new-user-bank-transfer'
        self.term_cond.save()

        address = reverse('regular')
        response = self.client.get(address)
        self.assertContains(
            response,
            '<input id="id_userprofile-first_name" maxlength="30" name="userprofile-first_name" type="text" required />',
            html=True,
        )

        response = self.client.post(address, self.regular_post_data, follow=True)
        self.assertContains(response, '<h1>Děkujeme!</h1>', html=True)
        # created data
        email = ProfileEmail.objects.get(email="test@test.cz")
        self.assertEqual(email.user.get_full_name(), "Testing User")
        self.assertEqual(email.user.username, "test1")
        self.assertEqual(email.user.telephone_set.get().telephone, '111222333')
        new_channel = DonorPaymentChannel.objects.get(user=email.user)
        self.assertEqual(new_channel.regular_amount, 321)
        self.assertEqual(new_channel.regular_payments, 'regular')
        self.assertEqual(new_channel.event.slug, self.event.slug)
        self.assertEqual(new_channel.money_account.slug, self.money.slug)
        # autocom send!
        self.assertEqual(len(mail.outbox), 1)

    def test_regular_existing_email_and_dpch(self):
        """
        regular form update data and sent autocom resent-data-bank-transfer
        """
        # autocom set up
        self.term_cond.value = 'resent-data-bank-transfer'
        self.term_cond.save()
        user = mommy.make('aklub.userprofile')
        mommy.make('aklub.profileemail', email='test@test.cz', user=user, is_primary=True)
        dpch = mommy.make('aklub.donorpaymentchannel', event=self.event, money_account=self.money, user=user)
        address = reverse('regular')
        response = self.client.post(address, self.regular_post_data, follow=False)
        self.assertContains(
            response,
            '<h1>Děkujeme!</h1>',
            html=True,
        )
        self.assertEqual(len(mail.outbox), 1)
        dpch.refresh_from_db()
        self.assertEqual(dpch.regular_amount, int(self.regular_post_data['userincampaign-regular_amount']))
        self.assertEqual(dpch.regular_payments, 'regular')
        self.assertEqual(dpch.event, self.event)
        self.assertEqual(dpch.money_account, self.money)

    def test_regular_darujme_new_user_and_dpch(self):
        """
        testing ajax response and saved data
        """
        self.term_cond.value = 'new-user-bank-transfer'
        self.term_cond.save()

        address = reverse('regular-darujme')
        response = self.client.post(address, self.post_data_darujme)
        self.assertContains(response, '<tr><th>Jméno: </th><td>test_surname test_name</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Číslo účtu: </th><td>12345/123</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Email: </th><td>test@email.cz</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Částka: </th><td>200 Kč</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Frekvence: </th><td>Měsíčně</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Pravidelné platby: </th><td>Pravidelné platby</td></tr>', html=True)
        email = ProfileEmail.objects.get(email="test@email.cz")
        new_channel = DonorPaymentChannel.objects.get(user=email.user)
        self.assertEqual(new_channel.regular_amount, int(self.post_data_darujme['ammount']))
        self.assertEqual(new_channel.regular_payments, 'regular')
        self.assertEqual(new_channel.event, self.event)
        self.assertEqual(new_channel.money_account, self.money)

        self.assertEqual(len(mail.outbox), 1)

    def test_regular_darujme_onetime(self):
        """
        testing ajax response in onetime
        """
        address = reverse('regular-darujme')
        post_data_darujme_onetime = self.post_data_darujme.copy()
        post_data_darujme_onetime["recurringfrequency"] = ""
        response = self.client.post(address, post_data_darujme_onetime)
        self.assertContains(response, '<tr><th>Jméno: </th><td>test_surname test_name</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Číslo účtu: </th><td>12345/123</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Email: </th><td>test@email.cz</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Částka: </th><td>200 Kč</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Frekvence: </th><td>Jednorázově</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Pravidelné platby: </th><td>Nemá pravidelné platby</td></tr>', html=True)

    def test_regular_darujme_existing_user_and_different_dpch(self):
        """
        testing ajax user has different DPCH, he is still able to register to new event """
        self.term_cond.value = 'new-user-bank-transfer'
        self.term_cond.save()

        address = reverse('regular-darujme')
        user = mommy.make('aklub.userprofile', first_name='test_name', last_name='test_surname')
        mommy.make('aklub.profileemail', email='test@email.cz', user=user, is_primary=True)
        event = mommy.make('aklub.event', administrative_units=[self.unit, ])
        mommy.make('aklub.donorpaymentchannel', event=event, money_account=self.money, user=user)

        response = self.client.post(address, self.post_data_darujme)

        self.assertContains(response, '<h1>Děkujeme!</h1>', html=True)
        self.assertContains(response, '<tr><th>Jméno: </th><td>test_surname test_name</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Číslo účtu: </th><td>12345/123</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Email: </th><td>test@email.cz</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Částka: </th><td>200 Kč</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Frekvence: </th><td>Měsíčně</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Pravidelné platby: </th><td>Pravidelné platby</td></tr>', html=True)

        self.assertEqual(user.userchannels.count(), 2)
        new_channel = user.userchannels.last()
        self.assertEqual(new_channel.regular_amount, int(self.post_data_darujme['ammount']))
        self.assertEqual(new_channel.regular_payments, 'regular')
        self.assertEqual(new_channel.event, self.event)
        self.assertEqual(new_channel.money_account, self.money)

        self.assertEqual(len(mail.outbox), 1)

    def test_regular_wp(self):
        """
        form testing data are saved new user and new dpch
        """
        address = reverse('regular-wp')
        response = self.client.get(address)
        self.assertContains(
            response,
            '<input class=" form-control" id="id_userprofile-first_name" maxlength="30" '
            'name="userprofile-first_name" type="text" required />',
            html=True,
        )

        response = self.client.post(address, self.regular_post_data, follow=True)
        self.assertContains(response, '<h1>Děkujeme!</h1>', html=True)

        email = ProfileEmail.objects.get(email="test@test.cz")
        self.assertEqual(email.user.get_full_name(), "Testing User")
        self.assertEqual(email.user.username, "test1")
        self.assertEqual(email.user.telephone_set.get().telephone, '111222333')
        new_channel = DonorPaymentChannel.objects.get(user=email.user)

        self.assertEqual(new_channel.regular_amount, 321)
        self.assertEqual(new_channel.regular_payments, 'regular')
        self.assertEqual(new_channel.event.slug, self.event.slug)
        self.assertEqual(new_channel.money_account.slug, self.money.slug)

    def test_regular_dpnk(self):
        """
        register new user => create user and donor payment channel
        """
        self.term_cond.value = 'new-user-bank-transfer'
        self.term_cond.save()

        address = "%s?firstname=Uest&surname=Tser&email=uest.tser@email.cz&telephone=1211221" % reverse('regular-dpnk')
        response = self.client.get(address)
        self.assertContains(
            response,
            '<input class=" form-control" id="id_userprofile-first_name" maxlength="30" '
            'name="userprofile-first_name" type="text" required value="Uest" />',
            html=True,
        )
        self.assertContains(
            response,
            '<input class=" form-control" id="id_userprofile-last_name" maxlength="%s" '
            'name="userprofile-last_name" type="text" required value="Tser" />' % (150 if django.VERSION >= (2, 0) else 30),
            html=True,
        )
        self.assertContains(
            response,
            '<input class=" form-control" id="id_userprofile-telephone" maxlength="30" '
            'name="userprofile-telephone" type="text" required value="1211221" />',
            html=True,
        )
        self.assertContains(
            response,
            '<input class=" form-control" id="id_userprofile-email" name="userprofile-email" type="email" '
            'required value="uest.tser@email.cz" />',
            html=True,
        )

        response = self.client.post(address, self.regular_post_data, follow=True)
        self.assertContains(response, '<h5>Děkujeme!</h5>', html=True)

        self.assertEqual(len(mail.outbox), 1)

        email = ProfileEmail.objects.get(email="test@test.cz")
        self.assertEqual(email.user.get_full_name(), "Testing User")
        self.assertEqual(email.user.username, "test1")
        self.assertEqual(email.user.telephone_set.get().telephone, '111222333')
        new_channel = DonorPaymentChannel.objects.get(user=email.user)

        self.assertEqual(new_channel.regular_amount, 321)
        self.assertEqual(new_channel.regular_payments, 'regular')
        self.assertEqual(new_channel.event.slug, self.event.slug)
        self.assertEqual(new_channel.money_account.slug, self.money.slug)

    def test_register_without_payment(self):
        """
        register => to receive new and so (dont want to pay)
        """
        address = reverse('register-withou-payment', kwargs={'unit': self.unit.slug})
        self.register_withotu_payment = {
            "age_group": "2010",
            "sex": "male",
            "first_name": "tester",
            "last_name": "testing",
            "telephone": "123456789",
            "email": "test@test.com",
            "street": "woah",
            "city": "memer",
            "zip_code": "987 00",
        }
        response = self.client.post(address, self.register_withotu_payment)
        self.assertTrue(response.status_code, 200)
        user = ProfileEmail.objects.get(email="test@test.com").user
        self.assertEqual(user.first_name, self.register_withotu_payment['first_name'])
        self.assertEqual(user.last_name, self.register_withotu_payment['last_name'])
        self.assertEqual(user.age_group, int(self.register_withotu_payment['age_group']))
        self.assertEqual(user.sex, self.register_withotu_payment['sex'])
        self.assertEqual(user.street, self.register_withotu_payment['street'])
        self.assertEqual(user.city, self.register_withotu_payment['city'])
        self.assertEqual(user.zip_code, self.register_withotu_payment['zip_code'])
        self.assertEqual(user.telephone_set.get().telephone, self.register_withotu_payment['telephone'])

        self.assertEqual(user.userchannels.count(), 0)


    def test_campaign_statistics(self):
        address = reverse('campaign-statistics', kwargs={'campaign_slug': 'klub'})
        response = self.client.get(address)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "total-income": 480,
                "expected-yearly-income": 1200,
                "number-of-regular-members": 1,
                "number-of-onetime-members": 1,
                "number-of-active-members": 2,
                "number-of-all-members": 3,
                'number-of-confirmed-members': 3,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_petition_signatures(self):
        address = reverse('petition-signatures', kwargs={'campaign_slug': 'klub'})
        response = self.client.get(address)
        self.assertJSONEqual(
            response.content.decode(),
            [
                {
                    "created": "2017-12-16T17:22:30.128Z",
                    "userprofile_first_name": "------",
                    "userprofile_last_name": "------",
                    "companyprofile_name": "------",
                },
                {
                    "created": "2016-12-16T17:22:30.128Z",
                    "userprofile_first_name": "Test",
                    "userprofile_last_name": "User",
                    "companyprofile_name": None,
                },
                {
                    "created": "2015-12-16T17:22:30.128Z",
                    "userprofile_first_name": "------",
                    "userprofile_last_name": "------",
                    "companyprofile_name": "------",
                },
            ],
        )
        self.assertEqual(response.status_code, 200)

    def test_main_admin_page(self):
        address = "/"
        response = self.client.get(address)
        self.assertContains(response, "Nestará registrace: 3 položek")
        self.assertContains(
            response,
            '<div class="dashboard-module-content"> <p>Celkový počet položek: 2</p><ul class="stacked">'
            '<li class="odd"><a href="/aklub/donorpaymentchannel/3/change/">Payments Without</a></li>'
            '<li class="even"><a href="/aklub/donorpaymentchannel/2978/change/">User Test</a></li>'
            '</ul> </div>',
            html=True,
        )

    def test_aklub_admin_page(self):
        address = "/aklub/"
        response = self.client.get(address)
        self.assertContains(response, "<h2>Poslední akce</h2>", html=True)

    def test_stat_members(self):
        address = reverse('stat-members')
        response = self.client.get(address)
        self.assertContains(response, "<tr><td>2016</td><td>Zář</td><td>2</td><td>2</td><td>4</td><td>4</td></tr>", html=True)
        self.assertContains(response, "<h1>Statistiky členů klubu</h1>", html=True)

    def test_stat_payments(self):
        address = reverse('stat-payments')
        response = self.client.get(address)
        self.assertContains(response, "<tr><td>2016</td><td>Bře</td><td>1</td><td>100 Kč</td><td>610 Kč</td></tr>", html=True)
        self.assertContains(response, "<h1>Statistiky plateb</h1>", html=True)

    def test_donators(self):
        address = reverse('donators')
        response = self.client.get(address)
        self.assertContains(
            response,
            '<p>Celkem již podpořilo činnost Auto*Matu 2 lidí<br/>Z toho 1 přispívá na jeho činnost pravidelně</p>',
            html=True,
        )
        self.assertContains(
            response,
            '<ul><li>Test&nbsp;User</li><li>Test&nbsp;User 1</li></ul>',
            html=True,
        )

    def test_profiles(self):
        address = reverse('profiles')
        response = self.client.get(address)
        self.assertJSONEqual(
            response.content.decode(),
            [
                {"firstname": "Test", "text": "", "picture": "", "surname": "User 1", "picture_thumbnail": ""},
                {"firstname": "Test", "text": "", "picture": "", "surname": "User", "picture_thumbnail": ""},
                {"firstname": "Without", "text": "", "picture": "", "surname": "Payments", "picture_thumbnail": ""},
                {"firstname": "Without", "text": "", "picture": "", "surname": "Payments", "picture_thumbnail": ""},
            ],
        )








    def test_sign_petition_no_gdpr_consent(self):
        address = reverse('petition')
        post_data = {
            'userprofile-email': 'test@email.cz',
            "userincampaign-campaign": "klub",
            "userincampaign-money_account": '12345123',
            "gdpr": False,
        }
        response = self.client.post(address, post_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertJSONEqual(
            response.content.decode(),
            {
                'gdpr': ['Toto pole je vyžadováno.'],
            },
        )

    def test_sign_petition_ajax_only_required(self):
        address = reverse('petition')
        post_data = {
            'userprofile-email': 'test@email.cz',
            "userincampaign-campaign": "klub",
            "userincampaign-money_account": '12345123',
            "gdpr": True,
        }
        response = self.client.post(address, post_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        payment_channel = DonorPaymentChannel.objects.get(user__email="test@email.cz")
        self.assertJSONEqual(
            response.content.decode(),
            {
                'account_number': '2400063333 / 2010',
                'variable_symbol': payment_channel.VS,
                'amount': None,
                'email': 'test@email.cz',
                'frequency': None,
                'repeated_registration': False,
                'valid': True,
                'addressment': 'příteli/kyně Auto*Matu',
            },
        )
        new_user = DonorPaymentChannel.objects.get(user__email="test@email.cz")
        self.assertEqual(new_user.regular_amount, None)
        self.assertEqual(new_user.regular_payments, '')
        self.assertTrue(PetitionSignature.objects.get(user__email="test@email.cz").gdpr_consent)

    def test_sign_petition_ajax_some_fields(self):
        address = reverse('petition')
        post_data = {
            'userprofile-email': 'test@email.cz',
            'userprofile-first_name': 'Testing',
            'userprofile-last_name': 'User',
            'userprofile-telephone': 111222333,
            "userincampaign-campaign": "klub",
            "userincampaign-money_account": '12345123',
            "gdpr": True,
        }
        response = self.client.post(address, post_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        payment_channel = DonorPaymentChannel.objects.get(user__email="test@email.cz")
        self.assertJSONEqual(
            response.content.decode(),
            {
                'account_number': '2400063333 / 2010',
                'variable_symbol': payment_channel.VS,
                'amount': None,
                'email': 'test@email.cz',
                'frequency': None,
                'repeated_registration': False,
                'valid': True,
                'addressment': 'Testingu',
            },
        )
        new_user = DonorPaymentChannel.objects.get(user__email="test@email.cz")
        self.assertEqual(new_user.regular_amount, None)
        self.assertEqual(new_user.regular_payments, '')
        self.assertTrue(PetitionSignature.objects.get(user__email="test@email.cz").gdpr_consent)

    def test_sign_petition_ajax_all(self):
        address = reverse('petition')
        post_data = {
            'userprofile-email': 'test@email.cz',
            'userprofile-first_name': 'Testing',
            'userprofile-last_name': 'User',
            'userprofile-telephone': 111222333,
            'userprofile-age_group': 1986,
            'userprofile-sex': 'male',
            'userprofile-city': 'Some city',
            'userprofile-street': 'Some street',
            'userprofile-country': 'Some country',
            'userprofile-zip_code': 11333,
            "userincampaign-campaign": "klub",
            "userincampaign-money_account": '12345123',
            "gdpr": True,
        }
        response = self.client.post(address, post_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        payment_channel = DonorPaymentChannel.objects.get(user__email="test@email.cz")
        self.assertJSONEqual(
            response.content.decode(),
            {
                'account_number': '2400063333 / 2010',
                'variable_symbol': payment_channel.VS,
                'amount': None,
                'email': 'test@email.cz',
                'frequency': None,
                'repeated_registration': False,
                'valid': True,
                'addressment': 'Testingu',
            },
        )
        new_user = DonorPaymentChannel.objects.get(user__email="test@email.cz")
        self.assertEqual(new_user.regular_amount, None)
        self.assertEqual(new_user.regular_payments, '')
        self.assertEqual(new_user.event.slug, 'klub')
        self.assertEqual(new_user.money_account.slug, '12345123')
        self.assertTrue(PetitionSignature.objects.get(user__email="test@email.cz").gdpr_consent)


class VariableSymbolTests(TestCase):
    # TODO ... add test if there is no more VS available for event
    def setUp(self):
        self.au = mommy.make(
            "aklub.administrativeunit",
            name='test_unit',
        )
        self.bank_account = mommy.make(
            'aklub.BankAccount',
            bank_account_number='111111/1111',
            administrative_unit=self.au,
        )

    def test_vs_generate_without_prefix(self):
        event = mommy.make(
            "aklub.event",
            administrative_units=[self.au, ],
        )

        dpch = mommy.make(
            'aklub.donorpaymentchannel',
            money_account=self.bank_account,
            event=event,
        )
        event2 = mommy.make(
            "aklub.event",
            administrative_units=[self.au, ],
        )
        dpch2 = mommy.make(
            'aklub.donorpaymentchannel',
            money_account=self.bank_account,
            event=event2,
        )
        # fist dpch without prefix
        self.assertEqual(dpch.VS, "0000000001")
        self.assertEqual(dpch2.VS, "0000000002")

    def test_vs_generate_witprefix(self):
        event = mommy.make(
            "aklub.event",
            administrative_units=[self.au, ],
            variable_symbol_prefix='12345',
        )

        dpch1_1 = mommy.make(
            'aklub.donorpaymentchannel',
            money_account=self.bank_account,
            event=event,
        )
        dpch1_2 = mommy.make(
            'aklub.donorpaymentchannel',
            money_account=self.bank_account,
            event=event,
        )
        event2 = mommy.make(
            "aklub.event",
            administrative_units=[self.au, ],
            variable_symbol_prefix='54321',
        )
        dpch2_1 = mommy.make(
            'aklub.donorpaymentchannel',
            money_account=self.bank_account,
            event=event2,
        )
        dpch2_2 = mommy.make(
            'aklub.donorpaymentchannel',
            money_account=self.bank_account,
            event=event2,
        )
        # dpch with prefix
        self.assertEqual(dpch1_1.VS, "1234500001")
        self.assertEqual(dpch1_2.VS, "1234500002")

        self.assertEqual(dpch2_1.VS, "5432100001")
        self.assertEqual(dpch2_2.VS, "5432100002")


class ResetPasswordTest(TestCase):
    def setUp(self):
        au = mommy.make('aklub.administrativeunit', name='au_1')
        self.user = mommy.make('aklub.userprofile', username='username_1', administrative_units=[au, ])
        mommy.make('aklub.profileemail', user=self.user, email='username_1@auto-mat.com', is_primary=True)

    def test_reset_password(self):
        url = reverse("password_reset")
        data = {'email': self.user.get_email_str()}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(mail.outbox[0].to[0], self.user.get_email_str())
        self.assertEqual(mail.outbox[0].subject, "password reset")
        # parse reset url
        reset_url = [te for te in mail.outbox[0].body.split(' ') if '/reset/' in te][0].replace('\n', '').replace(settings.WEB_URL, '')
        new_pw = 'super_hard_pw123_DSD'
        # page is firstly redirected
        self.client.get(reset_url, follow=True)
        # then fill up redirected url
        split_url = reset_url.split('/')
        split_url[-2] = "set-password"
        new_url = "/".join(split_url)
        data = {'new_password1': new_pw, 'new_password2': new_pw}
        response = self.client.post(new_url, data)
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.check_password(new_pw), True)
