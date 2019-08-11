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

from model_mommy.recipe import Recipe, seq


donor_payment_channel_recipe = Recipe(
    "aklub.DonorPaymentChannel", 
    event__name="Foo campaign",
    userprofile__is_active=True,
    userprofile__username=seq("username"),
    userprofile__email=seq("test@email.cz"),
    VS=seq(1),
)

user_profile_recipe = Recipe(
    "aklub.UserProfile",
    is_active=True,
    username=seq("username"),
    email=seq("test@email.cz"),
)
