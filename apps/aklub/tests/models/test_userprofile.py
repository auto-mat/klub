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

    def test_str_only_surname(self):
        """ Test, that __str__ works, when full name is set """
        t = mommy.make(
            "aklub.UserProfile",
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

    def test_get_addressment(self):
        """ Test, that get_addresment function makes vokativ """
        t = mommy.make(
            "aklub.UserProfile",
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

    def test_get_addressment_default_female(self):
        """ Test, that get_addresment function returns default for female """
        t = mommy.make(
            "aklub.UserProfile",
            sex='female',
        )
        self.assertEqual(t.get_addressment(), "členko Klubu přátel Auto*Matu")

    def test_get_addressment_default(self):
        """ Test, that get_addresment function returns default """
        t = mommy.make(
            "aklub.UserProfile",
            sex='unknown',
        )
        self.assertEqual(t.get_addressment(), "člene/členko Klubu přátel Auto*Matu")
