# Django settings for klub project.
import os
import sys

normpath = lambda *args: os.path.normpath(os.path.abspath(os.path.join(*args)))
PROJECT_ROOT = normpath(__file__, "..", "..")

sys.path.append(normpath(PROJECT_ROOT, "project"))
sys.path.append(normpath(PROJECT_ROOT, "apps"))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Hynek Hanke', 'hynek.hanke@auto-mat.cz'),
#    ('Vaclav Rehak', 'vrehak@baf.cz'),
)

MANAGERS = ADMINS

DATABASES = {
        'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': 'klub',
                'USER': 'django',
                'PASSWORD': 'osmiznak',
                'HOST': 'localhost',
                'PORT': '',
        },
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Prague'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'cs-CZ'

SITE_ID = 3

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = normpath(PROJECT_ROOT, 'data')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/upload/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = normpath(PROJECT_ROOT, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/media/'

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
TEMPLATE_CONTEXT_PROCESSORS += (
     'django.core.context_processors.request',
     'django.core.context_processors.media',
     'django.contrib.messages.context_processors.messages',
)

MIDDLEWARE_CLASSES = (
#    'johnny.middleware.LocalStoreClearMiddleware',  # disabled for django 1.4
#    'johnny.middleware.QueryCacheMiddleware', # disabled for django 1.4
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
)

CACHES = {
    'default' : dict(
        BACKEND = 'django.core.cache.backends.memcached.MemcachedCache',
        LOCATION = ['127.0.0.1:11211'],
		KEY_PREFIX = 'aklub',
    )
}

LOCALE_PATHS = [
    normpath(PROJECT_ROOT, 'apps/aklub/locale'),
]

USE_L10N = True

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    normpath(PROJECT_ROOT, 'apps/aklub/templates'),
    normpath(PROJECT_ROOT, 'env/lib/python2.6/site-packages/debug_toolbar/templates'),
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'admin_tools',
    'admin_tools.theming',
    'admin_tools.menu',
    'admin_tools.dashboard',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.formtools',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'stdimage',
    'bootstrapform',
    'django_extensions',
    'django_wysiwyg',
    'tinymce',
    'admin_user_stats',
    'chart_tools',
    'massadmin',
    'import_export',
    'debug_toolbar',
    'daterange_filter',
    'aklub'
)

ADMIN_TOOLS_INDEX_DASHBOARD = 'aklub.dashboard.AklubIndexDashboard'
ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'aklub.dashboard.AklubAppIndexDashboard'

UPLOAD_PATH = '/upload/'

DJANGO_WYSIWYG_FLAVOR = "tinymce_advanced_noentities"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
         'require_debug_false': {
             '()': 'django.utils.log.RequireDebugFalse'
         }
     },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'logfile': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': "/var/log/django/aklub.log",
            'backupCount': 50,
            'maxBytes': 10000000,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': {
        'django': { 
            'handlers': ['console', 'logfile'],
            'propagate': True, 
            'level': 'INFO',
        },
        'django.request': { 
            'handlers': ['mail_admins', 'logfile'],
            'level': 'ERROR',
            'propagate': False,
        },
        'aklub': {
            'handlers': ['console', 'mail_admins', 'logfile'],
            'level': 'DEBUG', 
        }
    }
}

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# import local settings
try:
    from settings_local import *
except ImportError:
    pass
