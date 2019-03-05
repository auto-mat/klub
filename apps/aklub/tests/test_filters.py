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

from unittest.mock import MagicMock

from django.test import RequestFactory, TestCase

from model_mommy import mommy

from .. import admin, filters
from ..models import Event, Payment, Telephone, UserInCampaign, UserProfile


class FilterTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("")


class FilterTests(FilterTestCase):
    def test_email_filter_blank(self):
        mommy.make('UserProfile', email="", first_name="Foo", last_name="")
        f = filters.EmailFilter(self.request, {"email": "blank"}, UserProfile, None)
        q = f.queryset(self.request, UserProfile.objects.all())
        self.assertQuerysetEqual(q, ["<UserProfile: Foo>"])

    def test_email_filter_format(self):
        mommy.make('UserProfile', email='foo', first_name="Foo", last_name="")
        f = filters.EmailFilter(self.request, {"email": "email-format"}, UserProfile, None)
        q = f.queryset(self.request, UserProfile.objects.all())
        self.assertQuerysetEqual(q, ["<UserProfile: Foo>"])

    def test_telephone_filter_duplicate(self):
        mommy.make('Telephone', telephone='123456', is_primary = True, user_id=3)
        mommy.make('Telephone', telephone='123456', is_primary = True, user_id=3)
        f = filters.TelephoneFilter(self.request, {"telephone": "duplicate"}, Telephone, None)
        q = f.queryset(self.request, Telephone.objects.all())
        self.assertQuerysetEqual(q, ["<Telephone: Foo>", "<Telephone: Bar>"], ordered=False)

    def test_telephone_filter_blank(self):
        mommy.make('Telephone', telephone='123456', is_primary=True, user_id=3)
        f = filters.TelephoneFilter(self.request, {"telephone": "blank"}, UserProfile, None)
        q = f.queryset(self.request, Telephone.objects.all())
        self.assertQuerysetEqual(q, ["<Telephone: Foo>"])

    def test_telephone_filter_format(self):
        mommy.make('Telephone', telephone='123456', is_primary=True, user_id=3)
        f = filters.TelephoneFilter(self.request, {"telephone": "bad-format"}, Telephone, None)
        q = f.queryset(self.request, Telephone.objects.all())
        self.assertQuerysetEqual(q, ["<Telephone: Foo>"])

    """
    def test_telephone_filter_without_query(self):
        mommy.make('UserProfile', telephone='1111', first_name="Foo", last_name="")
        f = filters.TelephoneFilter(self.request, {}, UserProfile, None)
        q = f.queryset(self.request, UserProfile.objects.all())
        self.assertQuerysetEqual(q, ["<UserProfile: Foo>"])
    """

    def test_name_filter_duplicate(self):
        mommy.make('UserProfile', first_name="Foo", last_name="")
        mommy.make('UserProfile', first_name="Foo", last_name="")
        f = filters.NameFilter(self.request, {"name": "duplicate"}, UserProfile, None)
        q = f.queryset(self.request, UserProfile.objects.all())
        self.assertQuerysetEqual(q, ["<UserProfile: Foo>", "<UserProfile: Foo>"], ordered=False)

    def test_name_filter_blank(self):
        mommy.make('UserProfile', first_name="", last_name="", username="foo_username")
        f = filters.NameFilter(self.request, {"name": "blank"}, UserProfile, None)
        q = f.queryset(self.request, UserProfile.objects.all())
        self.assertQuerysetEqual(q, ["<UserProfile: foo_username>"])

    def test_name_filter_without_query(self):
        mommy.make('UserProfile', first_name="", last_name="", username="foo_username")
        f = filters.NameFilter(self.request, {}, UserProfile, None)
        q = f.queryset(self.request, UserProfile.objects.all())
        self.assertQuerysetEqual(q, ["<UserProfile: foo_username>"])


class FixtureFilterTests(FilterTestCase):
    fixtures = ['conditions', 'users', 'communications']

    def test_payment_assignment_filter(self):
        f = filters.PaymentsAssignmentsFilter(self.request, {"user_assignment": "empty"}, UserProfile, None)
        q = f.queryset(self.request, Payment.objects.all())
        self.assertEqual(q.count(), 1)

    def test_payment_assignment_filter_without_query(self):
        f = filters.PaymentsAssignmentsFilter(self.request, {}, UserProfile, None)
        q = f.queryset(self.request, Payment.objects.all())
        self.assertEqual(q.count(), 6)

    def test_user_condition_filter(self):
        f = filters.UserConditionFilter(self.request, {"user_condition": 2}, UserProfile, None)
        q = f.queryset(self.request, UserInCampaign.objects.all())
        self.assertEqual(q.count(), 4)

    def test_user_condition_filter_without_query(self):
        f = filters.UserConditionFilter(self.request, {}, UserProfile, None)
        q = f.queryset(self.request, UserInCampaign.objects.all())
        self.assertEqual(q.count(), 4)

    def test_active_camaign_filter_no(self):
        f = filters.ActiveCampaignFilter(self.request, {"active": "no"}, UserProfile, None)
        q = f.queryset(self.request, Event.objects.all())
        self.assertEqual(q.count(), 0)

    def test_active_camaign_filter_yes(self):
        f = filters.ActiveCampaignFilter(self.request, {"active": "yes"}, UserProfile, None)
        q = f.queryset(self.request, Event.objects.all())
        self.assertEqual(q.count(), 3)

    def test_active_camaign_filter_yes_without_query(self):
        f = filters.ActiveCampaignFilter(self.request, {}, UserProfile, None)
        q = f.queryset(self.request, Event.objects.all())
        self.assertEqual(q.count(), 3)

    def test_show_payments_by_year_blank(self):
        m = MagicMock()
        admin.show_payments_by_year(m, self.request, UserInCampaign.objects.all())
        m.message_user.assert_called_once_with(self.request, '2016: 480<br/>TOT.: 480')

    def test_email_filter(self):
        f = filters.EmailFilter(self.request, {}, UserProfile, None)
        q = f.queryset(self.request, UserProfile.objects.all())
        self.assertEqual(q.count(), 3)
