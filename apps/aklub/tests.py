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
import datetime
from freezegun import freeze_time
from .models import TerminalCondition, Condition, User, Communication, AutomaticCommunication, AccountStatements
from django_admin_smoke_tests import tests
from .confirmation import makepdf
from . import autocom, mailing
import io
from PyPDF2 import PdfFileReader
from django.core.files import File


class BaseTestCase(TestCase):
    def assertQuerysetEquals(self, qs1, qs2):
        pk = lambda o: o.pk
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
            variable="User.date_condition",
            value="datetime.2010-09-24 00:00",
            operation=">",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(date_condition__gt=datetime.datetime(2010, 9, 24, 0, 0)))

    def test_boolean_condition(self):
        c = Condition.objects.create(operation="or")
        TerminalCondition.objects.create(
            variable="User.boolean_condition",
            value="true",
            operation="=",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(boolean_condition=True))

    def test_time_condition(self):
        c = Condition.objects.create(operation="or")
        TerminalCondition.objects.create(
            variable="User.time_condition",
            value="month_ago",
            operation="<",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(time_condition__lt=datetime.datetime(2009, 12, 2, 0, 0)))

    def test_text_condition(self):
        c = Condition.objects.create(operation="or")
        TerminalCondition.objects.create(
            variable="User.text_condition",
            value="asdf",
            operation="contains",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(text_condition__contains="asdf"))

    def test_text_icontains_condition(self):
        c = Condition.objects.create(operation="or")
        TerminalCondition.objects.create(
            variable="User.text_condition",
            value="asdf",
            operation="icontains",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(text_condition__icontains="asdf"))

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

    def test_blank_condition(self):
        c = Condition.objects.create(operation="and")
        TerminalCondition.objects.create(
            variable="User.regular_payments",
            value="true",
            operation="=",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(regular_payments=True))

    def test_combined_condition(self):
        c = Condition.objects.create(operation="and")
        TerminalCondition.objects.create(
            variable="User.time_condition",
            value="timedelta.5",
            operation=">=",
            condition=c,
        )
        TerminalCondition.objects.create(
            variable="User.days_ago_condition",
            value="days_ago.6",
            operation="!=",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), ~Q(days_ago_condition=datetime.datetime(2009, 12, 26, 0, 0)) & Q(time_condition__gte=datetime.timedelta(5)))

    def test_multiple_combined_conditions(self):
        c1 = Condition.objects.create(operation="and")
        c2 = Condition.objects.create(operation="nor")
        c2.conds.add(c1)
        TerminalCondition.objects.create(
            variable="User.time_condition",
            value="timedelta.5",
            operation=">=",
            condition=c1,
        )
        TerminalCondition.objects.create(
            variable="User.days_ago_condition",
            value="days_ago.6",
            operation="!=",
            condition=c1,
        )
        TerminalCondition.objects.create(
            variable="User.int_condition",
            value="5",
            operation="<=",
            condition=c2,
        )
        TerminalCondition.objects.create(
            variable="User.int_condition",
            value="4",
            operation="=",
            condition=c2,
        )
        test_query = ~((~Q(days_ago_condition=datetime.datetime(2009, 12, 26, 0, 0)) & Q(time_condition__gte=datetime.timedelta(5))) | Q(int_condition=4) | Q(int_condition__lte=5))
        self.assertQueryEquals(c2.get_query(), test_query)


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
        self.user = User.objects.create(sex='male')
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
            last_name="User",
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
    fixtures = ['conditions']

class ViewsTestsLogon(TestCase):
    fixtures = ['conditions']

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
        reverse('stay-members'),
        reverse('stay-payments'),
    ]

    def test_aklub_views(self):
        """
        test if the user pages work
        """
        status_code_map = {
        }

        self.verify_views(self.views, status_code_map)

class AccountStatementTests(TestCase):
    fixtures = ['conditions', 'users']

    def test_bank_statement(self):
        with open("apps/aklub/test_data/test_statement.csv", "rb") as f:
            a = AccountStatements(csv_file=File(f), type="account")
            a.clean()
            a.save()

            a1 = AccountStatements.objects.get()
            self.assertEqual(len(a1.payment_set.all()), 3)
            user = User.objects.get()
            self.assertEqual(user.payment_set.get(), a1.payment_set.get(account=2150508001))

    def test_darujme_statement(self):
        with open("apps/aklub/test_data/test_darujme.xls", "rb") as f:
            a = AccountStatements(csv_file=File(f), type="darujme")
            a.clean()
            a.save()

            a1 = AccountStatements.objects.get()
            self.assertEqual(len(a1.payment_set.all()), 2)
            user = User.objects.get()
            self.assertEqual(user.payment_set.get(), a1.payment_set.get(amount=200))
