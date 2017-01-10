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

from django.conf import settings
from django.test.runner import DiscoverRunner


class AklubTestSuiteRunner(DiscoverRunner):
    class InvalidStringError(str):
        def __mod__(self, other):
            raise Exception("empty string")  # pragma: no cover
            return "!!!!!empty string!!!!!"  # pragma: no cover

    def __init__(self, *args, **kwargs):
        settings.TEMPLATES[0]['OPTIONS']['string_if_invalid'] = self.InvalidStringError("%s")
        super().__init__(*args, **kwargs)
