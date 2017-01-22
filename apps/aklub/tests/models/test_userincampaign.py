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


@freeze_time("2010-5-1")
class TestNoUpgrade(TestCase):
    """ Test TerminalCondition.no_upgrade() """
    def test_not_regular(self):
        """ Test UserInCampaign with regular_payments=False returns False """
        user_in_campaign = mommy.make(
            "aklub.UserInCampaign",
            regular_payments="onetime",
            campaign__name="Foo campaign",
            userprofile__user__first_name="Foo userprofile",
        )
        self.assertEquals(
            user_in_campaign.no_upgrade,
            False,
        )

    def test_not_regular_for_one_year(self):
        """ Test UserInCampaign that is not regular for at leas one year """
        user_in_campaign = mommy.make(
            "aklub.UserInCampaign",
            regular_payments="regular",
            campaign__name="Foo campaign",
            userprofile__user__first_name="Foo userprofile",
        )
        self.assertEquals(
            user_in_campaign.no_upgrade,
            False,
        )

    def test_no_last_year_payments(self):
        """ Test UserInCampaign that has zero payments from last year """
        user_in_campaign = mommy.make(
            "aklub.UserInCampaign",
            regular_payments="regular",
            campaign__name="Foo campaign",
            userprofile__user__first_name="Foo userprofile",
            payment_set=[
                mommy.make("Payment", date=datetime.date(year=2010, month=4, day=1)),
            ],
        )
        user_in_campaign.save()
        self.assertEquals(
            user_in_campaign.no_upgrade,
            False,
        )

    def test_missing_payments(self):
        """ Test UserInCampaign that has different amount on payments before one year """
        user_in_campaign = mommy.make(
            "aklub.UserInCampaign",
            regular_payments="regular",
            campaign__name="Foo campaign",
            userprofile__user__first_name="Foo userprofile",
            payment_set=[
                mommy.make("Payment", date=datetime.date(year=2010, month=4, day=1), amount=100),
                mommy.make("Payment", date=datetime.date(year=2009, month=3, day=1), amount=200),
            ],
        )
        user_in_campaign.save()
        self.assertEquals(
            user_in_campaign.no_upgrade,
            False,
        )

    def test_regular(self):
        """ Test UserInCampaign that has regular payments """
        user_in_campaign = mommy.make(
            "aklub.UserInCampaign",
            regular_payments="regular",
            campaign__name="Foo campaign",
            userprofile__user__first_name="Foo userprofile",
            payment_set=[
                mommy.make("Payment", date=datetime.date(year=2010, month=4, day=1), amount=100),
                mommy.make("Payment", date=datetime.date(year=2009, month=3, day=1), amount=100),
            ],
        )
        user_in_campaign.save()
        self.assertEquals(
            user_in_campaign.no_upgrade,
            True,
        )
