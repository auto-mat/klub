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

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from .. import admin, filters
from ..models import Campaign, Payment, UserInCampaign


class FilterTests(TestCase):
    fixtures = ['conditions', 'users', 'communications']

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            username='admin',
            email='test_user@test_user.com',
            password='admin',
        )
        self.client.force_login(self.user)
        self.request = self.factory.get("")

    def test_payment_assignment_filter(self):
        f = filters.PaymentsAssignmentsFilter(self.request, {"user_assignment": "empty"}, User, None)
        q = f.queryset(self.request, Payment.objects.all())
        self.assertEquals(q.count(), 1)

    def test_user_condition_filter(self):
        f = filters.UserConditionFilter(self.request, {"user_condition": 2}, User, None)
        q = f.queryset(self.request, UserInCampaign.objects.all())
        self.assertEquals(q.count(), 4)

    def test_active_camaign_filter_no(self):
        f = filters.ActiveCampaignFilter(self.request, {"active": "no"}, User, None)
        q = f.queryset(self.request, Campaign.objects.all())
        self.assertEquals(q.count(), 0)

    def test_active_camaign_filter_yes(self):
        f = filters.ActiveCampaignFilter(self.request, {"active": "yes"}, User, None)
        q = f.queryset(self.request, Campaign.objects.all())
        self.assertEquals(q.count(), 3)

    def test_email_filter(self):
        f = filters.EmailFilter(self.request, {}, User, None)
        q = f.queryset(self.request, User.objects.all())
        self.assertEquals(q.count(), 4)

    def test_email_filter_duplicate(self):
        f = filters.EmailFilter(self.request, {"email": "duplicate"}, User, None)
        q = f.queryset(self.request, User.objects.all())
        self.assertEquals(q.count(), 0)

    def test_email_filter_blank(self):
        f = filters.EmailFilter(self.request, {"email": "blank"}, User, None)
        q = f.queryset(self.request, User.objects.all())
        self.assertEquals(q.count(), 0)

    def test_show_payments_by_year_blank(self):
        m = MagicMock()
        admin.show_payments_by_year(m, self.request, UserInCampaign.objects.all())
        m.message_user.assert_called_once_with(self.request, '2016: 480<br/>TOT.: 480')
