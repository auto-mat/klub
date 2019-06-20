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
from django.contrib import admin as django_admin, auth
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings

from django_admin_smoke_tests import tests

from freezegun import freeze_time

from model_mommy import mommy

from .recipes import donor_payment_channel_recipe
from .utils import RunCommitHooksMixin
from .utils import print_response  # noqa
from .. import admin
from ..models import (
    AccountStatements, AutomaticCommunication, DonorPaymentChannel, Interaction, MassCommunication,
    TaxConfirmation, UserProfile, UserYearPayments,
)


class AdminSmokeTest(tests.AdminSiteSmokeTest):
    fixtures = ['conditions', 'users']
    exclude_apps = ['helpdesk', 'postoffice']

    def post_request(self, post_data={}, params=None):
        request = self.factory.post('/', data=post_data)
        request.user = self.superuser
        request._dont_enforce_csrf_checks = True
        request.session = 'session'
        request._messages = FallbackStorage(request)
        return request


@override_settings(
    CELERY_ALWAYS_EAGER=True,
)
class AdminTest(RunCommitHooksMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.superuser = auth.get_user_model().objects.create_superuser(
            'testuser',
            'testuser@example.com',
            'foo',
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

    def test_send_mass_communication(self):
        donor_payment_channel_recipe.make(id=3)
        donor_payment_channel_recipe.make(id=4)
        donor_payment_channel_recipe.make(id=2978)
        donor_payment_channel_recipe.make(id=2979)
        model_admin = django_admin.site._registry[DonorPaymentChannel]
        request = self.post_request({})
        queryset = DonorPaymentChannel.objects.all()
        response = admin.send_mass_communication_action(model_admin, request, queryset)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/aklub/masscommunication/add/?send_to_users=3%2C4%2C2978%2C2979")

    def test_send_mass_communication_userprofile(self):
        """
        Test, that sending mass communication works for UserProfileAdmin.
        Communication shoul be send only once for every userprofile.
        """
        mutual_userprofile = mommy.make("aklub.Userprofile")
        donor_payment_channel_recipe.make(id=3, user=mutual_userprofile)
        donor_payment_channel_recipe.make(id=4, user=mutual_userprofile)
        donor_payment_channel_recipe.make(id=2978)
        donor_payment_channel_recipe.make(id=2979)
        model_admin = django_admin.site._registry[DonorPaymentChannel]
        request = self.post_request({})
        queryset = UserProfile.objects.all()
        response = admin.send_mass_communication_distinct_action(model_admin, request, queryset)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/aklub/masscommunication/add/?send_to_users=3%2C2978%2C2979")

    @freeze_time("2017-5-1")
    def test_tax_confirmation_generate(self):
        foo_user = donor_payment_channel_recipe.make(user__first_name="Foo", user__id=2978)
        bar_user = donor_payment_channel_recipe.make(user__first_name="Bar", user__id=2979)
        mommy.make("aklub.Payment", amount=350, date="2016-01-02", user_donor_payment_channel=foo_user, type="cash")
        mommy.make("aklub.Payment", amount=130, date="2016-01-02", user_donor_payment_channel=bar_user, type="cash")
        model_admin = django_admin.site._registry[TaxConfirmation]
        request = self.post_request({})
        response = model_admin.generate(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/aklub/taxconfirmation/")
        self.assertEqual(TaxConfirmation.objects.get(user_profile__id=2978, year=2016).amount, 350)
        confirmation_values = TaxConfirmation.objects.filter(year=2016).values('user_profile', 'amount', 'year').order_by('user_profile')
        expected_confirmation_values = [
            {'year': 2016, 'user_profile': 2978, 'amount': 350},
            {'year': 2016, 'user_profile': 2979, 'amount': 130},
        ]
        self.assertListEqual(list(confirmation_values), expected_confirmation_values)

    def test_useryearpayments(self):
        """
        Test, that the resulting amount in selected period matches
        """
        donor_payment_channel_recipe.make(
            payment_set=[
                mommy.make("aklub.Payment", date="2016-2-9", amount=150),
                mommy.make("aklub.Payment", date="2016-1-9", amount=100),
                mommy.make("aklub.Payment", date="2012-1-9", amount=100),
                mommy.make("aklub.Payment", date="2016-12-9", amount=100),  # Payment outside of selected period
            ],
        )
        model_admin = django_admin.site._registry[UserYearPayments]
        request = self.get_request({
            "drf__payment__date__gte": "01.07.2010",
            "drf__payment__date__lte": "10.10.2016",
        })
        response = model_admin.changelist_view(request)
        self.assertContains(response, '<td class="field-payment_total_by_year">350</td>', html=True)

    @freeze_time("2015-5-1")
    def test_account_statement_changelist_post(self):
        mommy.make("aklub.Event", darujme_name="Klub přátel Auto*Matu")
        mommy.make("aklub.Payment", SS=22258, type="darujme", operation_id="13954", date="2016-02-09")
        donor_payment_channel_recipe.make(id=2979, userprofile__email="bar@email.com", userprofile__language="cs")
        model_admin = django_admin.site._registry[AccountStatements]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        with open("apps/aklub/test_data/test_darujme.xls", "rb") as f:
            post_data = {
                '_save': 'Save',
                "type": "darujme",
                "date_from": "2010-10-01",
                "csv_file": f,
                'payment_set-TOTAL_FORMS': 0,
                'payment_set-INITIAL_FORMS': 0,
            }
            request = self.post_request(post_data=post_data)
            response = model_admin.add_view(request)
            self.run_commit_hooks()
            self.assertEqual(response.status_code, 302)
            obj = AccountStatements.objects.get(date_from="2010-10-01")
            self.assertEqual(response.url, "/aklub/accountstatements/")
            self.assertEqual(obj.payment_set.count(), 6)

            # self.assertEqual(request._messages._queued_messages[0].message, 'Skipped payments: Testing User 1 (test.user1@email.cz)')
            self.assertEqual(
                request._messages._queued_messages[0].message,
                'Položka typu Výpis z účtu "<a href="/aklub/accountstatements/%(id)s/change/">%(id)s (2015-05-01 00:00:00+00:00)</a>"'
                ' byla úspěšně přidána.' % {'id': obj.id},
            )

    @freeze_time("2015-5-1")
    def test_account_statement_changelist_post_bank_statement(self):
        donor_payment_channel_recipe.make(VS=120127010)
        model_admin = django_admin.site._registry[AccountStatements]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        with open("apps/aklub/test_data/Pohyby_5_2016.csv", "rb") as f:
            post_data = {
                '_save': 'Save',
                "type": "account",
                "csv_file": f,
                'payment_set-TOTAL_FORMS': 0,
                'payment_set-INITIAL_FORMS': 0,
            }
            request = self.post_request(post_data=post_data)
            response = model_admin.add_view(request)
            self.run_commit_hooks()
            self.assertEqual(response.status_code, 302)
            obj = AccountStatements.objects.get(date_from="2016-01-25")
            self.assertEqual(response.url, "/aklub/accountstatements/")
            self.assertEqual(obj.payment_set.count(), 4)

            # self.assertEqual(
            #     request._messages._queued_messages[0].message,
            #     'Payments without user: Testing user 1 (Bezhotovostní příjem), '
            #     'KRE DAN (KRE DAN), '
            #     'without variable symbol (without variable symbol)',
            # )
            self.assertEqual(
                request._messages._queued_messages[0].message,
                'Položka typu Výpis z účtu "<a href="/aklub/accountstatements/%(id)s/change/">%(id)s (2015-05-01 00:00:00+00:00)</a>"'
                ' byla úspěšně přidána.' % {'id': obj.id},
            )

    def test_mass_communication_changelist_post_send_mails(self):
        mommy.make("UserProfile", id=2978, email="foo@email.com", language="cs")
        mommy.make("UserProfile", id=2979, email="bar@email.com", language="cs")
        mommy.make("UserProfile", id=3, email="baz@email.com", language="en")
        model_admin = django_admin.site._registry[MassCommunication]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        post_data = {
            '_continue': 'send_mails',
            'name': 'test communication',
            "method": "email",
            'date': "2010-03-03",
            "subject": "Subject",
            "send_to_users": [2978, 2979, 3],
            "template": "Test template",
        }
        request = self.post_request(post_data=post_data)
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 302)
        obj = MassCommunication.objects.get(name="test communication")
        self.assertEqual(obj.subject, "Subject")
        self.assertEqual(response.url, "/aklub/masscommunication/%s/change/" % obj.id)
        self.assertEqual(
            request._messages._queued_messages[0].message,
            "Communication sending was queued for 3 users",
        )
        if django.VERSION < (2, 1):
            edit_text = 'Níže ji můžete dále upravovat.'
        else:
            edit_text = 'Níže můžete údaje znovu upravovat.'
        self.assertEqual(
            request._messages._queued_messages[1].message,
            'Položka typu Hromadná komunikace "<a href="/aklub/masscommunication/%s/change/">test communication</a>"'
            ' byla úspěšně přidána. %s' % (obj.id, edit_text),
        )

    def test_mass_communication_changelist_post(self):
        model_admin = django_admin.site._registry[MassCommunication]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        attachment = SimpleUploadedFile("attachment.txt", b"attachment", content_type="text/plain")
        post_data = {
            '_continue': 'test_mail',
            'name': 'test communication',
            "method": "email",
            'date': "2010-03-03",
            "subject": "Subject",
            "attach_tax_confirmation": False,
            "attachment": attachment,
            "template": "Test template",
        }
        request = self.post_request(post_data=post_data)
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 302)
        obj = MassCommunication.objects.get(name="test communication")
        self.assertEqual(obj.subject, "Subject")
        self.assertEqual(response.url, "/aklub/masscommunication/%s/change/" % obj.id)

    def test_automatic_communication_changelist_post(self):
        mommy.make("aklub.Condition", id=1)
        model_admin = django_admin.site._registry[AutomaticCommunication]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        post_data = {
            '_continue': 'test_mail',
            'name': 'test communication',
            'condition': 1,
            "method": "email",
            "subject": "Subject",
            "template": "Test template",
        }
        request = self.post_request(post_data=post_data)
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 302)
        obj = AutomaticCommunication.objects.get(name="test communication")
        self.assertEqual(obj.subject, "Subject")
        self.assertEqual(response.url, "/aklub/automaticcommunication/%s/change/" % obj.id)

    def test_communication_changelist_post(self):
        user_profile = mommy.make('UserProfile')
        model_admin = django_admin.site._registry[Interaction]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        post_data = {
            '_save': 'test_mail',
            "user": user_profile.id,
            "date_0": "2015-03-1",
            "date_1": "12:43",
            "method": "email",
            "subject": "Subject 123",
            "summary": "Test template",
        }
        request = self.post_request(post_data=post_data)
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 302)
        obj = Interaction.objects.get()
        self.assertEqual(obj.subject, "Subject 123")
        self.assertEqual(obj.summary, "Test template")
        self.assertEqual(response.url, "/aklub/interaction/")

    def test_user_in_campaign_changelist_post(self):
        mommy.make("aklub.Event", id=1)
        mommy.make("aklub.Userprofile", id=2978)
        model_admin = django_admin.site._registry[DonorPaymentChannel]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        post_data = {
            '_continue': 'Save',
            'user': 2978,
            'VS': 1234,
            'activity_points': 13,
            'registered_support_0': "2010-03-03",
            'registered_support_1': "12:35",
            'regular_payments': 'promise',
            'campaign': '1',
            'verified': 1,
            'communications-TOTAL_FORMS': 1,
            'communications-INITIAL_FORMS': 0,
            'payment_set-TOTAL_FORMS': 0,
            'payment_set-INITIAL_FORMS': 0,
            "communications-0-method": "phonecall",
            "communications-0-subject": "Subject 1",
            "communications-0-summary": "Text 1",
            "communications-0-date_0": "2010-01-01",
            "communications-0-date_1": "11:11",
        }
        request = self.post_request(post_data=post_data)
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 302)
        donorpaymentchannel = DonorPaymentChannel.objects.get(VS=1234)
        self.assertEqual(response.url, "/aklub/donorpaymentchannel/%s/change/" % donorpaymentchannel.id)

        # self.assertEqual(donorpaymentchannel.activity_points, 13)
        # self.assertEqual(donorpaymentchannel.verified_by.username, 'testuser')

    def test_pair_variable_symbols(self):
        """ Test pair_variable_symbols action """
        payment_channel = donor_payment_channel_recipe.make(VS=123)
        payment = mommy.make("aklub.Payment", VS=123)
        account_statement = mommy.make(
            "aklub.AccountStatements",
            payment_set=[payment],
        )
        request = self.post_request()
        admin.pair_variable_symbols(None, request, [account_statement])
        payment.refresh_from_db()
        self.assertEqual(payment.user_donor_payment_channel, payment_channel)
        self.assertEqual('Variabilní symboly úspěšně spárovány.', request._messages._queued_messages[0].message)


class AdminImportExportTests(TestCase):
    fixtures = ['conditions', 'users', 'communications']

    def setUp(self):
        super().setUp()
        self.user = UserProfile.objects.create_superuser(
            username='admin',
            email='test_user@test_user.com',
            password='admin',
        )
        self.client.force_login(self.user)

    def test_paymetnchannel_export(self):
        address = "/aklub/donorpaymentchannel/export/"
        post_data = {
            'file_format': 0,
        }
        response = self.client.post(address, post_data)
        self.assertContains(
            response,
            '2978,2,2978,,Test,User,,male,test.user@email.cz,,Praha 4,,120127010,0,regular,monthly,2015-12-16 17:22:30,1,cs,,,,100,'
            # TODO: check transforming following data into another models
            # ',Test,User,,male,,test.user@email.cz,,Praha 4,,120127010,0,1,regular,monthly,2015-12-16 17:22:30,'
            # '"Domníváte se, že má město po zprovoznění tunelu Blanka omezit tranzit historickým centrem? '
            # 'Ano, hned se zprovozněním tunelu",editor,1,cs,,,,0,0.0,100',
        )
