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

from django.test import TestCase

from freezegun import freeze_time

from model_mommy import mommy


class TestStr(TestCase):
    """ Test UserProfile.__str__() """

    def test_str(self):
        """ Test, that __str__ works, when full name is set """
        t = mommy.make(
            "aklub.UserProfile",
            first_name="Foo",
            last_name="User",
        )
        self.assertEqual(str(t), "User Foo")

        t = mommy.make(
            "aklub.CompanyProfile",
            first_name="Foo",
            last_name="User",
        )
        self.assertEqual(str(t), "User Foo")

    def test_str_titles(self):
        """ Test, that __str__ works, when full name is set """
        t = mommy.make(
            "aklub.UserProfile",
            title_before="Ing.",
            first_name="Foo",
            last_name="User",
            title_after="CSc.",
        )
        self.assertEqual(str(t), "Ing. User Foo, CSc.")

        t = mommy.make(
            "aklub.CompanyProfile",
            first_name="Foo",
            last_name="User",
        )
        self.assertEqual(str(t), "User Foo")

    def test_str_only_surname(self):
        """ Test, that __str__ works, when full name is set """
        t = mommy.make(
            "aklub.UserProfile",
            last_name="User",
        )
        self.assertEqual(str(t), "User")

        t = mommy.make(
            "aklub.CompanyProfile",
            last_name="User",
        )
        self.assertEqual(str(t), "User")

    def test_username(self):
        """ Test, that __str__ works, when only username is set """
        t = mommy.make(
            "aklub.UserProfile",
            username="foo_user",
        )
        self.assertEqual(str(t), "foo_user")
        t.delete()

        t = mommy.make(
            "aklub.CompanyProfile",
            username="foo_user",
        )
        self.assertEqual(str(t), "foo_user")

    def test_get_addressment(self):
        """ Test, that get_addresment function makes vokativ """
        t = mommy.make(
            "aklub.UserProfile",
            first_name="Petr",
        )
        self.assertEqual(t.get_addressment(), "Petře")

        t = mommy.make(
            "aklub.CompanyProfile",
            first_name="Petr",
        )
        self.assertEqual(t.get_addressment(), "Petře")

    def test_get_addressment_override(self):
        """ Test, that get_addresment function takes addressment override """
        t = mommy.make(
            "aklub.UserProfile",
            first_name="Petr",
            addressment="Petříčku",
        )
        self.assertEqual(t.get_addressment(), "Petříčku")

        t = mommy.make(
            "aklub.CompanyProfile",
            first_name="Petr",
            addressment="Petříčku",
        )
        self.assertEqual(t.get_addressment(), "Petříčku")

    def test_get_addressment_default_female(self):
        """ Test, that get_addresment function returns default for female """
        t = mommy.make(
            "aklub.UserProfile",
            sex='female',
        )
        self.assertEqual(t.get_addressment(), "přítelkyně Auto*Matu")

        t = mommy.make(
            "aklub.CompanyProfile",
        )
        self.assertEqual(t.get_addressment(), "Company")

    def test_get_addressment_default(self):
        """ Test, that get_addresment function returns default """
        t = mommy.make(
            "aklub.UserProfile",
            sex='unknown',
        )
        self.assertEqual(t.get_addressment(), "příteli/kyně Auto*Matu")

    def test_email_lowercase(self):
        """ Test, that email is stored in lowercase """
        t = mommy.make(
            "aklub.UserProfile",
            email='tEsT@TeSt.cz',
        )
        self.assertEqual(t.email, "test@test.cz")

        t = mommy.make(
            "aklub.CompanyProfile",
            email='tEsT@TeSt.cz',
        )
        self.assertEqual(t.email, "test@test.cz")

    def test_get_email_str_blank(self):
        """ Test, that get_email_str works when no email is set """
        t = mommy.make(
            "aklub.UserProfile",
        )
        self.assertEqual(t.get_email_str(), "")

        t = mommy.make(
            "aklub.CompanyProfile",
        )
        self.assertEqual(t.get_email_str(), "")

    def test_get_email_str(self):
        """ Test, that get_email_str strips the email """
        t = mommy.make(
            "aklub.UserProfile",
            email='  test@test.cz',
        )
        self.assertEqual(t.get_email_str(), "test@test.cz")

        t = mommy.make(
            "aklub.CompanyProfile",
            email='  test@test.cz',
        )
        self.assertEqual(t.get_email_str(), "test@test.cz")

    def test_clean_email(self):
        """ Test, that clean function cleanes the email """
        t = mommy.make(
            "aklub.UserProfile",
            email='',
        )
        t.clean()
        self.assertEqual(t.email, None)

        t = mommy.make(
            "aklub.CompanyProfile",
            email='',
        )
        t.clean()
        self.assertEqual(t.email, None)

    def test_make_tax_confirmation_no_payment(self):
        """ Test, that make_tax_confirmation function without any payment """
        t = mommy.make("aklub.UserProfile")
        tax_confirmation, created = t.make_tax_confirmation(2016)
        self.assertEqual(tax_confirmation, None)
        self.assertEqual(created, False)

        t = mommy.make("aklub.CompanyProfile")
        tax_confirmation, created = t.make_tax_confirmation(2016)
        self.assertEqual(tax_confirmation, None)
        self.assertEqual(created, False)

    @freeze_time("2016-5-1")
    def test_make_tax_confirmation(self):
        """ Test, that make_tax_confirmation function """
        t = mommy.make("aklub.UserProfile", sex='male')
        uc = mommy.make("aklub.DonorPaymentChannel", user=t, event=mommy.make("Event"))
        mommy.make("aklub.Payment", amount=350, date="2016-01-01", type='regular', user_donor_payment_channel=uc)
        tax_confirmation, created = t.make_tax_confirmation(2016)
        self.assertEqual(t.email, None)
        self.assertEqual(tax_confirmation.year, 2016)
        self.assertEqual(tax_confirmation.amount, 350)

        t = mommy.make("aklub.CompanyProfile")
        uc = mommy.make("aklub.DonorPaymentChannel", user=t, event=mommy.make("Event"))
        mommy.make("aklub.Payment", amount=350, date="2016-01-01", type='regular', user_donor_payment_channel=uc)
        tax_confirmation, created = t.make_tax_confirmation(2016)
        self.assertEqual(t.email, None)
        self.assertEqual(tax_confirmation.year, 2016)
        self.assertEqual(tax_confirmation.amount, 350)
