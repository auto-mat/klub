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


class TestPersonName(TestCase):
    """ Test Result.person_name """

    def test_result_str(self):
        user_profile = mommy.make(
            "aklub.UserProfile",
            first_name="Foo",
            last_name="Name",
        )
        result = mommy.make(
            "aklub.Payment",
            campaign__name="Foo campaign",
            user_donor_payment_channel__user=user_profile,
            user_donor_payment_channel__bank_account__id=1,
        )
        self.assertEqual(result.person_name(), 'Name Foo')

    def test_no_user(self):
        """ Test with no user set """
        result = mommy.make(
            "aklub.Payment",
            campaign__name="Foo campaign",
        )
        self.assertEqual(result.person_name(), None)
