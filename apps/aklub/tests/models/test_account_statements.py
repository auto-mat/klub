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

from django.core.files import File
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings

from model_mommy import mommy

from ..utils import RunCommitHooksMixin
from ... import admin, darujme
from ...models import AccountStatements, ApiAccount, DonorPaymentChannel, Payment, ProfileEmail, Telephone


@override_settings(
    CELERY_ALWAYS_EAGER=True,
)
class AccountStatementTests(RunCommitHooksMixin, TestCase):
    fixtures = ['conditions', 'users']

    def test_bank_new_statement_fio(self):
        with open("apps/aklub/test_data/Pohyby_5_2016.csv", "rb") as f:
            a = AccountStatements(csv_file=File(f), type="account")
            a.clean()
            a.save()

        donor_channel = DonorPaymentChannel.objects.get(VS=120127010)

        self.run_commit_hooks()
        a1 = AccountStatements.objects.get(pk=a.pk)
        self.assertEqual(len(a1.payment_set.all()), 4)
        self.assertEqual(a1.date_from, datetime.date(day=25, month=1, year=2016))
        self.assertEqual(a1.date_to, datetime.date(day=31, month=1, year=2016))

        p1 = Payment.objects.get(account=2150508001)
        self.assertEqual(p1.date, datetime.date(day=18, month=1, year=2016))
        self.assertEqual(p1.amount, 250)
        self.assertEqual(p1.account, '2150508001')
        self.assertEqual(p1.bank_code, '5500')
        self.assertEqual(p1.VS, '120127010')
        self.assertEqual(p1.VS2, None)
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
        self.assertEqual(p1.user_donor_payment_channel, donor_channel)

        self.assertEqual(donor_channel.payment_set.get(date=datetime.date(2016, 1, 18)), a1.payment_set.get(account=2150508001))

    def test_bank_new_statement_cs(self):
        with open("apps/aklub/test_data/Pohyby_cs.csv", "rb") as f:
            a = AccountStatements(csv_file=File(f), type="account_cs")
            a.clean()
            a.save()

        donor_channel = DonorPaymentChannel.objects.get(VS=120127010)

        self.run_commit_hooks()
        a1 = AccountStatements.objects.get(pk=a.pk)
        self.assertEqual(len(a1.payment_set.all()), 3)
        self.assertEqual(a1.date_from, datetime.date(day=10, month=2, year=2019))
        self.assertEqual(a1.date_to, datetime.date(day=11, month=3, year=2019))

        p1 = Payment.objects.get(account='20000 92392323')
        self.assertEqual(p1.date, datetime.date(day=11, month=3, year=2019))
        self.assertEqual(p1.amount, 1000)
        self.assertEqual(p1.account, '20000 92392323')
        self.assertEqual(p1.bank_code, '800')
        self.assertEqual(p1.VS, '120127010')
        self.assertEqual(p1.VS2, '120127010')
        self.assertEqual(p1.SS, "5")
        self.assertEqual(p1.KS, '0')
        self.assertEqual(p1.user_identification, '')
        self.assertEqual(p1.type, 'bank-transfer')
        self.assertEqual(p1.done_by, "")
        self.assertEqual(p1.account_name, "Test Name")
        self.assertEqual(p1.bank_name, "")
        self.assertEqual(p1.transfer_note, "Message for sender 1")
        self.assertEqual(p1.currency, None)
        self.assertEqual(p1.recipient_message, "Message for recepien 1")
        self.assertEqual(p1.operation_id, None)
        self.assertEqual(p1.transfer_type, None)
        self.assertEqual(p1.specification, None)
        self.assertEqual(p1.order_id, None)
        self.assertEqual(p1.user_donor_payment_channel, donor_channel)

        self.assertEqual(donor_channel.payment_set.get(date=datetime.date(2019, 3, 11)), a1.payment_set.get(account='20000 92392323'))

    def test_bank_new_statement_kb(self):
        with open("apps/aklub/test_data/pohyby_kb.csv", "rb") as f:
            a = AccountStatements(csv_file=File(f), type="account_kb")
            a.clean()
            a.save()

        donor_channel = DonorPaymentChannel.objects.get(VS=120127010)

        self.run_commit_hooks()
        a1 = AccountStatements.objects.get(pk=a.pk)
        self.assertEqual(len(a1.payment_set.all()), 3)
        self.assertEqual(a1.date_from, datetime.date(day=1, month=2, year=2010))
        self.assertEqual(a1.date_to, datetime.date(day=3, month=2, year=2010))

        p1 = Payment.objects.get(account='28937-32323234')
        self.assertEqual(p1.date, datetime.date(day=1, month=2, year=2010))
        self.assertEqual(p1.amount, 500)
        self.assertEqual(p1.account, '28937-32323234')
        self.assertEqual(p1.bank_code, '9999')
        self.assertEqual(p1.VS, '120127010')
        self.assertEqual(p1.VS2, None)
        self.assertEqual(p1.SS, "3232")
        self.assertEqual(p1.KS, '23')
        self.assertEqual(p1.user_identification, '')
        self.assertEqual(p1.type, 'bank-transfer')
        self.assertEqual(p1.done_by, "")
        self.assertEqual(p1.account_name, "Protiucet_name")
        self.assertEqual(p1.bank_name, "")
        self.assertEqual(p1.transfer_note, "TEST1, ")
        self.assertEqual(p1.currency, None)
        self.assertEqual(p1.recipient_message, 'Z    CK-73782378278')
        self.assertEqual(p1.operation_id, None)
        self.assertEqual(p1.transfer_type, None)
        self.assertEqual(p1.specification, None)
        self.assertEqual(p1.order_id, None)
        self.assertEqual(p1.user_donor_payment_channel, donor_channel)

        self.assertEqual(donor_channel.payment_set.get(date=datetime.date(2010, 2, 1)), a1.payment_set.get(account='28937-32323234'))

    def test_bank_new_statement_csob(self):
        with open("apps/aklub/test_data/pohyby_csob.csv", "rb") as f:
            a = AccountStatements(csv_file=File(f), type="account_csob")
            a.clean()
            a.save()

        donor_channel = DonorPaymentChannel.objects.get(VS=120127010)

        self.run_commit_hooks()
        a1 = AccountStatements.objects.get(pk=a.pk)
        self.assertEqual(len(a1.payment_set.all()), 4)
        self.assertEqual(a1.date_from, datetime.date(day=19, month=7, year=2019))
        self.assertEqual(a1.date_to, datetime.date(day=2, month=8, year=2019))

        p1 = Payment.objects.get(account='99999999')
        self.assertEqual(p1.date, datetime.date(day=19, month=7, year=2019))
        self.assertEqual(p1.amount, 200)
        self.assertEqual(p1.account, '99999999')
        self.assertEqual(p1.bank_code, '0600')
        self.assertEqual(p1.VS, '120127010')
        self.assertEqual(p1.VS2, None)
        self.assertEqual(p1.SS, "9999")
        self.assertEqual(p1.KS, '1')
        self.assertEqual(p1.user_identification, '')
        self.assertEqual(p1.type, 'bank-transfer')
        self.assertEqual(p1.done_by, "")
        self.assertEqual(p1.account_name, "TEST USER 1")
        self.assertEqual(p1.bank_name, "")
        self.assertEqual(p1.transfer_note, "")
        self.assertEqual(p1.currency, 'CZK')
        self.assertEqual(p1.recipient_message, 'We must test')
        self.assertEqual(p1.operation_id, None)
        self.assertEqual(p1.transfer_type, None)
        self.assertEqual(p1.specification, None)
        self.assertEqual(p1.order_id, None)
        self.assertEqual(p1.user_donor_payment_channel, donor_channel)

        self.assertEqual(donor_channel.payment_set.get(date=datetime.date(2019, 7, 19)), a1.payment_set.get(account='99999999'))

    def test_bank_new_statement_sberbank(self):
        with open("apps/aklub/test_data/pohyby_sberbank.txt", "rb") as f:
            a = AccountStatements(csv_file=File(f), type="account_sberbank")
            a.clean()
            a.save()

        donor_channel = DonorPaymentChannel.objects.get(VS=120127010)

        self.run_commit_hooks()
        a1 = AccountStatements.objects.get(pk=a.pk)
        self.assertEqual(len(a1.payment_set.all()), 4)
        self.assertEqual(a1.date_from, None)
        self.assertEqual(a1.date_to, None)

        p1 = Payment.objects.get(account='9999999999')
        self.assertEqual(p1.date, datetime.date(day=13, month=8, year=2019))
        self.assertEqual(p1.amount, 1000)
        self.assertEqual(p1.account, '9999999999')
        self.assertEqual(p1.bank_code, '9999')
        self.assertEqual(p1.VS, '120127010')
        self.assertEqual(p1.VS2, None)
        self.assertEqual(p1.SS, '')
        self.assertEqual(p1.KS, '999')
        self.assertEqual(p1.user_identification, '')
        self.assertEqual(p1.type, 'bank-transfer')
        self.assertEqual(p1.done_by, "")
        self.assertEqual(p1.account_name, "Tester TEST")
        self.assertEqual(p1.bank_name, "")
        self.assertEqual(p1.transfer_note, None)
        self.assertEqual(p1.currency, 'CZK')
        self.assertEqual(p1.recipient_message, "MESSAGE TEST ONE")
        self.assertEqual(p1.operation_id, None)
        self.assertEqual(p1.transfer_type, 'kreditní')
        self.assertEqual(p1.specification, None)
        self.assertEqual(p1.order_id, None)
        self.assertEqual(p1.user_donor_payment_channel, donor_channel)

        self.assertEqual(donor_channel.payment_set.get(date=datetime.date(2019, 8, 13)), a1.payment_set.get(account='9999999999'))

    def check_account_statement_data(self):
        self.run_commit_hooks()

        a1 = AccountStatements.objects.get(type="darujme")

        self.assertEqual(
            list(a1.payment_set.order_by('SS').values_list("account_name", "date", "SS")),
            [
                ('User 1, Testing', datetime.date(2016, 1, 19), ''),
                ('User 1, Testing', datetime.date(2016, 1, 19), '12121'),
                ('Date, Blank', datetime.date(2016, 8, 9), '12345'),
                ('User, Testing', datetime.date(2016, 1, 20), '17529'),
                ('User 1, Testing', datetime.date(2016, 1, 19), '22256'),
                ('User 1, Testing', datetime.date(2016, 1, 19), '22257'),
            ],
        )

        user = DonorPaymentChannel.objects.get(id=2978)
        self.assertEqual(user.payment_set.get(SS=17529), a1.payment_set.get(amount=200))

        user_email = ProfileEmail.objects.get(email="unknown@email.cz")
        unknown_user = DonorPaymentChannel.objects.get(user=user_email.user)
        payment = unknown_user.payment_set.get(SS=22257)
        tel_unknown_user = Telephone.objects.filter(user=user_email.user).first()
        self.assertEqual(payment.amount, 150)
        self.assertEqual(payment.date, datetime.date(2016, 1, 19))
        self.assertEqual(tel_unknown_user.telephone, "656464222")
        self.assertEqual(unknown_user.user.street, "Ulice 321")
        self.assertEqual(unknown_user.user.city, "Nová obec")
        self.assertEqual(unknown_user.user.zip_code, "12321")
        self.assertEqual(unknown_user.user.username, "unknown3")
        # self.assertEqual(unknown_user.wished_information, True)  # TODO: we should store this information somewhere
        self.assertEqual(unknown_user.regular_payments, "regular")
        self.assertEqual(unknown_user.regular_amount, 150)
        self.assertEqual(unknown_user.regular_frequency, "annually")

        user_email = ProfileEmail.objects.get(email="unknown1@email.cz")
        unknown_user1 = DonorPaymentChannel.objects.get(user=user_email.user)
        tel_unknown_user1 = Telephone.objects.filter(user=user_email.user).first()
        self.assertEqual(tel_unknown_user1, None)  # Telephone was submitted, but in bad format
        self.assertEqual(unknown_user1.user.zip_code, "123 21")
        self.assertEqual(unknown_user1.regular_amount, 150)
        self.assertEqual(unknown_user1.end_of_regular_payments, datetime.date(2014, 12, 31))
        self.assertEqual(unknown_user1.regular_frequency, 'monthly')
        self.assertEqual(unknown_user1.regular_payments, "regular")

        self.assertEqual(Payment.objects.filter(SS=22359).exists(), False)

        user_email = ProfileEmail.objects.get(email="unknown3@email.cz")
        unknown_user3 = DonorPaymentChannel.objects.get(user=user_email.user)
        tel_unknown_user3 = Telephone.objects.filter(user=user_email.user).first()
        self.assertEqual(tel_unknown_user3, None)
        self.assertEqual(unknown_user3.user.zip_code, "")
        self.assertEqual(unknown_user3.regular_amount, 0)
        self.assertEqual(unknown_user3.end_of_regular_payments, None)
        self.assertEqual(unknown_user3.regular_frequency, 'monthly')
        self.assertEqual(unknown_user3.regular_payments, "promise")

        user_email = ProfileEmail.objects.get(email="test.user1@email.cz")
        test_user1 = DonorPaymentChannel.objects.get(user=user_email.user)
        tel_user1 = Telephone.objects.filter(user=user_email.user).first()
        self.assertEqual(test_user1.user.zip_code, "")
        self.assertEqual(tel_user1, None)
        self.assertEqual(test_user1.regular_amount, 150)
        self.assertEqual(test_user1.end_of_regular_payments, None)
        self.assertEqual(test_user1.regular_frequency, "annually")
        self.assertEqual(test_user1.regular_payments, "regular")

        user_email = ProfileEmail.objects.get(email="blank.date@seznam.cz")
        blank_date_user = DonorPaymentChannel.objects.get(user=user_email.user)
        payment_blank = blank_date_user.payment_set.get(SS=12345)
        tel_blank_date_user = Telephone.objects.filter(user=user_email.user).first()
        self.assertEqual(tel_blank_date_user, None)
        self.assertEqual(payment_blank.amount, 500)
        self.assertEqual(payment_blank.date, datetime.date(2016, 8, 9))
        self.assertEqual(blank_date_user.user.zip_code, "")
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

    @patch("urllib.request")
    def test_darujme_action(self, urllib_request):
        request = RequestFactory().get("")
        with open("apps/aklub/test_data/darujme.xml", "r", encoding="utf-8") as f:
            m = MagicMock()
            urllib_request.urlopen = MagicMock(return_value=f)
            admin.download_darujme_statement(m, request, ApiAccount.objects.filter(event__slug='klub'))
        a1 = self.check_account_statement_data()
        m.message_user.assert_called_once_with(
            request,
            'Created following account statements: %s<br/>Skipped payments: ['
            'OrderedDict([(&#39;ss&#39;, &#39;22258&#39;), (&#39;date&#39;, &#39;2016-02-09&#39;), (&#39;name&#39;, &#39;Testing&#39;), '
            '(&#39;surname&#39;, &#39;User 1&#39;), (&#39;email&#39;, &#39;test.user1@email.cz&#39;)])]' % a1.id,
        )


@override_settings(
    CELERY_ALWAYS_EAGER=True,
)
class TestPairPayments(TestCase):
    """ Test AccountStatement. payment_pair()"""
    def setUp(self):
        self.payment_vs = mommy.make("aklub.Payment", id=1, VS=123, account=999999, bank_code=1111)
        self.payment_no_vs = mommy.make("aklub.Payment", id=2, account=999999, bank_code=1111)

        self.administrative_unit_1 = mommy.make("aklub.AdministrativeUnit", name='test1')
        self.administrative_unit_2 = mommy.make("aklub.AdministrativeUnit", name='test2')

        self.user_bank_acc = mommy.make('aklub.UserBankAccount', bank_account_number='999999/1111')

        self.bank_account_1 = mommy.make('aklub.BankAccount', id=1, administrative_unit=self.administrative_unit_1)
        self.bank_account_2 = mommy.make('aklub.BankAccount', id=2, administrative_unit=self.administrative_unit_2)

        self.donor_payment_channel_1 = mommy.make(
                                        'aklub.DonorPaymentChannel',
                                        VS=123,
                                        user_bank_account=self.user_bank_acc,
                                        money_account=self.bank_account_1,
        )
        self.donor_payment_channel_1_1 = mommy.make(
                                        'aklub.DonorPaymentChannel',
                                        VS=1234,
                                        user_bank_account=self.user_bank_acc,
                                        money_account=self.bank_account_1,
        )
        self.donor_payment_channel_2 = mommy.make(
                                        'aklub.DonorPaymentChannel',
                                        VS=123,
                                        user_bank_account=self.user_bank_acc,
                                        money_account=self.bank_account_2,
        )

    def test_pairing_vs(self):
        """
        Test if Variable symbol exist and there is more than one user_bank_acc with same number=
        pair with DPCH with same administrative unit and VS
        """
        account_statement = mommy.make(
            "aklub.AccountStatements",
            administrative_unit=self.administrative_unit_1,
            payment_set=[self.payment_vs],
        )

        return_value = account_statement.payment_pair(self.payment_vs)
        payment = Payment.objects.get(id=1)

        self.assertEqual(payment.user_donor_payment_channel, self.donor_payment_channel_1)
        self.assertEqual(return_value, True)

    def test_pairing_user_bank_acc(self):
        """ Prefer pair with DPCH with unique user bank account in administrative unit """
        account_statement = mommy.make(
            "aklub.AccountStatements",
            administrative_unit=self.administrative_unit_2,
            payment_set=[self.payment_vs],
        )

        return_value = account_statement.payment_pair(self.payment_vs)
        payment = Payment.objects.get(id=1)

        self.assertEqual(payment.user_donor_payment_channel, self.donor_payment_channel_2)
        self.assertEqual(return_value, True)

    def test_pairing_multiple_user_bank_acc_false(self):
        """ Test if Variable symbol not exist and multiple user_bank_acc exist in one administrative unit """

        account_statement = mommy.make(
            "aklub.AccountStatements",
            administrative_unit=self.administrative_unit_1,
            payment_set=[self.payment_no_vs],
        )

        return_value = account_statement.payment_pair(self.payment_no_vs)
        payment = Payment.objects.get(id=2)

        self.assertEqual(payment.user_donor_payment_channel, None)
        self.assertEqual(return_value, False)

    def test_pairing_no_dpch_false(self):
        """ Test if donor_payment_channel is not found """
        payment = mommy.make("aklub.Payment", VS=12345, id=3)
        account_statement = mommy.make(
            "aklub.AccountStatements",
            administrative_unit=self.administrative_unit_1,
            payment_set=[payment],
        )

        return_value = account_statement.payment_pair(payment)
        payment = Payment.objects.get(id=3)

        self.assertEqual(payment.user_donor_payment_channel, None)
        self.assertEqual(return_value, False)
