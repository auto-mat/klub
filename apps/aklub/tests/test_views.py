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

from interactions.models import PetitionSignature

from model_mommy import mommy

from sesame import utils as sesame_utils

from .test_admin import CreateSuperUserMixin
from .utils import print_response  # noqa
from ..models import DonorPaymentChannel, ProfileEmail


class ClearCacheMixin(object):
    def tearDown(self):
        super().tearDown()
        cache.clear()


class ViewsTests(CreateSuperUserMixin, ClearCacheMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.superuser)
        self.unit = mommy.make(
            "aklub.AdministrativeUnit",
            name='test',
            slug="test",
        )
        self.event = mommy.make(
            'events.event',
            administrative_units=[self.unit, ],
            slug='klub',
            enable_registration=True,
            enable_signing_petitions=True,
            allow_statistics=True,
            real_yield=500,
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
        self.register_without_payment = {
            "userprofile-age_group": "2010",
            "userprofile-sex": "male",
            "userprofile-first_name": "tester",
            "userprofile-last_name": "testing",
            "userprofile-telephone": "123456789",
            "userprofile-email": "test@test.com",
            "userprofile-street": "woah",
            "userprofile-city": "memer",
            "userprofile-zip_code": "987 00",
        }
        self.sign_petition = {
            "userprofile-age_group": 2010,
            "userprofile-sex": "male",
            "userprofile-first_name": "test_first",
            "userprofile-last_name": "test_last",
            "userprofile-email": "testeros@test.com",
            "userprofile-telephone": "123456789",
            "userprofile-street": "test 5005",
            "userprofile-city": "test 5005",
            "userprofile-zip_code": "155 00",
            "petitionsignature-event": "klub",
            "petitionsignature-public": True,
            "gdpr": True,
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
        testing ajax response and saved data sent autocom new-user-bank-transfer
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
        testing ajax user has different DPCH, he is still able to register to new event, sent autocom new-user-bank-transfer
        """
        self.term_cond.value = 'new-user-bank-transfer'
        self.term_cond.save()

        address = reverse('regular-darujme')
        user = mommy.make('aklub.userprofile', first_name='test_name', last_name='test_surname')
        mommy.make('aklub.profileemail', email='test@email.cz', user=user, is_primary=True)
        event = mommy.make('events.event', administrative_units=[self.unit, ])
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
        register new user => create user and donor payment channel send autocom new-user-bank-transfer
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
        register => to receive new and so (dont want to pay) autocom sent action new-user
        """
        self.term_cond.value = 'new-user'
        self.term_cond.save()

        address = reverse('register-withou-payment', kwargs={'unit': self.unit.slug})
        response = self.client.post(address, self.register_without_payment)
        self.assertTrue(response.status_code, 200)
        user = ProfileEmail.objects.get(email="test@test.com").user
        self.assertEqual(user.first_name, self.register_without_payment['userprofile-first_name'])
        self.assertEqual(user.last_name, self.register_without_payment['userprofile-last_name'])
        self.assertEqual(user.age_group, int(self.register_without_payment['userprofile-age_group']))
        self.assertEqual(user.sex, self.register_without_payment['userprofile-sex'])
        self.assertEqual(user.street, self.register_without_payment['userprofile-street'])
        self.assertEqual(user.city, self.register_without_payment['userprofile-city'])
        self.assertEqual(user.zip_code, self.register_without_payment['userprofile-zip_code'])
        self.assertEqual(user.telephone_set.get().telephone, self.register_without_payment['userprofile-telephone'])

        self.assertEqual(user.userchannels.count(), 0)

        self.assertEqual(len(mail.outbox), 1)

    def test_sign_petition(self):
        """
        signature success => create user and signature autocom sent 'user-signature'
        """
        self.term_cond.value = 'user-signature'
        self.term_cond.save()

        address = reverse('petition')
        response = self.client.post(address, self.sign_petition, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'Podpis petice')

        user = ProfileEmail.objects.get(email=self.sign_petition['userprofile-email']).user
        self.assertEqual(user.age_group, self.sign_petition['userprofile-age_group'])
        self.assertEqual(user.sex, self.sign_petition['userprofile-sex'])
        self.assertEqual(user.first_name, self.sign_petition['userprofile-first_name'])
        self.assertEqual(user.last_name, self.sign_petition['userprofile-last_name'])
        self.assertEqual(user.street, self.sign_petition['userprofile-street'])
        self.assertEqual(user.city, self.sign_petition['userprofile-city'])
        self.assertEqual(user.zip_code, self.sign_petition['userprofile-zip_code'])

        self.assertEqual(user.telephone_set.first().telephone, self.sign_petition['userprofile-telephone'])

        signature = user.petitionsignature_set.first()

        self.assertEqual(signature.event, self.event)
        self.assertEqual(signature.administrative_unit, self.unit)
        self.assertEqual(signature.email_confirmed, False)
        self.assertEqual(signature.gdpr_consent, self.sign_petition['gdpr'])
        self.assertEqual(signature.public, self.sign_petition['petitionsignature-public'])

        self.assertEqual(len(mail.outbox), 1)

    def test_sign_petition_repeatly(self):
        """
        signature success => create user and signature autocom sent 'user-signature'
        """
        self.term_cond.value = 'user-signature-again'
        self.term_cond.save()

        user = mommy.make("aklub.UserProfile")
        mommy.make("aklub.ProfileEmail", email=self.sign_petition['userprofile-email'], user=user, is_primary=True)
        mommy.make("interactions.PetitionSignature", administrative_unit=self.unit, user=user, event=self.event)
        address = reverse('petition')
        response = self.client.post(address, self.sign_petition, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'Podpis petice')

        self.assertEqual(len(mail.outbox), 1)

    def test_sign_petition_no_gdpr_consent(self):
        """
        petition form is filled, but gdpr is not clicked autocom is not sent
        """
        self.term_cond.value = 'user-signature'
        self.term_cond.save()

        address = reverse('petition')
        post_data = self.sign_petition.copy()
        post_data['gdpr'] = False

        response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<div class="fieldWrapper">'
            '<img src="http://www.auto-mat.cz/wp-content/themes/atm/img/odrazka.gif" />'
            '<strong><label for="id_gdpr">GDPR souhlas:</label><br/></strong>'
            '<ul class="errorlist"><li>Toto pole je vyžadováno.</li></ul>'
            '<input type="checkbox" name="gdpr" required id="id_gdpr"></div>',
            html=True,
        )

        self.assertEqual(len(mail.outbox), 0)

    def test_sign_petition_confirmation(self):
        """
        confirmation petition signature
        """
        user = mommy.make("aklub.UserProfile")
        mommy.make("aklub.ProfileEmail", email=self.sign_petition['userprofile-email'], user=user, is_primary=True)
        signature = mommy.make("interactions.PetitionSignature", administrative_unit=self.unit, user=user, event=self.event)

        address = reverse('sing-petition-confirm', kwargs={'campaign_slug': 'klub'})
        url_hax = sesame_utils.get_query_string(user)
        address += url_hax

        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'Podpis potvrzen')

        signature.refresh_from_db()
        self.assertTrue(signature.email_confirmed)

    def test_petition_signatures_list(self):
        """
        list of all signatures
        """
        for i in range(0, 3):
            user = mommy.make('aklub.userprofile', first_name='first_' + str(i), last_name='last_' + str(i))
            mommy.make(
                "interactions.PetitionSignature",
                administrative_unit=self.unit,
                user=user,
                event=self.event,
                public=True,
                email_confirmed=True,
            )

        address = reverse('petition-signatures', kwargs={'campaign_slug': self.event.slug})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)

        signatures = PetitionSignature.objects.order_by('-created')
        # response is already ordered by -create
        sig_json = response.json()
        from django.utils.dateparse import parse_datetime
        for i in range(0, signatures.count()):
            self.assertEqual(sig_json[i]['user__userprofile__first_name'], signatures[i].user.first_name)
            self.assertEqual(sig_json[i]['user__userprofile__last_name'], signatures[i].user.last_name)
            self.assertEqual(parse_datetime(sig_json[i]['created']).replace(microsecond=0), signatures[i].created.replace(microsecond=0))

    def test_send_mailing_list_unsubscribe(self):
        """
        unsubscribe to mailing list in preference
        """
        self.term_cond.value = 'user-mailing-unsubscribe'
        self.term_cond.save()

        user = mommy.make("aklub.UserProfile")
        mommy.make("aklub.ProfileEmail", email='harry@test.com', user=user, is_primary=True)
        preference = mommy.make("aklub.Preference", user=user, administrative_unit=self.unit)

        address = reverse('send-mailing-list', kwargs={'unit': self.unit.slug, 'unsubscribe': 'unsubscribe'})
        url_hax = sesame_utils.get_query_string(user)
        address += url_hax

        response = self.client.get(address, follow=True)
        self.assertEqual(response.status_code, 200)

        preference.refresh_from_db()
        self.assertFalse(preference.send_mailing_lists)

        self.assertEqual(len(mail.outbox), 1)

    def test_send_mailing_list_subscribe(self):
        """
        subscribe back to mailing list in preference
        """
        self.term_cond.value = 'user-mailing-subscribe'
        self.term_cond.save()

        user = mommy.make("aklub.UserProfile")
        mommy.make("aklub.ProfileEmail", email='harry@test.com', user=user, is_primary=True)
        preference = mommy.make("aklub.Preference", user=user, administrative_unit=self.unit, send_mailing_lists=False)

        address = reverse('send-mailing-list', kwargs={'unit': self.unit.slug, 'unsubscribe': 'subscribe'})
        url_hax = sesame_utils.get_query_string(user)
        address += url_hax

        response = self.client.get(address, follow=True)
        self.assertEqual(response.status_code, 200)

        preference.refresh_from_db()
        self.assertTrue(preference.send_mailing_lists)

        self.assertEqual(len(mail.outbox), 1)

    def test_event_statistics(self):
        """
        some event statistics
        """
        for i in range(0, 3):
            user = mommy.make("aklub.UserProfile")
            dpch = mommy.make(
                'aklub.donorpaymentchannel',
                money_account=self.money,
                event=self.event,
                user=user,
                regular_payments='regular',
                regular_amount=300,
                regular_frequency='monthly',
                )
            mommy.make('aklub.payment', recipient_account=self.money, amount=250, user_donor_payment_channel=dpch)

        address = reverse('campaign-statistics', kwargs={'campaign_slug': self.event.slug})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        response = response.json()

        self.assertEqual(response["total-income"], self.event.real_yield)
        self.assertEqual(response["expected-yearly-income"], 10800)
        self.assertEqual(response["number-of-regular-members"], 3)
        self.assertEqual(response["number-of-onetime-members"], 0)
        self.assertEqual(response["number-of-active-members"], 3)
        self.assertEqual(response["number-of-all-members"], 3)
        self.assertEqual(response["number-of-confirmed-members"], 0)

    def test_donators(self):
        """
        count users who donating for selected administrative units total/regular
        """
        for i in range(0, 3):
            user = mommy.make("aklub.UserProfile")
            mommy.make("aklub.preference", user=user, administrative_unit=self.unit)
            dpch = mommy.make(
                'aklub.donorpaymentchannel',
                money_account=self.money,
                event=self.event,
                user=user,
                regular_payments='regular',
                regular_amount=300,
                regular_frequency='monthly',
                )
            mommy.make('aklub.payment', recipient_account=self.money, amount=250, user_donor_payment_channel=dpch)
        dpch.regular_payments = 'onetime'
        dpch.save()  # editing last one to onetime

        address = reverse('donators', kwargs={'unit': self.unit.slug})
        response = self.client.get(address)

        self.assertContains(
            response,
            '<p>Celkem již podpořilo činnost Auto*Matu 3 lidí<br/>Z toho 2 přispívá na jeho činnost pravidelně</p>',
            html=True,
        )


class AdminViewTests(CreateSuperUserMixin, ClearCacheMixin, TestCase):
    fixtures = ['conditions', 'users', 'communications', 'dashboard_stats']

    def setUp(self):
        super().setUp()
        self.client.force_login(self.superuser)

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
            "events.event",
            administrative_units=[self.au, ],
        )

        dpch = mommy.make(
            'aklub.donorpaymentchannel',
            money_account=self.bank_account,
            event=event,
        )
        event2 = mommy.make(
            "events.event",
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
            "events.event",
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
            "events.event",
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
