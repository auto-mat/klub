# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2015 o.s. Auto*Mat
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
from django.db.models import Q
from django.test import TestCase
import datetime
from freezegun import freeze_time
from .models import TerminalCondition, Condition
from django_admin_smoke_tests import tests


class BaseTestCase(TestCase):
    def assertQuerysetEquals(self, qs1, qs2):
        pk = lambda o: o.pk
        return self.assertEqual(
            list(sorted(qs1, key=pk)),
            list(sorted(qs2, key=pk))
        )

    def assertQueryEquals(self, q1, q2):
        return self.assertEqual(
            q1.__str__(),
            q2.__str__()
        )


@freeze_time("2010-1-1")
class ConditionsTests(BaseTestCase):
    """ Test conditions infrastructure and conditions in fixtures """
    maxDiff = None

    def test_date_condition(self):
        c = Condition.objects.create(operation="and")
        TerminalCondition.objects.create(
            variable="User.date_condition",
            value="datetime.2010-09-24 00:00",
            operation=">",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(date_condition__gt=datetime.datetime(2010, 9, 24, 0, 0)))

    def test_boolean_condition(self):
        c = Condition.objects.create(operation="or")
        TerminalCondition.objects.create(
            variable="User.boolean_condition",
            value="true",
            operation="=",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(boolean_condition=True))

    def test_time_condition(self):
        c = Condition.objects.create(operation="or")
        TerminalCondition.objects.create(
            variable="User.time_condition",
            value="month_ago",
            operation="<",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(time_condition__lt=datetime.datetime(2009, 12, 2, 0, 0)))

    def test_text_condition(self):
        c = Condition.objects.create(operation="or")
        TerminalCondition.objects.create(
            variable="User.text_condition",
            value="asdf",
            operation="contains",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(text_condition__contains="asdf"))

    def test_text_icontains_condition(self):
        c = Condition.objects.create(operation="or")
        TerminalCondition.objects.create(
            variable="User.text_condition",
            value="asdf",
            operation="icontains",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(text_condition__icontains="asdf"))

    def test_action_condition_equals(self):
        c = Condition.objects.create(operation="or")
        TerminalCondition.objects.create(
            variable="action",
            value="asdf",
            operation="=",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(action="asdf"), Q())

    def test_action_condition_not_equals(self):
        c = Condition.objects.create(operation="or")
        TerminalCondition.objects.create(
            variable="action",
            value="asdf",
            operation="=",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(pk__in=[]))

    def test_blank_condition(self):
        c = Condition.objects.create(operation="and")
        TerminalCondition.objects.create(
            variable="User.regular_payments",
            value="true",
            operation="=",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), Q(regular_payments=True))

    def test_combined_condition(self):
        c = Condition.objects.create(operation="and")
        TerminalCondition.objects.create(
            variable="User.time_condition",
            value="timedelta.5",
            operation=">=",
            condition=c,
        )
        TerminalCondition.objects.create(
            variable="User.days_ago_condition",
            value="days_ago.6",
            operation="!=",
            condition=c,
        )
        self.assertQueryEquals(c.get_query(), ~Q(days_ago_condition=datetime.datetime(2009, 12, 26, 0, 0)) & Q(time_condition__gte=datetime.timedelta(5)))

    def test_multiple_combined_conditions(self):
        c1 = Condition.objects.create(operation="and")
        c2 = Condition.objects.create(operation="nor")
        c2.conds.add(c1)
        TerminalCondition.objects.create(
            variable="User.time_condition",
            value="timedelta.5",
            operation=">=",
            condition=c1,
        )
        TerminalCondition.objects.create(
            variable="User.days_ago_condition",
            value="days_ago.6",
            operation="!=",
            condition=c1,
        )
        TerminalCondition.objects.create(
            variable="User.int_condition",
            value="5",
            operation="<=",
            condition=c2,
        )
        TerminalCondition.objects.create(
            variable="User.int_condition",
            value="4",
            operation="=",
            condition=c2,
        )
        test_query = ~((~Q(days_ago_condition=datetime.datetime(2009, 12, 26, 0, 0)) & Q(time_condition__gte=datetime.timedelta(5))) | Q(int_condition=4) | Q(int_condition__lte=5))
        self.assertQueryEquals(c2.get_query(), test_query)


class AdminTest(tests.AdminSiteSmokeTest):
    fixtures = ['conditions']
