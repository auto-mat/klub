import django_heroku

from .cloud import *  # noqa

django_heroku.settings(locals())
