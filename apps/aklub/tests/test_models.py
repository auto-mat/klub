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
from django.test import TestCase

from events.models import Event

from freezegun import freeze_time

from interactions.models import Interaction

from model_mommy import mommy

from .utils import ICON_FALSE, ICON_UNKNOWN
from aklub.models import DonorPaymentChannel, Payment, UserProfile


@freeze_time("2016-5-1")
class ModelTests(TestCase):
    fixtures = ["conditions", "users"]

    def setUp(self):
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
        self.u1 = DonorPaymentChannel.objects.get(pk=2978)

    def test_user_model(self):
        # self.assertEqual(self.u.is_direct_dialogue(), False)
        self.assertEqual(self.u.last_payment_date(), None)
        self.assertEqual(self.u.last_payment_type(), None)
        self.assertEqual(self.u.requires_action(), False)
        self.assertEqual(self.u.expected_regular_payment_date, None)
        self.assertEqual(self.u.regular_payments_delay(), None)
        self.assertEqual(self.u.extra_payments(), ICON_FALSE)
        self.assertEqual(self.u.regular_payments_info(), ICON_FALSE)
        self.assertEqual(self.u.no_upgrade, False)
        self.assertEqual(self.u.monthly_regular_amount(), 0)

        self.assertEqual(self.u1.person_name(), "User Test")
        self.assertEqual(self.u1.requires_action(), True)
        self.assertSetEqual(set(self.u1.payment_set.all()), {self.p1, self.p2, self.p})
        self.assertEqual(self.u1.number_of_payments, 3)
        self.assertEqual(self.u1.last_payment, self.p1)
        self.assertEqual(self.u1.last_payment_date(), datetime.date(2016, 3, 9))
        self.assertEqual(self.u1.last_payment_type(), "bank-transfer")
        self.assertEqual(self.u1.regular_frequency_td(), datetime.timedelta(31))
        self.assertEqual(
            self.u1.expected_regular_payment_date, datetime.date(2016, 4, 9)
        )
        self.assertEqual(self.u1.regular_payments_delay(), datetime.timedelta(12))
        self.assertEqual(self.u1.extra_money, None)
        self.assertEqual(self.u1.regular_payments_info(), datetime.date(2016, 4, 9))
        self.assertEqual(self.u1.extra_payments(), ICON_FALSE)
        self.assertEqual(self.u1.user.mail_communications_count(), False)
        self.assertEqual(self.u1.payment_total, 350.0)
        self.assertEqual(self.u1.total_contrib_string(), "350&nbsp;Kč")
        self.assertEqual(self.u1.registered_support_date(), "16. 12. 2015")
        self.assertEqual(
            self.u1.payment_total_range(
                datetime.date(2016, 1, 1), datetime.date(2016, 2, 1)
            ),
            0,
        )
        self.assertEqual(self.u1.no_upgrade, False)
        self.assertEqual(self.u1.monthly_regular_amount(), 100)

        self.assertEqual(
            self.u2.expected_regular_payment_date, datetime.date(2015, 12, 19)
        )
        self.assertEqual(self.u2.regular_payments_info(), datetime.date(2015, 12, 19))

        self.assertEqual(self.u4.regular_payments_info(), ICON_UNKNOWN)


class CommunicationTest(TestCase):
    def setUp(self):
        self.userprofile = UserProfile.objects.create(sex="male")
        mommy.make(
            "ProfileEmail", user=self.userprofile, email="test@test.cz", is_primary=True
        )
        self.campaign = Event.objects.create(date_from=datetime.date(2010, 10, 10))

    def test_communication(self):
        inter_category = mommy.make(
            "interactions.interactioncategory", category="testcategory"
        )
        inter_type = mommy.make(
            "interactions.interactiontype",
            category=inter_category,
            name="testtype",
            send_email=True,
        )
        unit = mommy.make("aklub.administrativeunit", name="testAU")
        Interaction.objects.create(
            communication_type="individual",
            user=self.userprofile,
            date_from=datetime.date(2016, 1, 1),
            type=inter_type,
            summary="Testing template",
            subject="Testing email",
            administrative_unit=unit,
        )
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ["test@test.cz"])
        self.assertEqual(msg.subject, "Testing email")
        self.assertIn("Testing template", msg.body)

    def test_communication_sms(self):
        inter_category = mommy.make(
            "interactions.interactioncategory", category="testcategory"
        )
        inter_type = mommy.make(
            "interactions.interactiontype",
            category=inter_category,
            name="testtype",
            send_sms=True,
        )
        unit = mommy.make("aklub.administrativeunit", name="testAU")
        Interaction.objects.create(
            communication_type="individual",
            user=self.userprofile,
            date_from=datetime.date(2016, 1, 1),
            type=inter_type,
            administrative_unit=unit,
        )
        self.assertEqual(len(mail.outbox), 0)
