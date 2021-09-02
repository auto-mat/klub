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
import os

from .base import *  # noqa
from .base import INSTALLED_APPS, LOGGING, MIDDLEWARE

DEBUG = True

POST_OFFICE = {
    "BACKENDS": {
        "default": "django.core.mail.backends.filebased.EmailBackend",
    },
}

if os.environ.get("AKLUB_DEBUG_TOOLBAR", False):
    INSTALLED_APPS += ("debug_toolbar",)

    MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)

    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda x: True,
    }

EMAIL_FILE_PATH = "/tmp/aklub-emails"

LOGGING["handlers"]["logfile"]["filename"] = "aklub.log"
WEB_URL = "https://www.test_url.com"
SITE_NAME = "site_name"

CORS_ORIGIN_ALLOW_ALL = True

CELERY_ALWAYS_EAGER = True

CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
