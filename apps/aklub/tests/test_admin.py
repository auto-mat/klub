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
from django.contrib import admin as django_admin
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from django_admin_smoke_tests import tests

from freezegun import freeze_time

from model_mommy import mommy

from .. import admin
from ..models import (
    AccountStatements, AutomaticCommunication, Communication, MassCommunication,
    TaxConfirmation, UserInCampaign, UserProfile, UserYearPayments,
)


class AdminTest(tests.AdminSiteSmokeTest):
    fixtures = ['conditions', 'users']

    def post_request(self, post_data={}, params=None):
        request = self.factory.post('/', data=post_data)
        request.user = self.superuser
        request._dont_enforce_csrf_checks = True
        request.session = 'session'
        request._messages = FallbackStorage(request)
        return request

    def test_send_mass_communication(self):
        model_admin = django_admin.site._registry[UserInCampaign]
        request = self.post_request({})
        queryset = UserInCampaign.objects.all()
        response = admin.send_mass_communication(model_admin, request, queryset)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/aklub/masscommunication/add/?send_to_users=3%2C4%2C2978%2C2979")

    def test_send_mass_communication_userprofile(self):
        model_admin = django_admin.site._registry[UserInCampaign]
        request = self.post_request({})
        queryset = UserProfile.objects.all()
        response = admin.send_mass_communication_distinct(model_admin, request, queryset)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/aklub/masscommunication/add/?send_to_users=3%2C2978%2C2979")

    @freeze_time("2017-5-1")
    def test_tax_confirmation_generate(self):
        model_admin = django_admin.site._registry[TaxConfirmation]
        request = self.post_request({})
        response = model_admin.generate(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/aklub/taxconfirmation/")
        self.assertEqual(TaxConfirmation.objects.get(user_profile__id=2978, year=2016).amount, 350)
        confirmation_values = TaxConfirmation.objects.filter(year=2016).values('user_profile', 'amount', 'year').order_by('user_profile')
        expected_confirmation_values = [
            {'year': 2016, 'user_profile': 2978, 'amount': 350},
            {'year': 2016, 'user_profile': 2979, 'amount': 130},
        ]
        self.assertListEqual(list(confirmation_values), expected_confirmation_values)
        self.assertEqual(request._messages._queued_messages[0].message, 'Generated 2 tax confirmations')

    def test_useryearpayments(self):
        model_admin = django_admin.site._registry[UserYearPayments]
        request = self.get_request({
            "drf__payment__date__gte": "01.07.2010",
            "drf__payment__date__lte": "10.10.2016",
        })
        response = model_admin.changelist_view(request)
        self.assertContains(response, '<td class="field-payment_total_by_year">350</td>', html=True)

    @freeze_time("2015-5-1")
    def test_account_statement_changelist_post(self):
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
            self.assertEqual(response.status_code, 302)
            obj = AccountStatements.objects.get(date_from="2010-10-01")
            self.assertEqual(response.url, "/admin/aklub/accountstatements/")
            self.assertEqual(obj.payment_set.count(), 6)

            self.assertEqual(request._messages._queued_messages[0].message, 'Skipped payments: Testing User 1 (test.user1@email.cz)')
            self.assertEqual(
                request._messages._queued_messages[1].message,
                'Položka typu Výpis z účtu "<a href="/admin/aklub/accountstatements/%(id)s/change/">%(id)s (2015-05-01 00:00:00)</a>"'
                ' byla úspěšně přidána.' % {'id': obj.id},
            )

    @freeze_time("2015-5-1")
    def test_account_statement_changelist_post_bank_statement(self):
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
            self.assertEqual(response.status_code, 302)
            obj = AccountStatements.objects.get(date_from="2016-01-25")
            self.assertEqual(response.url, "/admin/aklub/accountstatements/")
            self.assertEqual(obj.payment_set.count(), 4)

            self.assertEqual(
                request._messages._queued_messages[0].message,
                'Payments without user: Testing user 1 (Bezhotovostní příjem), '
                'KRE DAN (KRE DAN), '
                'without variable symbol (without variable symbol)',
            )
            self.assertEqual(
                request._messages._queued_messages[1].message,
                'Položka typu Výpis z účtu "<a href="/admin/aklub/accountstatements/%(id)s/change/">%(id)s (2015-05-01 00:00:00)</a>"'
                ' byla úspěšně přidána.' % {'id': obj.id},
            )

    def test_mass_communication_changelist_post_send_mails(self):
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
        self.assertEqual(response.url, "/admin/aklub/masscommunication/%s/change/" % obj.id)
        self.assertEqual(
            request._messages._queued_messages[1].message,
            'Emaily odeslány na následující adresy: without_payments@email.cz, test.user@email.cz',
        )
        self.assertEqual(
            request._messages._queued_messages[0].message,
            'Odeslání na následující adresy nebylo možné kvůli problémům: test.user1@email.cz',
        )
        self.assertEqual(
            request._messages._queued_messages[2].message,
            'Položka typu Hromadná komunikace "<a href="/admin/aklub/masscommunication/%s/change/">test communication</a>"'
            ' byla úspěšně přidána. Níže ji můžete dále upravovat.' % obj.id,
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
        self.assertEqual(response.url, "/admin/aklub/masscommunication/%s/change/" % obj.id)

    def test_automatic_communication_changelist_post(self):
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
        self.assertEqual(response.url, "/admin/aklub/automaticcommunication/%s/change/" % obj.id)

    def test_communication_changelist_post(self):
        model_admin = django_admin.site._registry[Communication]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        post_data = {
            '_save': 'test_mail',
            "user": "2978",
            "date_0": "2015-03-1",
            "date_1": "12:43",
            "method": "email",
            "subject": "Subject 123",
            "summary": "Test template",
        }
        request = self.post_request(post_data=post_data)
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 302)
        obj = Communication.objects.get(subject="Subject 123")
        self.assertEqual(obj.summary, "Test template")
        self.assertEqual(response.url, "/admin/aklub/communication/")

    def test_user_in_campaign_changelist_post(self):
        model_admin = django_admin.site._registry[UserInCampaign]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        post_data = {
            '_continue': 'Save',
            'userprofile': 2978,
            'variable_symbol': 1234,
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
        userincampaign = UserInCampaign.objects.get(variable_symbol=1234)
        self.assertEqual(response.url, "/admin/aklub/userincampaign/%s/change/" % userincampaign.id)

        self.assertEqual(userincampaign.activity_points, 13)
        self.assertEqual(userincampaign.verified_by.username, 'testuser')


class AdminImportExportTests(TestCase):
    fixtures = ['conditions', 'users', 'communications']

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_superuser(
            username='admin',
            email='test_user@test_user.com',
            password='admin',
        )
        self.client.force_login(self.user)

    def test_userattendance_export(self):
        address = "/admin/aklub/userincampaign/export/"
        post_data = {
            'file_format': 0,
        }
        response = self.client.post(address, post_data)
        self.assertContains(
            response,
            ',Test,User,,male,,test.user@email.cz,,Praha 4,,120127010,0,regular,monthly,2015-12-16 18:22:30,'
            '"Domníváte se, že má město po zprovoznění tunelu Blanka omezit tranzit historickým centrem? '
            'Ano, hned se zprovozněním tunelu",editor,1,cs',
        )


class TestUserForm(TestCase):
    """ Tests for UserForm """

    def test_clean_email(self):
        form = admin.UserForm()
        form.cleaned_data = {'email': 'foo@email.com'}
        self.assertEquals(form.clean_email(), 'foo@email.com')

    def test_clean_email_not_unique(self):
        mommy.make("auth.User", email="foo@email.com")
        form = admin.UserForm()
        form.cleaned_data = {'email': 'foo@email.com'}
        with self.assertRaises(django.forms.ValidationError):
            form.clean_email()
