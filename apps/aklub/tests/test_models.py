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

from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from freezegun import freeze_time

from .utils import ICON_FALSE, ICON_UNKNOWN
from ..models import DonorPaymentChannel, Event, Interaction, Payment, UserProfile


@freeze_time("2016-5-1")
class ModelTests(TestCase):
    fixtures = ['conditions', 'users']

    def setUp(self):
        call_command('denorm_init')
        self.u = DonorPaymentChannel.objects.get(pk=2979)
        self.u1 = DonorPaymentChannel.objects.get(pk=2978)
        self.u2 = DonorPaymentChannel.objects.get(pk=3)
        self.u2.save()
        self.u4 = DonorPaymentChannel.objects.get(pk=4)
        self.p = Payment.objects.get(pk=1)
        self.p1 = Payment.objects.get(pk=2)
        self.p2 = Payment.objects.get(pk=3)
        self.p1.BIC = 101
        self.p1.save()
        call_command('denorm_flush')
        self.u1 = DonorPaymentChannel.objects.get(pk=2978)

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
        self.assertSetEqual(set(self.u1.payment_set.all()), {self.p1, self.p2, self.p})
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
        self.assertEqual(self.u1.user.mail_communications_count(), False)
        self.assertEqual(self.u1.payment_delay(), '3\xa0týdny, 1\xa0den')
        self.assertEqual(self.u1.payment_total, 350.0)
        self.assertEqual(self.u1.total_contrib_string(), "350&nbsp;Kč")
        self.assertEqual(self.u1.registered_support_date(), "16. 12. 2015")
        self.assertEqual(self.u1.payment_total_range(datetime.date(2016, 1, 1), datetime.date(2016, 2, 1)), 0)
        self.assertEqual(self.u1.no_upgrade, False)
        self.assertEqual(self.u1.monthly_regular_amount(), 100)

        self.assertEqual(self.u2.expected_regular_payment_date, datetime.date(2015, 12, 19))
        self.assertEqual(self.u2.payment_delay(), '4\xa0měsíce, 2\xa0týdny')
        self.assertEqual(self.u2.regular_payments_info(), datetime.date(2015, 12, 19))

        self.assertEqual(self.u4.payment_delay(), ICON_FALSE)
        self.assertEqual(self.u4.regular_payments_info(), ICON_UNKNOWN)


class CommunicationTest(TestCase):
    def setUp(self):
        self.userprofile = UserProfile.objects.create(sex='male', email="test@test.cz")
        self.campaign = Event.objects.create(created=datetime.date(2010, 10, 10))

    def test_communication(self):
        Interaction.objects.create(
            type="individual",
            user=self.userprofile,
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
        Interaction.objects.create(
            type="individual",
            user=self.userprofile,
            date=datetime.date(2016, 1, 1),
            method="phonecall",
            send=True,
        )
        self.assertEqual(len(mail.outbox), 0)
