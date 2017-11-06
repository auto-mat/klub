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

from django.test import TestCase

from freezegun import freeze_time

from model_mommy import mommy
from model_mommy.recipe import Recipe

from ..utils import ICON_FALSE


@freeze_time("2010-5-1")
class TestNoUpgrade(TestCase):
    """ Test TerminalCondition.no_upgrade() """

    def setUp(self):
        self.userincampaign = Recipe(
            "aklub.UserInCampaign",
            campaign__name="Foo campaign",
            userprofile__first_name="Foo userprofile",
        )

    def test_not_regular(self):
        """ Test UserInCampaign with regular_payments=False returns False """
        user_in_campaign = self.userincampaign.make(
            regular_payments="onetime",
        )
        self.assertEqual(
            user_in_campaign.no_upgrade,
            False,
        )

    def test_not_regular_for_one_year(self):
        """ Test UserInCampaign that is not regular for at leas one year """
        user_in_campaign = self.userincampaign.make(
            regular_payments="regular",
        )
        self.assertEqual(
            user_in_campaign.no_upgrade,
            False,
        )

    def test_no_last_year_payments(self):
        """ Test UserInCampaign that has zero payments from last year """
        user_in_campaign = self.userincampaign.make(
            regular_payments="regular",
            payment_set=[
                mommy.make("Payment", date=datetime.date(year=2010, month=4, day=1)),
            ],
        )
        user_in_campaign.save()
        self.assertEqual(
            user_in_campaign.no_upgrade,
            False,
        )

    def test_missing_payments(self):
        """ Test UserInCampaign that has different amount on payments before one year """
        user_in_campaign = self.userincampaign.make(
            regular_payments="regular",
            payment_set=[
                mommy.make("Payment", date=datetime.date(year=2010, month=4, day=1), amount=100),
                mommy.make("Payment", date=datetime.date(year=2009, month=3, day=1), amount=200),
            ],
        )
        user_in_campaign.save()
        self.assertEqual(
            user_in_campaign.no_upgrade,
            False,
        )

    def test_regular(self):
        """ Test UserInCampaign that has regular payments """
        user_in_campaign = self.userincampaign.make(
            regular_payments="regular",
            payment_set=[
                mommy.make("Payment", date=datetime.date(year=2010, month=4, day=1), amount=100),
                mommy.make("Payment", date=datetime.date(year=2009, month=3, day=1), amount=100),
            ],
        )
        user_in_campaign.save()
        self.assertEqual(
            user_in_campaign.no_upgrade,
            True,
        )


@freeze_time("2016-6-1")
class TestExtraMoney(TestCase):
    """ Test TerminalCondition.extra_money() """

    def setUp(self):
        self.userincampaign = Recipe(
            "aklub.UserInCampaign",
            campaign__name="Foo campaign",
            userprofile__first_name="Foo userprofile",
        )

    def test_extra_payment(self):
        """ Test UserInCampaign with extra payment """
        user_in_campaign = self.userincampaign.make(
            regular_amount=100,
            regular_payments="regular",
            regular_frequency="monthly",
            payment_set=[
                mommy.make("Payment", date=datetime.date(year=2016, month=5, day=5), amount=250),
            ],
        )
        user_in_campaign.save()
        self.assertEqual(user_in_campaign.extra_money, 150)
        self.assertEqual(user_in_campaign.extra_payments(), "150&nbsp;Kč")

    def test_payment_too_old(self):
        """ Test that if the payment is older than 27 days, it is not counted in  """
        user_in_campaign = self.userincampaign.make(
            regular_amount=100,
            regular_payments="regular",
            regular_frequency="monthly",
            payment_set=[
                mommy.make("Payment", date=datetime.date(year=2016, month=5, day=4), amount=250),
            ],
        )
        user_in_campaign.save()
        self.assertEqual(user_in_campaign.extra_money, None)
        self.assertEqual(user_in_campaign.extra_payments(), ICON_FALSE)

    def test_no_extra_payment(self):
        """ Test UserInCampaign with extra payment """
        user_in_campaign = self.userincampaign.make(
            regular_amount=100,
            regular_payments="regular",
            regular_frequency="monthly",
        )
        user_in_campaign.save()
        self.assertEqual(user_in_campaign.extra_money, None)
        self.assertEqual(user_in_campaign.extra_payments(), ICON_FALSE)

    def test_no_frequency(self):
        """ Test UserInCampaign with no regular frequency """
        user_in_campaign = self.userincampaign.make(
            regular_amount=100,
            regular_payments="regular",
            regular_frequency=None,
        )
        user_in_campaign.save()
        self.assertEqual(user_in_campaign.extra_money, None)
        self.assertEqual(user_in_campaign.extra_payments(), ICON_FALSE)

    def test_not_regular(self):
        """ Test when UserInCampaign is not regular """
        user_in_campaign = self.userincampaign.make(
            regular_payments="onetime",
        )
        self.assertEqual(user_in_campaign.extra_money, None)
        self.assertEqual(user_in_campaign.extra_payments(), ICON_FALSE)


class TestNameFunctions(TestCase):
    """ Test UserInCampaign.person_name(), UserInCampaign.__str__() """

    def setUp(self):
        self.user_in_campaign = mommy.make(
            "aklub.UserInCampaign",
            campaign__name="Foo campaign",
            userprofile__last_name="User 1",
            userprofile__first_name="Test",
            userprofile__email="test@test.com",
        )

    def test_user_person_name(self):
        self.assertEqual(self.user_in_campaign.person_name(), 'User 1 Test')

    def test_str(self):
        self.assertEqual(self.user_in_campaign.__str__(), 'User 1 Test - test@test.com (Foo campaign)')
