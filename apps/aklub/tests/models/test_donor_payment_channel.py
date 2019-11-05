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
from ...models import Profile


@freeze_time("2010-5-1")
class TestNoUpgrade(TestCase):
    """ Test TerminalCondition.no_upgrade() """

    def setUp(self):
        self.administrative_unit = mommy.make(
            "aklub.AdministrativeUnit",
            name='test',
        )
        self.bank_account = mommy.make(
            'aklub.BankAccount',
            administrative_unit=self.administrative_unit,
        )

    def test_not_regular(self):
        """ Test DonorPaymentChannel with regular_payments=False returns False """
        for model in Profile.__subclasses__():
            model_name = model._meta.model_name
            profile = mommy.make(
                model_name,
                username='test.{}'.format(model_name),
            )
            donor_payment_channel = mommy.make(
                "aklub.DonorPaymentChannel",
                campaign__name="Foo campaign",
                user=profile,
                money_account=self.bank_account,
            )
            self.assertEqual(
                donor_payment_channel.no_upgrade,
                False,
            )

    def test_not_regular_for_one_year(self):
        """ Test DonorPaymentChannel that is not regular for at leas one year """
        for model in Profile.__subclasses__():
            model_name = model._meta.model_name
            profile = mommy.make(
                model_name,
                username='test.{}'.format(model_name),
            )
            donor_payment_channel = mommy.make(
                "aklub.DonorPaymentChannel",
                campaign__name="Foo campaign",
                regular_payments="regular",
                user=profile,
                money_account=self.bank_account,
            )
            self.assertEqual(
                donor_payment_channel.no_upgrade,
                False,
            )

    def test_no_last_year_payments(self):
        """ Test DonorPaymentChannel that has zero payments from last year """
        for model in Profile.__subclasses__():
            model_name = model._meta.model_name
            profile = mommy.make(
                model_name,
                username='test.{}'.format(model_name),
            )
            donor_payment_channel = mommy.make(
                "aklub.DonorPaymentChannel",
                campaign__name="Foo campaign",
                regular_payments="regular",
                payment_set=[
                    mommy.make("Payment", date=datetime.date(year=2010, month=4, day=1)),
                ],
                user=profile,
                money_account=self.bank_account,
            )
            donor_payment_channel.save()
            self.assertEqual(
                donor_payment_channel.no_upgrade,
                False,
            )

    def test_missing_payments(self):
        """ Test DonorPaymentChannel that has different amount on payments before one year """
        for model in Profile.__subclasses__():
            model_name = model._meta.model_name
            profile = mommy.make(
                model_name,
                username='test.{}'.format(model_name),
            )
            donor_payment_channel = mommy.make(
                "aklub.DonorPaymentChannel",
                campaign__name="Foo campaign",
                regular_payments="regular",
                payment_set=[
                    mommy.make("Payment", date=datetime.date(year=2010, month=4, day=1), amount=100),
                    mommy.make("Payment", date=datetime.date(year=2009, month=3, day=1), amount=200),
                ],
                user=profile,
                money_account=self.bank_account,
            )
            donor_payment_channel.save()
            self.assertEqual(
                donor_payment_channel.no_upgrade,
                False,
            )

    def test_regular(self):
        """ Test DonorPaymentChannel that has regular payments """
        for model in Profile.__subclasses__():
            model_name = model._meta.model_name
            profile = mommy.make(
                model_name,
                username='test.{}'.format(model_name),
            )
            donor_payment_channel = mommy.make(
                "aklub.DonorPaymentChannel",
                campaign__name="Foo campaign",
                regular_payments="regular",
                payment_set=[
                    mommy.make("Payment", date=datetime.date(year=2010, month=4, day=1), amount=100),
                    mommy.make("Payment", date=datetime.date(year=2009, month=3, day=1), amount=100),
                ],
                user=profile,
                money_account=self.bank_account,
            )
            donor_payment_channel.save()
            self.assertEqual(
                donor_payment_channel.no_upgrade,
                True,
            )


@freeze_time("2016-6-1")
class TestExtraMoney(TestCase):
    """ Test TerminalCondition.extra_money() """

    def setUp(self):
        administrative_unit = mommy.make(
            "aklub.AdministrativeUnit",
            name='test',
        )
        self.bank_account = mommy.make(
            'aklub.BankAccount',
            administrative_unit=administrative_unit,
        )
        self.donor_payment_channel = Recipe(
            "aklub.DonorPaymentChannel",
            campaign__name="Foo campaign",
            user__first_name="Foo user",
            money_account=self.bank_account,
        )

    def test_extra_payment(self):
        """ Test DonorPaymentChannel with extra payment """
        for model in Profile.__subclasses__():
            model_name = model._meta.model_name
            profile = mommy.make(
                model_name,
                username='test.{}'.format(model_name),
            )
            donor_payment_channel = self.donor_payment_channel.make(
                regular_amount=100,
                regular_payments="regular",
                regular_frequency="monthly",
                payment_set=[
                    mommy.make("Payment", date=datetime.date(year=2016, month=5, day=5), amount=250),
                ],
                user=profile,
                money_account=self.bank_account,
            )
            donor_payment_channel.save()
            self.assertEqual(donor_payment_channel.extra_money, 150)
            self.assertEqual(donor_payment_channel.extra_payments(), "150&nbsp;Kč")

    def test_payment_too_old(self):
        """ Test that if the payment is older than 27 days, it is not counted in  """
        for model in Profile.__subclasses__():
            model_name = model._meta.model_name
            profile = mommy.make(
                model_name,
                username='test.{}'.format(model_name),
            )
            donor_payment_channel = self.donor_payment_channel.make(
                regular_amount=100,
                regular_payments="regular",
                regular_frequency="monthly",
                payment_set=[
                    mommy.make("Payment", date=datetime.date(year=2016, month=5, day=4), amount=250),
                ],
                user=profile,
                money_account=self.bank_account,
            )
            donor_payment_channel.save()
            self.assertEqual(donor_payment_channel.extra_money, None)
            self.assertEqual(donor_payment_channel.extra_payments(), ICON_FALSE)

    def test_no_extra_payment(self):
        """ Test DonorPaymentChannel with extra payment """
        for model in Profile.__subclasses__():
            model_name = model._meta.model_name
            profile = mommy.make(
                model_name,
                username='test.{}'.format(model_name),
            )
            donor_payment_channel = self.donor_payment_channel.make(
                regular_amount=100,
                regular_payments="regular",
                regular_frequency="monthly",
                user=profile,
                money_account=self.bank_account,
            )
            donor_payment_channel.save()
            self.assertEqual(donor_payment_channel.extra_money, None)
            self.assertEqual(donor_payment_channel.extra_payments(), ICON_FALSE)

    def test_no_frequency(self):
        """ Test DonorPaymentChannel with no regular frequency """
        for model in Profile.__subclasses__():
            model_name = model._meta.model_name
            profile = mommy.make(
                model_name,
                username='test.{}'.format(model_name),
            )
            donor_payment_channel = self.donor_payment_channel.make(
                regular_amount=100,
                regular_payments="regular",
                regular_frequency=None,
                user=profile,
                money_account=self.bank_account,
            )
            donor_payment_channel.save()
            self.assertEqual(donor_payment_channel.extra_money, None)
            self.assertEqual(donor_payment_channel.extra_payments(), ICON_FALSE)

    def test_not_regular(self):
        """ Test when DonorPaymentChannel is not regular """
        for model in Profile.__subclasses__():
            model_name = model._meta.model_name
            profile = mommy.make(
                model_name,
                username='test.{}'.format(model_name),
            )
            donor_payment_channel = self.donor_payment_channel.make(
                regular_payments="onetime",
                user=profile,
                money_account=self.bank_account,
            )
            self.assertEqual(donor_payment_channel.extra_money, None)
            self.assertEqual(donor_payment_channel.extra_payments(), ICON_FALSE)


class TestNameFunctions(TestCase):
    """ Test DonorPaymentChannel.person_name(), DonorPaymentChannel.__str__() """

    def setUp(self):
        user_profile = mommy.make(
            "aklub.UserProfile",
            first_name="Test",
            last_name="User 1",
            email="test@test.com",
            title_before="Ing.",
        )
        company_profile = mommy.make(
            "aklub.CompanyProfile",
            username="test",
            name="Company",
            email="test@test.com",
        )
        administrative_unit = mommy.make(
            "aklub.AdministrativeUnit",
            name='test',
        )
        bank_account = mommy.make(
            'aklub.BankAccount',
            administrative_unit=administrative_unit,
        )
        self.donor_payment_channel_user_profile = mommy.make(
            "aklub.DonorPaymentChannel",
            event__name="Foo campaign",
            user=user_profile,
            VS=1234,
            money_account=bank_account,
        )
        self.donor_payment_channel_company_profile = mommy.make(
            "aklub.DonorPaymentChannel",
            event__name="Foo campaign",
            user=company_profile,
            VS=5678,
            money_account=bank_account,
        )

    def test_user_person_name(self):
        self.assertEqual(self.donor_payment_channel_user_profile.person_name(), 'Ing. User 1 Test')
        self.assertEqual(self.donor_payment_channel_company_profile.person_name(), 'Company')

    def test_str(self):
        self.assertEqual(self.donor_payment_channel_user_profile.__str__(), 'Payment channel: test@test.com - 1234')
        self.assertEqual(self.donor_payment_channel_company_profile.__str__(), 'Payment channel: test@test.com - 5678')
