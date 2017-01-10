# -*- coding: utf-8 -*-
# Author: Petr Dlouhý <petr.dlouhy@emial.cz>
#
# Copyright (C) 2010 o.s. Auto*Mat
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

from .base import *  # noqa
from .base import LOGGING

DEBUG = True

POST_OFFICE = {
    'BACKENDS': {
        'default': 'django.core.mail.backends.filebased.EmailBackend',
    },
}

EMAIL_FILE_PATH = '/tmp/aklub-emails'

LOGGING['handlers']['logfile']['filename'] = "aklub.log"

CORS_ORIGIN_ALLOW_ALL = True
