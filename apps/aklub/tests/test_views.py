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

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.core.urlresolvers import reverse

from django.test import TestCase

from django.test.utils import override_settings

from model_mommy.recipe import Recipe, seq

from .. import views
from ..models import UserInCampaign, UserProfile


userincampaign_recipe = Recipe(
    "aklub.UserInCampaign",
    campaign__name="Foo campaign",
    userprofile__user__is_active=True,
    variable_symbol=seq(1),
)


class ClearCacheMixin(object):
    def tearDown(self):
        super().tearDown()
        cache.clear()


@override_settings(
    MANAGERS=(('Manager', 'manager@test.com'),),
)
class ViewsTests(ClearCacheMixin, TestCase):
    fixtures = ['conditions', 'users', 'communications', 'dashboard_stats']

    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin',
            email='test_user@test_user.com',
            password='admin',
        )
        self.client.force_login(self.user)

    regular_post_data = {
        'user-email': 'test@test.cz',
        'user-first_name': 'Testing',
        'user-last_name': 'User',
        'userprofile-telephone': 111222333,
        'userincampaign-regular_frequency': 'monthly',
        'userincampaign-regular_amount': '321',
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
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_main_admin_page(self):
        address = "/"
        response = self.client.get(address)
        self.assertContains(response, "Nestará registrace: 4 položek")
        self.assertContains(
            response,
            '<div class="dashboard-module-content"> <p>Celkový počet položek: 2</p><ul class="stacked">'
            '<li class="odd"><a href="/admin/aklub/userincampaign/3/change/">Payments Without</a></li>'
            '<li class="even"><a href="/admin/aklub/userincampaign/2978/change/">User Test</a></li>'
            '</ul> </div>',
            html=True,
        )

    def test_aklub_admin_page(self):
        address = "/admin/aklub/"
        response = self.client.get(address)
        self.assertContains(response, "<h2>Nedávné akce</h2>", html=True)

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

    def test_change_dashboard_chart(self):
        address = "/"
        post_data = {
            'select_box_payment_amount': 'regular',
        }
        response = self.client.post(address, post_data)
        self.assertContains(
            response,
            '<option value="regular" selected=selected>Pravidelní</option>',
            html=True,
        )

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
        regular_post_data['user-email'] = 'test.user@email.cz'
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

    def test_regular_dpnk(self):
        address = "%s?firstname=Uest&surname=Tser&email=uest.tser@email.cz&telephone=1211221" % reverse('regular-dpnk')
        response = self.client.get(address)
        self.assertContains(
            response,
            '<input class=" form-control" id="id_user-first_name" maxlength="30" '
            'name="user-first_name" type="text" required value="Uest" />',
            html=True,
        )
        self.assertContains(
            response,
            '<input class=" form-control" id="id_user-last_name" maxlength="30" '
            'name="user-last_name" type="text" required value="Tser" />',
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
            '<input class=" form-control" id="id_user-email" name="user-email" type="email" '
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

        self.assertEqual(User.objects.get(email="test@test.cz").get_full_name(), "Testing User")
        self.assertEqual(User.objects.get(email="test@test.cz").username, "test4")
        self.assertEqual(UserProfile.objects.get(user__email="test@test.cz").telephone, '111222333')
        self.assertEqual(UserInCampaign.objects.get(userprofile__user__email="test@test.cz").regular_amount, 321)

    def test_regular(self):
        address = reverse('regular')
        response = self.client.get(address)
        self.assertContains(
            response,
            '<input id="id_user-first_name" maxlength="30" name="user-first_name" type="text" required />',
            html=True,
        )

        response = self.client.post(address, self.regular_post_data, follow=True)
        self.assertContains(response, '<h1>Děkujeme!</h1>', html=True)

        self.assertEqual(User.objects.get(email="test@test.cz").get_full_name(), "Testing User")
        self.assertEqual(User.objects.get(email="test@test.cz").username, "test4")
        self.assertEqual(UserProfile.objects.get(user__email="test@test.cz").telephone, '111222333')
        self.assertEqual(UserInCampaign.objects.get(userprofile__user__email="test@test.cz").regular_amount, 321)

    post_data_darujme = {
        "recurringfrequency": "28",
        "ammount": "200",
        "payment_data____jmeno": "test_name",
        "payment_data____prijmeni": "test_surname",
        "payment_data____email": "test@email.cz",
        "payment_data____telefon": "123456789",
        "transaction_type": "2",
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

    def test_regular_darujme_ajax(self):
        address = reverse('regular-darujme')
        response = self.client.post(address, self.post_data_darujme, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        userincampaign = UserInCampaign.objects.get(userprofile__user__email="test@email.cz")
        self.assertJSONEqual(
            response.content.decode(),
            {
                'account_number': '2400063333 / 2010',
                'variable_symbol': userincampaign.variable_symbol,
                'amount': 200,
                'email': 'test@email.cz',
                'frequency': 'monthly',
                'repeated_registration': False,
                'valid': True,
            },
        )

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
        userincampaign = UserInCampaign.objects.get(userprofile__user__email="test@email.cz")
        self.assertJSONEqual(
            response.content.decode(),
            {
                'account_number': '2400063333 / 2010',
                'variable_symbol': userincampaign.variable_symbol,
                'amount': 200,
                'email': 'test@email.cz',
                'frequency': None,
                'repeated_registration': False,
                'valid': True,
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
            '<input class=" form-control" id="id_user-first_name" maxlength="30" name="user-first_name" type="text" required />',
            html=True,
        )

        response = self.client.post(address, self.regular_post_data, follow=True)
        self.assertContains(response, '<h1>Děkujeme!</h1>', html=True)

        self.assertEqual(User.objects.get(email="test@test.cz").get_full_name(), "Testing User")
        self.assertEqual(User.objects.get(email="test@test.cz").username, "test4")
        self.assertEqual(UserProfile.objects.get(user__email="test@test.cz").telephone, '111222333')
        self.assertEqual(UserInCampaign.objects.get(userprofile__user__email="test@test.cz").regular_amount, 321)

    def test_onetime(self):
        address = reverse('onetime')
        response = self.client.get(address)
        self.assertContains(response, '<input id="id_0-first_name" maxlength="40" name="0-first_name" type="text" required />', html=True)

        post_data = {
            'one_time_payment_wizard-current_step': 0,
            '0-email': 'test@test.cz',
            '0-first_name': 'Testing',
            '0-last_name': 'User',
            '0-amount': '321',
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(
            response,
            '<input id="id_userprofile__1-title_before" maxlength="15" name="userprofile__1-title_before" type="text" />',
            html=True,
        )

        post_data = {
            'one_time_payment_wizard-current_step': 1,
            'userincampaign__1-note': 'Note',
            'user__1-first_name': 'Testing',
            'user__1-last_name': 'User',
            'user__1-email': 'test@test.cz',
            'userprofile__1-title_before': 'Tit.',
            'userprofile__1-title_after': '',
            'userprofile__1-street': 'On Street 1',
            'userprofile__1-city': 'City',
            'userprofile__1-country': 'Country',
            'userprofile__1-zip_code': '100 00',
            'userprofile__1-language': 'cs',
            'userprofile__1-telephone': '+420123456789',
            'userprofile__1-wished_tax_confirmation': 'on',
            'userprofile__1-wished_information': 'on',
            'userprofile__1-public': 'on',
            'userprofile__1-note': 'asdf',
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(response, '<h1>Děkujeme!</h1>', html=True)

        self.assertEqual(User.objects.get(email="test@test.cz").get_full_name(), "Testing User")
        self.assertEqual(User.objects.get(email="test@test.cz").username, "test4")
        self.assertEqual(UserProfile.objects.get(user__email="test@test.cz").telephone, '+420123456789')
        self.assertEqual(UserInCampaign.objects.get(userprofile__user__email="test@test.cz").note, 'Note')

    def test_onetime_existing_email(self):
        address = reverse('onetime')
        response = self.client.get(address)
        self.assertContains(response, '<input id="id_0-first_name" maxlength="40" name="0-first_name" type="text" required />', html=True)

        post_data = {
            'one_time_payment_wizard-current_step': 0,
            '0-email': 'test.user@email.cz',
            '0-first_name': 'Testing',
            '0-last_name': 'User',
            '0-amount': '321',
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(response, '<option value="2978">Test User &lt;t***r@e***.cz&gt;</option>', html=True)

        post_data = {
            'one_time_payment_wizard-current_step': 2,
            '2-uid': 2978,
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(response, '<input id="id_4-vs_check" maxlength="40" name="4-vs_check" type="text" />', html=True)

        post_data = {
            'one_time_payment_wizard-current_step': 4,
            '4-vs_check': 120127010,
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(response, '<h1>Děkujeme!</h1>', html=True)


class VariableSymbolTests(TestCase):
    fixtures = ['users']

    def test_out_of_vs(self):
        with self.assertRaises(AssertionError):
            for i in range(1, 400):
                vs = views.generate_variable_symbol()
                user = User.objects.create(username=vs)
                userprofile = UserProfile.objects.create(user=user)
                UserInCampaign.objects.create(variable_symbol=vs, campaign_id=1, userprofile=userprofile)


class TestOneTimePaymentWizard(TestCase):
    def test_find_matching_users(self):
        """ Test that OneTimePaymentWizard._find_matching_users() works correctly """
        userincampaign_recipe.make(
            userprofile__user__email="foo@email.com",
        )
        userincampaign_recipe.make(
            userprofile__user__first_name="Foo",
            userprofile__user__last_name="User",
        )

        users = views.OneTimePaymentWizard._find_matching_users(None, "foo@email.com", "Foo", "User")
        expected_users = ['<UserInCampaign:   - foo@email.com (Foo campaign)>', '<UserInCampaign: User Foo -  (Foo campaign)>']
        self.assertQuerysetEqual(users, expected_users)
