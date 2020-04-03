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
from django.core import mail
from django.core.cache import cache
try:
    from django.urls import reverse
except ImportError:  # Django<2.0
    from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from model_mommy import mommy

from .test_admin import CreateSuperUserMixin
from .utils import print_response  # noqa
from .. import views
from ..models import AdministrativeUnit, BankAccount, DonorPaymentChannel, PetitionSignature, ProfileEmail, UserProfile


class ClearCacheMixin(object):
    def tearDown(self):
        super().tearDown()
        cache.clear()


@override_settings(
    MANAGERS=(('Manager', 'manager@test.com'),),
)
class ViewsTests(CreateSuperUserMixin, ClearCacheMixin, TestCase):
    fixtures = ['conditions', 'users', 'communications', 'dashboard_stats']

    def setUp(self):
        super().setUp()
        self.client.force_login(self.superuser)

        au = mommy.make(
            "aklub.AdministrativeUnit",
            name='test',
        )
        mommy.make(
            'aklub.BankAccount',
            administrative_unit=au,
            bank_account_number='12345/123',
            bank_account='test',
            slug='12345123',

        )

    regular_post_data = {
        'userprofile-email': 'test@test.cz',
        'userprofile-first_name': 'Testing',
        'userprofile-last_name': 'User',
        'userprofile-telephone': 111222333,
        'userincampaign-regular_frequency': 'monthly',
        'userincampaign-regular_amount': '321',
        'userincampaign-campaign': 'klub',
        'userincampaign-money_account': '12345123',
    }

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

    def test_regular_existing_email(self):
        address = reverse('regular')
        regular_post_data = self.regular_post_data.copy()
        regular_post_data['userprofile-email'] = 'test.user@email.cz'
        response = self.client.post(address, regular_post_data, follow=False)
        self.assertContains(
            response,
            '<h1>Děkujeme!</h1>',
            html=True,
        )
        self.assertEqual(len(mail.outbox), 2)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test.user@email.cz', 'kp@auto-mat.cz'])
        self.assertEqual(msg.subject, 'Resending data')
        self.assertEqual(
            msg.body,
            'Resending data to Jméno: Test Příjmení: User Ulice: Město: Praha 4 PSC:\nE-mail: test.user@email.cz Telefon:\n\n',
        )
        msg1 = mail.outbox[1]
        self.assertEqual(msg1.recipients(), ['manager@test.com'])
        self.assertEqual(msg1.subject, '[Django] Opakovaná registrace')
        self.assertEqual(
            msg1.body,
            'Repeated registration for email test.user@email.cz\n'
            'name: Testing\nsurname: User\nfrequency: monthly\ntelephone: 111222333\namount: 321',
        )

    def test_darujme_existing_email_different_campaign(self):
        """ Test, that if the user exists in different campaign, he is able to register """
        address = reverse('regular-darujme')
        foo_user = mommy.make(
            'aklub.UserProfile',
            first_name="Foo",
            last_name='Duplabar',
        )
        mommy.make(
            'aklub.ProfileEmail',
            email='test@email.cz',
            user=foo_user,
            is_primary=True,
        )
        au = mommy.make(
            'aklub.AdministrativeUnit',
            name='test',
        )
        bc = mommy.make(
            'aklub.BankAccount',
            bank_account="0000",
            administrative_unit=au,
        )
        donor_payment_channel = mommy.make(
            "aklub.DonorPaymentChannel",
            money_account=bc,
            event__id=1,
            user=foo_user,
        )
        response = self.client.post(address, self.post_data_darujme, follow=False)
        self.assertContains(
            response,
            '<h1>Děkujeme!</h1>',
            html=True,
        )
        self.assertEqual(len(mail.outbox), 2)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test@email.cz', 'kp@auto-mat.cz'])
        self.assertEqual(msg.subject, 'New user')
        self.assertEqual(
            msg.body,
            'New user has been created Jméno: Foo Příjmení: Duplabar Ulice: Město: PSC:\nE-mail: test@email.cz Telefon:\n\n',
        )
        self.assertEqual(donor_payment_channel.user.last_name, 'Duplabar')
        self.assertEqual(donor_payment_channel.user.userchannels.count(), 2)

    def test_regular_dpnk(self):
        mommy.make("Event", slug="dpnk")
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
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test@test.cz', 'kp@auto-mat.cz'])
        self.assertEqual(msg.subject, 'New user')
        self.assertEqual(
            msg.body,
            'New user has been created Jméno: Testing Příjmení: User Ulice: Město: PSC:\nE-mail: test@test.cz Telefon: 111222333\n\n',
        )

        self.assertEqual(UserProfile.objects.get(email="test@test.cz").get_full_name(), "Testing User")
        self.assertEqual(UserProfile.objects.get(email="test@test.cz").username, "test4")
        self.assertEqual(UserProfile.objects.get(email="test@test.cz").telephone_set.get().telephone, '111222333')
        new_channel = DonorPaymentChannel.objects.get(user__email="test@test.cz")
        self.assertEqual(new_channel.regular_amount, 321)
        self.assertEqual(new_channel.regular_payments, 'regular')
        self.assertEqual(new_channel.regular_frequency, 'monthly')

    def test_regular(self):
        address = reverse('regular')
        response = self.client.get(address)
        self.assertContains(
            response,
            '<input id="id_userprofile-first_name" maxlength="30" name="userprofile-first_name" type="text" required />',
            html=True,
        )
        response = self.client.post(address, self.regular_post_data, follow=True)
        self.assertContains(response, '<h1>Děkujeme!</h1>', html=True)
        email = ProfileEmail.objects.get(email="test@test.cz")
        self.assertEqual(email.user.get_full_name(), "Testing User")
        self.assertEqual(email.user.username, "test4")
        self.assertEqual(email.user.telephone_set.get().telephone, '111222333')
        new_channel = DonorPaymentChannel.objects.get(user=email.user)
        self.assertEqual(new_channel.regular_amount, 321)
        self.assertEqual(new_channel.regular_payments, 'regular')
        self.assertEqual(new_channel.event.slug, 'klub')
        self.assertEqual(new_channel.money_account.administrative_unit.name, 'test')

    post_data_darujme = {
        "recurringfrequency": "28",
        "ammount": "200",
        "payment_data____jmeno": "test_name",
        "payment_data____prijmeni": "test_surname",
        "payment_data____email": "test@email.cz",
        "payment_data____telefon": "123456789",
        "transaction_type": "2",
        "userincampaign-campaign": 'klub',
        "userincampaign-money_account": '12345123',
    }

    def test_regular_darujme(self):
        address = reverse('regular-darujme')
        response = self.client.post(address, self.post_data_darujme)
        self.assertContains(response, '<tr><th>Jméno: </th><td>test_surname test_name</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Číslo účtu: </th><td>2400063333 / 2010</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Email: </th><td>test@email.cz</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Částka: </th><td>200 Kč</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Frekvence: </th><td>Měsíčně</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Pravidelné platby: </th><td>Pravidelné platby</td></tr>', html=True)
        email = ProfileEmail.objects.get(email="test@email.cz")
        new_channel = DonorPaymentChannel.objects.get(user=email.user)
        self.assertEqual(new_channel.regular_amount, 200)
        self.assertEqual(new_channel.regular_payments, 'regular')
        self.assertEqual(new_channel.event.slug, 'klub')
        self.assertEqual(new_channel.money_account.administrative_unit.name, 'test')

    def test_regular_darujme_ajax(self):
        address = reverse('regular-darujme')
        response = self.client.post(address, self.post_data_darujme, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        payment_channel = DonorPaymentChannel.objects.get(user__email="test@email.cz")
        self.assertJSONEqual(
            response.content.decode(),
            {
                'account_number': '2400063333 / 2010',
                'variable_symbol': payment_channel.VS,
                'amount': 200,
                'email': 'test@email.cz',
                'frequency': 'monthly',
                'repeated_registration': False,
                'valid': True,
                'addressment': 'Test_Name',
            },
        )
        new_channel = DonorPaymentChannel.objects.get(user__email="test@email.cz")
        self.assertEqual(new_channel.regular_amount, 200)
        self.assertEqual(new_channel.regular_payments, 'regular')

    post_data_darujme_onetime = post_data_darujme.copy()
    post_data_darujme_onetime["recurringfrequency"] = ""

    def test_regular_darujme_onetime(self):
        address = reverse('regular-darujme')
        response = self.client.post(address, self.post_data_darujme_onetime)
        self.assertContains(response, '<tr><th>Jméno: </th><td>test_surname test_name</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Číslo účtu: </th><td>2400063333 / 2010</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Email: </th><td>test@email.cz</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Částka: </th><td>200 Kč</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Frekvence: </th><td>Jednorázově</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Pravidelné platby: </th><td>Nemá pravidelné platby</td></tr>', html=True)

    def test_regular_darujme_ajax_onetime(self):
        address = reverse('regular-darujme')
        response = self.client.post(address, self.post_data_darujme_onetime, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        payment_channel = DonorPaymentChannel.objects.get(user__email="test@email.cz")
        self.assertJSONEqual(
            response.content.decode(),
            {
                'account_number': '2400063333 / 2010',
                'variable_symbol': payment_channel.VS,
                'amount': 200,
                'email': 'test@email.cz',
                'frequency': None,
                'repeated_registration': False,
                'valid': True,
                'addressment': 'Test_Name',
            },
        )

    post_data_darujme_known_email = post_data_darujme.copy()
    post_data_darujme_known_email["payment_data____email"] = "test.user@email.cz"

    def test_regular_darujme_known_email(self):
        address = reverse('regular-darujme')
        response = self.client.post(address, self.post_data_darujme_known_email)
        self.assertContains(response, '<h1>Děkujeme!</h1>', html=True)
        self.assertContains(response, '<tr><th>Jméno: </th><td>User Test</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Číslo účtu: </th><td>2400063333 / 2010</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Variabilní symbol: </th><td>120127010</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Email: </th><td>test.user@email.cz</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Částka: </th><td>100 Kč</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Frekvence: </th><td>Měsíčně</td></tr>', html=True)
        self.assertContains(response, '<tr><th>Pravidelné platby: </th><td>Pravidelné platby</td></tr>', html=True)

        self.assertEqual(len(mail.outbox), 2)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test.user@email.cz', 'kp@auto-mat.cz'])
        self.assertEqual(msg.subject, 'Resending data')
        self.assertEqual(
            msg.body,
            'Resending data to Jméno: Test Příjmení: User Ulice: Město: Praha 4 PSC:\nE-mail: test.user@email.cz Telefon:\n\n',
        )
        msg1 = mail.outbox[1]
        self.assertEqual(msg1.recipients(), ['manager@test.com'])
        self.assertEqual(msg1.subject, '[Django] Opakovaná registrace')
        self.assertEqual(
            msg1.body,
            'Repeated registration for email test.user@email.cz\nname: test_name\n'
            'surname: test_surname\nfrequency: monthly\ntelephone: 123456789\namount: 200',
        )

    def test_regular_darujme_known_email_ajax(self):
        address = reverse('regular-darujme')
        response = self.client.post(address, self.post_data_darujme_known_email, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertJSONEqual(
            response.content.decode(),
            {
                'account_number': '2400063333 / 2010',
                'variable_symbol': '120127010',
                'amount': '200',
                'email': 'test.user@email.cz',
                'frequency': 'monthly',
                'repeated_registration': True,
                'valid': True,
                'addressment': 'Zbyněku',
            },
        )

        self.assertEqual(len(mail.outbox), 2)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test.user@email.cz', 'kp@auto-mat.cz'])
        self.assertEqual(msg.subject, 'Resending data')
        self.assertEqual(
            msg.body,
            'Resending data to Jméno: Test Příjmení: User Ulice: Město: Praha 4 PSC:\nE-mail: test.user@email.cz Telefon:\n\n',
        )
        msg1 = mail.outbox[1]
        self.assertEqual(msg1.recipients(), ['manager@test.com'])
        self.assertEqual(msg1.subject, '[Django] Opakovaná registrace')
        self.assertEqual(
            msg1.body,
            'Repeated registration for email test.user@email.cz\nname: test_name\n'
            'surname: test_surname\nfrequency: monthly\ntelephone: 123456789\namount: 200',
        )

    post_data_short_telephone = post_data_darujme.copy()
    post_data_short_telephone["payment_data____telefon"] = "12345"

    def test_regular_darujme_short_telephone(self):
        address = reverse('regular-darujme')
        response = self.client.post(address, self.post_data_short_telephone)
        self.assertContains(response, '<ul class="errorlist"><li>Tato hodnota má mít nejméně 9 znaků (nyní má 5).</li></ul>', html=True)
        self.assertContains(
            response,
            '<li><label for="id_recurringfrequency_0"><input checked="checked" id="id_recurringfrequency_0" '
            'name="recurringfrequency" type="radio" value="28" /> Měsíčně</label></li>',
            html=True,
        )
        self.assertContains(
            response,
            '<input id="id_payment_data____telefon" maxlength="30" name="payment_data____telefon" type="text" value="12345" required>',
            html=True,
        )

    def test_regular_darujme_short_telephone_ajax(self):
        address = reverse('regular-darujme')
        response = self.client.post(address, self.post_data_short_telephone, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(),
            {"payment_data____telefon": ["Tato hodnota má mít nejméně 9 znaků (nyní má 5)."]},
        )

    def test_regular_wp(self):
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

        self.assertEqual(UserProfile.objects.get(email="test@test.cz").get_full_name(), "Testing User")
        self.assertEqual(UserProfile.objects.get(email="test@test.cz").username, "test4")
        self.assertEqual(UserProfile.objects.get(email="test@test.cz").telephone_set.get().telephone, '111222333')
        new_channel = DonorPaymentChannel.objects.get(user__email="test@test.cz")
        self.assertEqual(new_channel.regular_amount, 321)
        self.assertEqual(new_channel.regular_payments, 'regular')

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
                'gdpr': ['Toto pole je třeba vyplnit.'],
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
    fixtures = ['users']

    def test_out_of_vs(self):
        au = AdministrativeUnit.objects.create(name='test')
        bank_acc = BankAccount.objects.create(bank_account_number=1111, administrative_unit=au)
        with self.assertRaises(AssertionError):
            for i in range(1, 400):
                vs = views.generate_variable_symbol(99)
                userprofile = UserProfile.objects.create(username=vs, email="test%s@test.cz" % i)
                DonorPaymentChannel.objects.create(VS=vs, event_id=1, user=userprofile, money_account=bank_acc)
