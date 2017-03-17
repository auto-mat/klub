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
    """ Test TerminalCondition.__str__() """
    def test_str(self):
        t = mommy.make(
            "aklub.Condition",
            name="Foo condition",
        )
        self.assertEqual(str(t), "Foo condition")


class TestConditionString(TestCase):
    """ Test TerminalCondition.condition_string() """

    def test_and(self):
        """ Test if and operation works """
        t = mommy.make(
            "aklub.Condition",
            name="Foo condition",
            operation="and",
        )
        self.assertEqual(t.condition_string(), "Foo condition()")

    def test_nor(self):
        """ Test if nor operation works """
        t = mommy.make(
            "aklub.Condition",
            name="Foo condition",
            operation="nor",
        )
        self.assertEqual(t.condition_string(), "not(Foo condition())")

    def test_more_operands(self):
        """ Testing more operands """
        t = mommy.make(
            "aklub.Condition",
            name="Foo condition",
            operation="nor",
            conds=[
                mommy.make("aklub.Condition", operation="and"),
                mommy.make("aklub.Condition", operation="nor"),
            ],
        )
        self.assertEqual(t.condition_string(), "not(Foo condition(None() or not(None())))")
