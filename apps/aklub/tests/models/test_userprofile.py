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
            user__first_name="Foo",
            user__last_name="User",
        )
        self.assertEquals(str(t), "User Foo")

    def test_username(self):
        """ Test, that __str__ works, when only username is set """
        t = mommy.make(
            "aklub.UserProfile",
            user__username="foo_user",
        )
        self.assertEquals(str(t), "foo_user")

    def test_id(self):
        """ Test, that __str__ works, when no user is set """
        t = mommy.prepare(
            "aklub.UserProfile",
            user=None,
            id=1,
        )
        self.assertEquals(str(t), "UserProfile: 1")
