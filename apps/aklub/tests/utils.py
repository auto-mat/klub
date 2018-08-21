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
import django


def print_response(response):
    with open("response.html", "w") as f:  # pragma: no cover
        f.write(response.content.decode())  # pragma: no cover


ICON_FALSE = '<img src="/media/admin/img/icon-no.svg" alt="False"%s>' % (' /' if django.VERSION < (2, 1) else '')
ICON_UNKNOWN = '<img src="/media/admin/img/icon-unknown.svg" alt="None"%s>' % (' /' if django.VERSION < (2, 1) else '')
