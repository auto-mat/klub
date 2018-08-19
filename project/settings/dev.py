from settings import *  # noqa
from settings import LOGGING

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = ()
MANAGERS = ADMINS

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SECRET_KEY = ''

# Make log in execution directory when testing
LOGGING['handlers']['logfile']['filename'] = "aklub.log"

CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 60
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
X_FRAME_OPTIONS = 'ALLOW'

ALLOWED_HOSTS = [
    'localhost',
]
