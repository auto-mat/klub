from settings import *  # noqa
from settings import ALLOWED_HOSTS, INSTALLED_APPS, LOGGING, MIDDLEWARE, TEMPLATES

INSTALLED_APPS += ("debug_toolbar",)

MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)

INTERNAL_IPS = [
    "127.0.0.1",
]


def custom_show_toolbar(request):
    return True


SHOW_TOOLBAR_CALLBACK = custom_show_toolbar

ALLOWED_HOSTS += [
    "localhost",
    "0.0.0.0",
    "127.0.0.1",
]


EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Make log in execution directory when testing
LOGGING["handlers"]["logfile"]["filename"] = "aklub.log"

CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 60
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
X_FRAME_OPTIONS = "ALLOW"

CORS_ORIGIN_ALLOW_ALL = True
