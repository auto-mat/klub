# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2015 o.s. Auto*Mat
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
from django.db.models import Q
from django.test import TestCase
from django.core import mail
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User as DjangoUser
from django.core.management import call_command
import datetime
from freezegun import freeze_time
from .models import TerminalCondition, Condition, UserInCampaign, Communication, AutomaticCommunication, AccountStatements, Payment
from django_admin_smoke_tests import tests
from .confirmation import makepdf
from . import autocom, mailing, admin
import io
from PyPDF2 import PdfFileReader
from django.core.files import File


class BaseTestCase(TestCase):
    def assertQuerysetEquals(self, qs1, qs2):
        def pk(o):
            return o.pk
        return self.assertEqual(
            list(sorted(qs1, key=pk)),
            list(sorted(qs2, key=pk))
        )

    def assertQueryEquals(self, q1, q2):
        return self.assertEqual(
            q1.__str__(),
            q2.__str__()
        )


@freeze_time("2010-1-1")
class ConditionsTests(BaseTestCase):
    """ Test conditions infrastructure and conditions in fixtures """
    maxDiff = None

    def test_date_condition(self):
        c = Condition.objects.create(operation="and")
        TerminalCondition.objects.create(
            variable="UserInCampaign.date_condition",
            value="datetime.2010-09-24 00:00",
            operation=">",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(date_condition__gt=datetime.datetime(2010, 9, 24, 0, 0)))
        self.assertQueryEquals(c.condition_string(), "None(UserInCampaign.date_condition > datetime.2010-09-24 00:00)")

    def test_boolean_condition(self):
        c = Condition.objects.create(operation="or")
        TerminalCondition.objects.create(
            variable="UserInCampaign.boolean_condition",
            value="true",
            operation="=",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(boolean_condition=True))
        self.assertQueryEquals(c.condition_string(), "None(UserInCampaign.boolean_condition = true)")

    def test_time_condition(self):
        c = Condition.objects.create(operation="or")
        TerminalCondition.objects.create(
            variable="UserInCampaign.time_condition",
            value="month_ago",
            operation="<",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(time_condition__lt=datetime.datetime(2009, 12, 2, 0, 0)))
        self.assertQueryEquals(c.condition_string(), "None(UserInCampaign.time_condition < month_ago)")

    def test_text_condition(self):
        c = Condition.objects.create(operation="or")
        TerminalCondition.objects.create(
            variable="UserInCampaign.text_condition",
            value="asdf",
            operation="contains",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(text_condition__contains="asdf"))
        self.assertQueryEquals(c.condition_string(), "None(UserInCampaign.text_condition contains asdf)")

    def test_text_icontains_condition(self):
        c = Condition.objects.create(operation="or")
        TerminalCondition.objects.create(
            variable="UserInCampaign.text_condition",
            value="asdf",
            operation="icontains",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(text_condition__icontains="asdf"))
        self.assertQueryEquals(c.condition_string(), "None(UserInCampaign.text_condition icontains asdf)")

    def test_action_condition_equals(self):
        c = Condition.objects.create(operation="or")
        TerminalCondition.objects.create(
            variable="action",
            value="asdf",
            operation="=",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(action="asdf"), Q())

    def test_action_condition_not_equals(self):
        c = Condition.objects.create(operation="or")
        TerminalCondition.objects.create(
            variable="action",
            value="asdf",
            operation="=",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(pk__in=[]))
        self.assertQueryEquals(c.condition_string(), "None(action = asdf)")

    def test_blank_condition(self):
        c = Condition.objects.create(operation="and")
        TerminalCondition.objects.create(
            variable="UserInCampaign.regular_payments",
            value="true",
            operation="=",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(regular_payments=True))
        self.assertQueryEquals(c.condition_string(), "None(UserInCampaign.regular_payments = true)")

    def test_combined_condition(self):
        c = Condition.objects.create(operation="and")
        TerminalCondition.objects.create(
            variable="UserInCampaign.time_condition",
            value="timedelta.5",
            operation=">=",
            condition=c,
        )
        TerminalCondition.objects.create(
            variable="UserInCampaign.days_ago_condition",
            value="days_ago.6",
            operation="!=",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), ~Q(days_ago_condition=datetime.datetime(2009, 12, 26, 0, 0)) & Q(time_condition__gte=datetime.timedelta(5)))
        self.assertQueryEquals(c.condition_string(), "None(UserInCampaign.days_ago_condition != days_ago.6 and UserInCampaign.time_condition >= timedelta.5)")

    def test_multiple_combined_conditions(self):
        c1 = Condition.objects.create(operation="and")
        c2 = Condition.objects.create(operation="nor")
        c2.conds.add(c1)
        TerminalCondition.objects.create(
            variable="UserInCampaign.time_condition",
            value="timedelta.5",
            operation=">=",
            condition=c1,
        )
        TerminalCondition.objects.create(
            variable="UserInCampaign.days_ago_condition",
            value="days_ago.6",
            operation="!=",
            condition=c1,
        )
        TerminalCondition.objects.create(
            variable="UserInCampaign.int_condition",
            value="5",
            operation="<=",
            condition=c2,
        )
        TerminalCondition.objects.create(
            variable="UserInCampaign.int_condition",
            value="4",
            operation="=",
            condition=c2,
        )
        test_query = ~((~Q(days_ago_condition=datetime.datetime(2009, 12, 26, 0, 0)) & Q(time_condition__gte=datetime.timedelta(5))) | Q(int_condition=4) | Q(int_condition__lte=5))
        self.assertQueryEquals(c2.get_query(), test_query)
        self.assertQueryEquals(
            c2.condition_string(),
            "not(None(None(UserInCampaign.days_ago_condition != days_ago.6 and UserInCampaign.time_condition >= timedelta.5) "
            "or UserInCampaign.int_condition = 4 or UserInCampaign.int_condition <= 5))"
        )


class ConfirmationTest(TestCase):
    def test_makepdf(self):
        output = io.BytesIO()
        makepdf(output, 'Test name', 'male', 'Test street', 'Test city', 2099, 999)
        pdf = PdfFileReader(output)
        pdf_string = pdf.pages[0].extractText()
        self.assertTrue('Test name' in pdf_string)
        self.assertTrue('Test street' in pdf_string)
        self.assertTrue('Test city' in pdf_string)
        self.assertTrue('2099' in pdf_string)
        self.assertTrue('999' in pdf_string)

    def test_makepdf_female(self):
        output = io.BytesIO()
        makepdf(output, 'Test name', 'female', 'Test street', 'Test city', 2099, 999)
        pdf = PdfFileReader(output)
        pdf_string = pdf.pages[0].extractText()
        self.assertTrue('Test name' in pdf_string)
        self.assertTrue('Test street' in pdf_string)
        self.assertTrue('Test city' in pdf_string)
        self.assertTrue('2099' in pdf_string)
        self.assertTrue('999' in pdf_string)


class AutocomTest(TestCase):
    def setUp(self):
        self.user = UserInCampaign.objects.create(sex='male')
        c = Condition.objects.create(operation="nor")
        TerminalCondition.objects.create(
            variable="action",
            value="test-autocomm",
            operation="==",
            condition=c,
        )
        AutomaticCommunication.objects.create(
            condition=c,
            template="Vazen{y|a} {pane|pani} $addressment $regular_frequency testovací šablona",
            template_en="Dear {sir|miss} $addressment $regular_frequency test template",
            subject="Testovací komunikace",
            subject_en="Testing communication",
        )

    def test_autocom(self):
        autocom.check(action="test-autocomm")
        communication = Communication.objects.get(user=self.user)
        self.assertTrue("testovací šablona" in communication.summary)
        self.assertTrue("člene Klubu přátel Auto*Matu" in communication.summary)
        self.assertTrue("Vazeny pane" in communication.summary)

    def test_autocom_female(self):
        self.user.sex = 'female'
        self.user.save()
        autocom.check(action="test-autocomm")
        communication = Communication.objects.get(user=self.user)
        self.assertIn("testovací šablona", communication.summary)
        self.assertIn("členko Klubu přátel Auto*Matu", communication.summary)
        self.assertIn("Vazena pani", communication.summary)

    def test_autocom_unknown(self):
        self.user.sex = 'unknown'
        self.user.save()
        autocom.check(action="test-autocomm")
        communication = Communication.objects.get(user=self.user)
        self.assertIn("testovací šablona", communication.summary)
        self.assertIn("člene/členko Klubu přátel Auto*Matu", communication.summary)
        self.assertIn("Vazeny/a pane/pani", communication.summary)

    def test_autocom_addressment(self):
        self.user.sex = 'male'
        self.user.addressment = 'own addressment'
        self.user.save()
        autocom.check(action="test-autocomm")
        communication = Communication.objects.get(user=self.user)
        self.assertIn("testovací šablona", communication.summary)
        self.assertIn("own addressment", communication.summary)
        self.assertIn("Vazeny pane", communication.summary)

    def test_autocom_en(self):
        self.user.sex = 'unknown'
        self.user.language = 'en'
        self.user.save()
        autocom.check(action="test-autocomm")
        communication = Communication.objects.get(user=self.user)
        self.assertIn("test template", communication.summary)
        self.assertIn("member of the Auto*Mat friends club", communication.summary)
        self.assertIn("Dear sir", communication.summary)


class MailingTest(TestCase):
    def test_mailing(self):
        sending_user = DjangoUser.objects.create(
            first_name="Testing",
            last_name="UserInCampaign",
            email="test@test.com",
        )
        c = AutomaticCommunication.objects.create(
            condition=Condition.objects.create(),
            template="Testing template",
            subject="Testing email",
            method="email",
        )
        mailing.send_mass_communication(c, ["fake_user"], sending_user, save=False)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test@test.com'])
        self.assertEqual(msg.subject, 'Testing email')
        self.assertIn("Testing template", msg.body)


class AdminTest(tests.AdminSiteSmokeTest):
    fixtures = ['conditions', 'users']


class ViewsTestsLogon(TestCase):
    fixtures = ['conditions', 'users']

    def setUp(self):
        self.user = DjangoUser.objects.create_superuser(
            username='admin', email='test_user@test_user.com', password='admin')
        self.assertTrue(self.client.login(username='admin', password='admin'))

    def verify_views(self, views, status_code_map):
        for view in views:
            status_code = status_code_map[view] if view in status_code_map else 200
            address = view
            response = self.client.get(address, follow=True)
            filename = view.replace("/", "_")
            if response.status_code != status_code:
                with open("error_%s.html" % filename, "w") as f:
                    f.write(response.content.decode())
            self.assertEqual(response.status_code, status_code, "%s view failed, the failed page is saved to error_%s.html file." % (view, filename))

    views = [
        '/admin',
        reverse('regular'),
        reverse('regular-wp'),
        reverse('regular-dpnk'),
        reverse('onetime'),
        reverse('donators'),
        reverse('profiles'),
        # reverse('stay-members'),
        # reverse('stay-payments'),
    ]

    def test_aklub_views(self):
        """
        test if the user pages work
        """
        status_code_map = {
        }

        self.verify_views(self.views, status_code_map)


class ModelTests(TestCase):
    fixtures = ['conditions', 'users']

    def setUp(self):
        call_command('denorm_init')
        self.u = UserInCampaign.objects.get(pk=2979)
        self.u1 = UserInCampaign.objects.get(pk=2978)
        self.p = Payment.objects.get(pk=1)
        self.p1 = Payment.objects.get(pk=2)
        self.p1.BIC = 101
        self.p1.save()
        call_command('denorm_flush')
        self.u1 = UserInCampaign.objects.get(pk=2978)
        self.tax_confirmation = self.u1.make_tax_confirmation(2016)

    def test_payment_model(self):
        self.assertEquals(self.p.person_name(), 'User Test')

    @freeze_time("2016-5-1")
    def test_user_model(self):
        self.assertEquals(self.u.is_direct_dialogue(), False)
        self.assertEquals(self.u.last_payment_date(), None)
        self.assertEquals(self.u.last_payment_type(), None)
        self.assertEquals(self.u.requires_action(), False)
        self.assertEquals(self.u.expected_regular_payment_date, None)
        self.assertEquals(self.u.regular_payments_delay(), False)
        self.assertEquals(self.u.extra_payments(), '<img src="/media/admin/img/icon-no.svg" alt="False" />')
        self.assertEquals(self.u.no_upgrade, False)
        self.assertEquals(self.u.monthly_regular_amount(), 0)

        self.assertEquals(self.u1.is_direct_dialogue(), False)
        self.assertEquals(self.u1.person_name(), 'User Test')
        self.assertEquals(self.u1.requires_action(), True)
        self.assertListEqual(list(self.u1.payments()), [self.p1, self.p])
        self.assertEquals(self.u1.number_of_payments, 2)
        self.assertEquals(self.u1.last_payment, self.p1)
        self.assertEquals(self.u1.last_payment_date(), datetime.date(2016, 3, 9))
        self.assertEquals(self.u1.last_payment_type(), 'bank-transfer')
        self.assertEquals(self.u1.regular_frequency_td(), datetime.timedelta(31))
        self.assertEquals(self.u1.expected_regular_payment_date, datetime.date(2016, 4, 9))
        self.assertEquals(self.u1.regular_payments_delay(), datetime.timedelta(12))
        self.assertEquals(self.u1.extra_money, 150)
        self.assertEquals(self.u1.regular_payments_info(), datetime.date(2016, 4, 9))
        self.assertEquals(self.u1.extra_payments(), 150)
        self.assertEquals(self.u1.mail_communications_count(), False)
        self.assertEquals(self.u1.payment_total, 250.0)
        self.assertEquals(self.u1.total_contrib_string(), "250&nbsp;Kč")
        self.assertEquals(self.u1.registered_support_date(), "16. 12. 2015")
        self.assertEquals(self.u1.payment_total_range(datetime.date(2016, 1, 1), datetime.date(2016, 2, 1)), 0)
        self.assertEquals(self.tax_confirmation.year, 2016)
        self.assertTrue("PDF-1.4" in str(self.tax_confirmation.file.read()))
        self.assertEquals(self.tax_confirmation.amount, 250)
        self.assertEquals(self.u1.no_upgrade, False)
        self.assertEquals(self.u1.monthly_regular_amount(), 100)


class AccountStatementTests(TestCase):
    fixtures = ['conditions', 'users']

    def test_bank_new_statement(self):
        with open("apps/aklub/test_data/Pohyby_5_2016.csv", "rb") as f:
            a = AccountStatements(csv_file=File(f), type="account")
            a.clean()
            a.save()

        a1 = AccountStatements.objects.get()
        self.assertEqual(len(a1.payment_set.all()), 3)
        self.assertEqual(a1.date_from, datetime.date(day=25, month=1, year=2016))
        self.assertEqual(a1.date_to, datetime.date(day=31, month=1, year=2016))
        user = UserInCampaign.objects.get(pk=2978)

        p1 = Payment.objects.get(account=2150508001)
        self.assertEqual(p1.date, datetime.date(day=18, month=1, year=2016))
        self.assertEqual(p1.amount, 250)
        self.assertEqual(p1.account, '2150508001')
        self.assertEqual(p1.bank_code, '5500')
        self.assertEqual(p1.VS, '120127010')
        self.assertEqual(p1.SS, "12321")
        self.assertEqual(p1.KS, '0101')
        self.assertEqual(p1.user_identification, 'Account note')
        self.assertEqual(p1.type, 'bank-transfer')
        self.assertEqual(p1.done_by, "Done by")
        self.assertEqual(p1.account_name, "Testing user account")
        self.assertEqual(p1.bank_name, "Raiffeisenbank a.s.")
        self.assertEqual(p1.transfer_note, "Testing user note")
        self.assertEqual(p1.currency, "CZK")
        self.assertEqual(p1.recipient_message, "Message for recepient")
        self.assertEqual(p1.operation_id, "12366")
        self.assertEqual(p1.transfer_type, "Bezhotovostní příjem")
        self.assertEqual(p1.specification, "Account specification")
        self.assertEqual(p1.order_id, "1232")
        self.assertEqual(p1.user, user)

        self.assertEqual(user.payment_set.get(date=datetime.date(2016, 1, 18)), a1.payment_set.get(account=2150508001))

        unpaired_payment = a1.payment_set.get(VS=130430002)
        unpaired_payment.VS = 130430001
        unpaired_payment.save()
        user1 = UserInCampaign.objects.get(pk=2979)
        admin.pair_variable_symbols(None, None, [a1, ])
        self.assertEqual(user1.payment_set.get(), a1.payment_set.get(VS=130430001))

    def test_darujme_statement(self):
        with open("apps/aklub/test_data/test_darujme.xls", "rb") as f:
            a = AccountStatements(csv_file=File(f), type="darujme")
            a.clean()
            a.save()

        a1 = AccountStatements.objects.get()
        self.assertEqual(len(a1.payment_set.all()), 2)
        user = UserInCampaign.objects.get(pk=2978)
        self.assertEqual(user.payment_set.get(date=datetime.date(2016, 1, 20)), a1.payment_set.get(amount=200))
