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

import datetime

from collections import OrderedDict
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.core import mail
from django.core.files import File
from django.core.management import call_command
from django.forms import ValidationError
from django.test import RequestFactory, TestCase

from freezegun import freeze_time

from .. import admin, darujme
from ..models import (
    AccountStatements, Campaign, Communication,
    Payment, Result, UserInCampaign, UserProfile,
)

ICON_FALSE = '<img src="/media/admin/img/icon-no.svg" alt="False" />'
ICON_UNKNOWN = '<img src="/media/admin/img/icon-unknown.svg" alt="None" />'


@freeze_time("2016-5-1")
class ModelTests(TestCase):
    fixtures = ['conditions', 'users']

    def setUp(self):
        call_command('denorm_init')
        self.u = UserInCampaign.objects.get(pk=2979)
        self.u1 = UserInCampaign.objects.get(pk=2978)
        self.u2 = UserInCampaign.objects.get(pk=3)
        self.u2.save()
        self.u4 = UserInCampaign.objects.get(pk=4)
        self.p = Payment.objects.get(pk=1)
        self.p1 = Payment.objects.get(pk=2)
        self.p2 = Payment.objects.get(pk=3)
        self.p1.BIC = 101
        self.p1.save()
        call_command('denorm_flush')
        self.u1 = UserInCampaign.objects.get(pk=2978)
        self.tax_confirmation, created = self.u1.userprofile.make_tax_confirmation(2016)

    def test_payment_model(self):
        self.assertEqual(self.p.person_name(), 'User Test')

    def test_user_person_name(self):
        self.assertEqual(self.u.person_name(), 'User 1 Test')

    def test_result_str(self):
        self.assertEqual(Result(name="Test result").__str__(), 'Test result')

    def test_user_model(self):
        self.assertEqual(self.u.is_direct_dialogue(), False)
        self.assertEqual(self.u.last_payment_date(), None)
        self.assertEqual(self.u.last_payment_type(), None)
        self.assertEqual(self.u.requires_action(), False)
        self.assertEqual(self.u.payment_delay(), ICON_FALSE)
        self.assertEqual(self.u.expected_regular_payment_date, None)
        self.assertEqual(self.u.regular_payments_delay(), False)
        self.assertEqual(self.u.extra_payments(), ICON_FALSE)
        self.assertEqual(self.u.regular_payments_info(), ICON_FALSE)
        self.assertEqual(self.u.no_upgrade, False)
        self.assertEqual(self.u.monthly_regular_amount(), 0)

        self.assertEqual(self.u1.is_direct_dialogue(), False)
        self.assertEqual(self.u1.person_name(), 'User Test')
        self.assertEqual(self.u1.requires_action(), True)
        self.assertSetEqual(set(self.u1.payment_set.all()), set((self.p1, self.p2, self.p)))
        self.assertEqual(self.u1.number_of_payments, 3)
        self.assertEqual(self.u1.last_payment, self.p1)
        self.assertEqual(self.u1.last_payment_date(), datetime.date(2016, 3, 9))
        self.assertEqual(self.u1.last_payment_type(), 'bank-transfer')
        self.assertEqual(self.u1.regular_frequency_td(), datetime.timedelta(31))
        self.assertEqual(self.u1.expected_regular_payment_date, datetime.date(2016, 4, 9))
        self.assertEqual(self.u1.regular_payments_delay(), datetime.timedelta(12))
        self.assertEqual(self.u1.extra_money, None)
        self.assertEqual(self.u1.regular_payments_info(), datetime.date(2016, 4, 9))
        self.assertEqual(self.u1.extra_payments(), ICON_FALSE)
        self.assertEqual(self.u1.mail_communications_count(), False)
        self.assertEqual(self.u1.payment_delay(), '3\xa0týdny, 1\xa0den')
        self.assertEqual(self.u1.payment_total, 350.0)
        self.assertEqual(self.u1.total_contrib_string(), "350&nbsp;Kč")
        self.assertEqual(self.u1.registered_support_date(), "16. 12. 2015")
        self.assertEqual(self.u1.payment_total_range(datetime.date(2016, 1, 1), datetime.date(2016, 2, 1)), 0)
        self.assertEqual(self.tax_confirmation.year, 2016)
        self.assertTrue("PDF-1.4" in str(self.tax_confirmation.file.read()))
        self.assertEqual(self.tax_confirmation.amount, 350)
        self.assertEqual(self.u1.no_upgrade, False)
        self.assertEqual(self.u1.monthly_regular_amount(), 100)

        self.assertEqual(self.u2.expected_regular_payment_date, datetime.date(2015, 12, 19))
        self.assertEqual(self.u2.payment_delay(), '4\xa0měsíce, 2\xa0týdny')
        self.assertEqual(self.u2.regular_payments_info(), datetime.date(2015, 12, 19))

        self.assertEqual(self.u4.payment_delay(), ICON_FALSE)
        self.assertEqual(self.u4.regular_payments_info(), ICON_UNKNOWN)

    def test_extra_payments(self):
        Payment.objects.create(date=datetime.date(year=2016, month=5, day=1), user=self.u1, amount=250)
        call_command('denorm_flush')
        self.u1 = UserInCampaign.objects.get(pk=2978)
        self.assertEqual(self.u1.extra_money, 150)
        self.assertEqual(self.u1.extra_payments(), "150&nbsp;Kč")


class CommunicationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="test@test.cz")
        self.userprofile = UserProfile.objects.create(sex='male', user=self.user)
        self.campaign = Campaign.objects.create(created=datetime.date(2010, 10, 10))
        self.userincampaign = UserInCampaign.objects.create(userprofile=self.userprofile, campaign=self.campaign)

    def test_communication(self):
        Communication.objects.create(
            type="individual",
            user=self.userincampaign,
            date=datetime.date(2016, 1, 1),
            method="email",
            summary="Testing template",
            subject="Testing email",
            send=True,
        )
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test@test.cz', 'kp@auto-mat.cz'])
        self.assertEqual(msg.subject, 'Testing email')
        self.assertIn("Testing template", msg.body)

    def test_communication_phonecall(self):
        Communication.objects.create(
            type="individual",
            user=self.userincampaign,
            date=datetime.date(2016, 1, 1),
            method="phonecall",
            send=True,
        )
        self.assertEqual(len(mail.outbox), 0)


class AccountStatementTests(TestCase):
    fixtures = ['conditions', 'users']

    def test_bank_new_statement(self):
        with open("apps/aklub/test_data/Pohyby_5_2016.csv", "rb") as f:
            a = AccountStatements(csv_file=File(f), type="account")
            a.clean()
            a.save()

        a1 = AccountStatements.objects.get(pk=a.pk)
        self.assertEqual(len(a1.payment_set.all()), 4)
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
        self.assertEqual(user1.payment_set.get(VS=130430001), a1.payment_set.get(VS=130430001))

    def check_account_statement_data(self):
        a1 = AccountStatements.objects.get(type="darujme")
        self.assertEqual(
            list(a1.payment_set.values_list("account_name", "date", "SS")),
            [
                ('Date, Blank', datetime.date(2016, 8, 9), '12345'),
                ('User, Testing', datetime.date(2016, 1, 20), '17529'),
                ('User 1, Testing', datetime.date(2016, 1, 19), '12121'),
                ('User 1, Testing', datetime.date(2016, 1, 19), ''),
                ('User 1, Testing', datetime.date(2016, 1, 19), '22257'),
                ('User 1, Testing', datetime.date(2016, 1, 19), '22256'),
            ],
        )
        user = UserInCampaign.objects.get(pk=2978)
        self.assertEqual(user.payment_set.get(SS=17529), a1.payment_set.get(amount=200))
        unknown_user = UserInCampaign.objects.get(userprofile__user__email="unknown@email.cz")
        payment = unknown_user.payment_set.get(SS=22257)
        self.assertEqual(payment.amount, 150)
        self.assertEqual(payment.date, datetime.date(2016, 1, 19))
        self.assertEqual(unknown_user.__str__(), "User 1 Testing - unknown@email.cz (Klub přátel Auto*Matu)")
        self.assertEqual(unknown_user.userprofile.telephone, "656 464 222")
        self.assertEqual(unknown_user.userprofile.street, "Ulice 321")
        self.assertEqual(unknown_user.userprofile.city, "Nová obec")
        self.assertEqual(unknown_user.userprofile.zip_code, "12321")
        self.assertEqual(unknown_user.userprofile.user.username, "unknown3")
        self.assertEqual(unknown_user.wished_information, True)
        self.assertEqual(unknown_user.regular_payments, "regular")
        self.assertEqual(unknown_user.regular_amount, 150)
        self.assertEqual(unknown_user.regular_frequency, "annually")

        unknown_user1 = UserInCampaign.objects.get(userprofile__user__email="unknown1@email.cz")
        self.assertEqual(unknown_user1.userprofile.telephone, "2158")
        self.assertEqual(unknown_user1.userprofile.zip_code, "123 21")
        self.assertEqual(unknown_user1.regular_amount, 150)
        self.assertEqual(unknown_user1.end_of_regular_payments, datetime.date(2014, 12, 31))
        self.assertEqual(unknown_user1.regular_frequency, 'monthly')
        self.assertEqual(unknown_user1.regular_payments, "regular")

        self.assertEqual(Payment.objects.filter(SS=22359).exists(), False)
        unknown_user3 = UserInCampaign.objects.get(userprofile__user__email="unknown3@email.cz")
        self.assertEqual(unknown_user3.userprofile.zip_code, "")
        self.assertEqual(unknown_user3.userprofile.telephone, "")
        self.assertEqual(unknown_user3.regular_amount, 0)
        self.assertEqual(unknown_user3.end_of_regular_payments, None)
        self.assertEqual(unknown_user3.regular_frequency, 'monthly')
        self.assertEqual(unknown_user3.regular_payments, "promise")

        test_user1 = UserInCampaign.objects.get(userprofile__user__email="test.user1@email.cz")
        self.assertEqual(test_user1.userprofile.zip_code, "")
        self.assertEqual(test_user1.userprofile.telephone, "")
        self.assertEqual(test_user1.regular_amount, 150)
        self.assertEqual(test_user1.end_of_regular_payments, None)
        self.assertEqual(test_user1.regular_frequency, "annually")
        self.assertEqual(test_user1.regular_payments, "regular")

        blank_date_user = UserInCampaign.objects.get(userprofile__user__email="blank.date@seznam.cz")
        payment_blank = blank_date_user.payment_set.get(SS=12345)
        self.assertEqual(payment_blank.amount, 500)
        self.assertEqual(payment_blank.date, datetime.date(2016, 8, 9))
        self.assertEqual(blank_date_user.userprofile.zip_code, "")
        self.assertEqual(blank_date_user.userprofile.telephone, "")
        self.assertEqual(blank_date_user.regular_amount, None)
        self.assertEqual(blank_date_user.end_of_regular_payments, None)
        self.assertEqual(blank_date_user.regular_frequency, None)
        self.assertEqual(blank_date_user.regular_payments, "onetime")
        return a1

    def test_darujme_statement(self):
        with open("apps/aklub/test_data/test_darujme.xls", "rb") as f:
            a = AccountStatements(csv_file=File(f), type="darujme")
            a.clean()
            a.save()
        self.check_account_statement_data()

    def test_darujme_xml_statement(self):
        a, skipped = darujme.create_statement_from_file("apps/aklub/test_data/darujme.xml")
        a1 = self.check_account_statement_data()
        self.assertEqual(a, a1)
        self.assertListEqual(
            skipped,
            [
                OrderedDict(
                    [
                        ('ss', '22258'),
                        ('date', '2016-02-09'),
                        ('name', 'Testing'),
                        ('surname', 'User 1'),
                        ('email', 'test.user1@email.cz'),
                    ],
                ),
            ],
        )

    def test_darujme_xml_file_skipped(self):
        count_before = AccountStatements.objects.count()
        a, skipped = darujme.create_statement_from_file("apps/aklub/test_data/darujme_skip.xml")
        self.assertEqual(AccountStatements.objects.count(), count_before)
        self.assertEqual(a, None)
        self.assertListEqual(
            skipped,
            [
                OrderedDict(
                    [
                        ('ss', '22258'),
                        ('date', '2016-2-9'),
                        ('name', 'Testing'),
                        ('surname', 'User'),
                        ('email', 'test.user@email.cz'),
                    ],
                ),
            ],
        )

    def test_darujme_xml_file_no_duplicates(self):
        a, skipped = darujme.create_statement_from_file("apps/aklub/test_data/darujme_duplicate.xml")
        self.assertEqual(a.payment_set.count(), 1)
        self.assertListEqual(
            skipped,
            [
                OrderedDict(
                    [
                        ('ss', '23259'),
                        ('date', '2016-3-9'),
                        ('name', 'Testing'),
                        ('surname', 'User'),
                        ('email', 'test.user@email.cz'),
                    ],
                ),
            ],
        )

    def test_darujme_xml_statement_duplicate_email(self):
        u2 = User.objects.get(pk=3)
        u2.email = "test.user@email.cz"
        u2.save()
        with self.assertRaises(ValidationError):
            darujme.create_statement_from_file("apps/aklub/test_data/darujme.xml")

    @patch("urllib.request")
    def test_darujme_action(self, urllib_request):
        request = RequestFactory().get("")
        with open("apps/aklub/test_data/darujme.xml", "r") as f:
            m = MagicMock()
            urllib_request.urlopen = MagicMock(return_value=f)
            admin.download_darujme_statement(m, request, Campaign.objects.filter(slug="klub"))

        a1 = self.check_account_statement_data()
        m.message_user.assert_called_once_with(
            request,
            'Created following account statements: %s<br/>Skipped payments: ['
            'OrderedDict([(&#39;ss&#39;, &#39;22258&#39;), (&#39;date&#39;, &#39;2016-02-09&#39;), (&#39;name&#39;, &#39;Testing&#39;), '
            '(&#39;surname&#39;, &#39;User 1&#39;), (&#39;email&#39;, &#39;test.user1@email.cz&#39;)])]' % a1.id,
        )
