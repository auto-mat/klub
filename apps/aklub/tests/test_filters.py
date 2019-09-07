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
from ..models import DonorPaymentChannel, Event, Payment, Profile


class FilterTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("")


class FilterTests(FilterTestCase):
    def test_email_filter_blank(self):
        for model in Profile.__subclasses__():
            model_name = model._meta.object_name
            profile = mommy.make(model_name, email="", first_name="Foo", last_name="")
            f = filters.EmailFilter(self.request, {"email": "blank"}, Profile, None)
            q = f.queryset(self.request, Profile.objects.all())
            self.assertQuerysetEqual(q, ["<{}: Foo>".format(model_name)])
            profile.delete()

    def test_email_filter_format(self):
        for model in Profile.__subclasses__():
            model_name = model._meta.object_name
            profile = mommy.make(model_name, email='foo', first_name="Foo", last_name="")
            f = filters.EmailFilter(self.request, {"email": "email-format"}, Profile, None)
            q = f.queryset(self.request, Profile.objects.all())
            self.assertQuerysetEqual(q, ["<{}: Foo>".format(model_name)])
            profile.delete()

    def test_telephone_filter_duplicate_blank(self):
        f = filters.TelephoneFilter(self.request, {"telephone": "duplicate"}, Profile, None)
        q = f.queryset(self.request, Profile.objects.all())
        self.assertQuerysetEqual(q, [], ordered=False)

    def test_telephone_filter_duplicate(self):
        for model in Profile.__subclasses__():
            model_name = model._meta.object_name
            profile1 = mommy.make(model_name, telephone='123456', first_name="Foo", last_name="")
            mommy.make('Telephone', telephone='123456', user=profile1)
            profile2 = mommy.make(model_name, telephone='123456', first_name="Bar", last_name="")
            mommy.make('Telephone', telephone='123456', user=profile2)
            f = filters.TelephoneFilter(self.request, {"telephone": "duplicate"}, Profile, None)
            q = f.queryset(self.request, Profile.objects.all())
            self.assertQuerysetEqual(
                q,
                [
                    "<{}: Foo>".format(model_name),
                    "<{}: Bar>".format(model_name),
                ],
                ordered=False,
            )
            profile1.delete()
            profile2.delete()

    def test_telephone_filter_blank(self):
        for model in Profile.__subclasses__():
            model_name = model._meta.object_name
            profile = mommy.make(model_name, telephone=None, first_name="Foo", last_name="")
            f = filters.TelephoneFilter(self.request, {"telephone": "blank"}, Profile, None)
            q = f.queryset(self.request, Profile.objects.all())
            self.assertQuerysetEqual(q, ["<{}: Foo>".format(model_name)])
            profile.delete()

    def test_telephone_filter_blank_foreign(self):
        for model in Profile.__subclasses__():
            model_name = model._meta.object_name
            profile = mommy.make(model_name, first_name="Foo", last_name="")
            mommy.make('Telephone', user=profile, telephone='')
            f = filters.TelephoneFilter(self.request, {"telephone": "blank"}, Profile, None)
            q = f.queryset(self.request, Profile.objects.all())
            self.assertQuerysetEqual(q, ["<{}: Foo>".format(model_name)])
            profile.delete()

    def test_telephone_filter_format(self):
        for model in Profile.__subclasses__():
            model_name = model._meta.object_name
            profile = mommy.make(model_name, telephone='1111', first_name="Foo", last_name="")
            f = filters.TelephoneFilter(self.request, {"telephone": "bad-format"}, Profile, None)
            q = f.queryset(self.request, Profile.objects.all())
            self.assertQuerysetEqual(q, ["<{}: Foo>".format(model_name)])
            profile.delete()

    def test_telephone_filter_without_query(self):
        for model in Profile.__subclasses__():
            model_name = model._meta.object_name
            profile = mommy.make(model_name, telephone='1111', first_name="Foo", last_name="")
            f = filters.TelephoneFilter(self.request, {}, Profile, None)
            q = f.queryset(self.request, Profile.objects.all())
            self.assertQuerysetEqual(q, ["<{}: Foo>".format(model_name)])
            profile.delete()

    def test_name_filter_duplicate(self):
        for model in Profile.__subclasses__():
            model_name = model._meta.object_name
            profile1 = mommy.make(model_name, first_name="Foo", last_name="")
            profile2 = mommy.make(model_name, first_name="Foo", last_name="")
            f = filters.NameFilter(self.request, {"name": "duplicate"}, Profile, None)
            q = f.queryset(self.request, Profile.objects.all())
            self.assertQuerysetEqual(
                q,
                [
                    "<{}: Foo>".format(model_name),
                    "<{}: Foo>".format(model_name),
                ],
                ordered=False,
            )
            profile1.delete()
            profile2.delete()

    def test_name_filter_blank(self):
        for model in Profile.__subclasses__():
            model_name = model._meta.object_name
            profile = mommy.make(model_name, first_name="", last_name="", username="foo_username")
            f = filters.NameFilter(self.request, {"name": "blank"}, Profile, None)
            q = f.queryset(self.request, Profile.objects.all())
            self.assertQuerysetEqual(q, ["<{}: foo_username>".format(model_name)])
            profile.delete()

    def test_name_filter_without_query(self):
        for model in Profile.__subclasses__():
            model_name = model._meta.object_name
            profile = mommy.make(model_name, first_name="", last_name="", username="foo_username")
            f = filters.NameFilter(self.request, {}, Profile, None)
            q = f.queryset(self.request, Profile.objects.all())
            self.assertQuerysetEqual(q, ["<{}: foo_username>".format(model_name)])
            profile.delete()


class FixtureFilterTests(FilterTestCase):
    fixtures = ['conditions', 'users', 'communications']

    def test_payment_assignment_filter(self):
        f = filters.PaymentsAssignmentsFilter(self.request, {"user_assignment": "empty"}, Profile, None)
        q = f.queryset(self.request, Payment.objects.all())
        self.assertEqual(q.count(), 1)

    def test_payment_assignment_filter_without_query(self):
        f = filters.PaymentsAssignmentsFilter(self.request, {}, Profile, None)
        q = f.queryset(self.request, Payment.objects.all())
        self.assertEqual(q.count(), 6)

    def test_user_condition_filter(self):
        f = filters.UserConditionFilter(self.request, {"user_condition": 2}, Profile, None)
        q = f.queryset(self.request, DonorPaymentChannel.objects.all())
        self.assertEqual(q.count(), 4)

    def test_user_condition_filter_without_query(self):
        f = filters.UserConditionFilter(self.request, {}, Profile, None)
        q = f.queryset(self.request, DonorPaymentChannel.objects.all())
        self.assertEqual(q.count(), 4)

    def test_active_camaign_filter_no(self):
        f = filters.ActiveCampaignFilter(self.request, {"active": "no"}, Profile, None)
        q = f.queryset(self.request, Event.objects.all())
        self.assertEqual(q.count(), 0)

    def test_active_camaign_filter_yes(self):
        f = filters.ActiveCampaignFilter(self.request, {"active": "yes"}, Profile, None)
        q = f.queryset(self.request, Event.objects.all())
        self.assertEqual(q.count(), 3)

    def test_active_camaign_filter_yes_without_query(self):
        f = filters.ActiveCampaignFilter(self.request, {}, Profile, None)
        q = f.queryset(self.request, Event.objects.all())
        self.assertEqual(q.count(), 3)

    def test_show_payments_by_year_blank(self):
        m = MagicMock()
        admin.show_payments_by_year(m, self.request, DonorPaymentChannel.objects.all())
        m.message_user.assert_called_once_with(self.request, '2016: 480<br/>TOT.: 480')

    def test_email_filter(self):
        f = filters.EmailFilter(self.request, {}, Profile, None)
        q = f.queryset(self.request, Profile.objects.all())
        self.assertEqual(q.count(), 3)
