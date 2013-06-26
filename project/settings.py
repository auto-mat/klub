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

# some johnny settings
#CACHES = {
#    'default' : dict(
#        BACKEND = 'johnny.backends.memcached.MemcachedCache',
#        LOCATION = ['127.0.0.1:11211'],
#        JOHNNY_CACHE = True,
#    )
#}
#JOHNNY_MIDDLEWARE_KEY_PREFIX='jc_aklub'

LOCALE_PATHS = [
    normpath(PROJECT_ROOT, 'apps/aklub/locale'),
]

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    normpath(PROJECT_ROOT, 'apps/aklub/templates'),
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
    'south',
    'bootstrapform',
    'django_extensions',
    'django_wysiwyg',
    'tinymce',
    'admin_user_stats',
    'chart_tools',
    'aklub'
)

ADMIN_TOOLS_INDEX_DASHBOARD = 'aklub.dashboard.AklubIndexDashboard'
ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'aklub.dashboard.AklubAppIndexDashboard'

UPLOAD_PATH = '/upload/'

DJANGO_WYSIWYG_FLAVOR = "tinymce_advanced" 

# import local settings
try:
    from settings_local import *
except ImportError:
    pass
