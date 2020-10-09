# Django settings for klub project.
import os
import sys

import raven


def normpath(*args):
    return os.path.normpath(os.path.abspath(os.path.join(*args)))


PROJECT_ROOT = normpath(__file__, "..", "..", "..")
BASE_DIR = PROJECT_ROOT

sys.path.append(normpath(PROJECT_ROOT, "project"))
sys.path.append(normpath(PROJECT_ROOT, "apps"))

DEBUG = os.environ.get('AKLUB_DEBUG', False) in (True, "True")
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DATABASE_NAME', ''),
        'USER': os.environ.get('DATABASE_USER', ''),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
        'HOST': os.environ.get('DATABASE_HOST', ''),
        'PORT': os.environ.get('DATABASE_PORT', ''),
    },
}

SECRET_KEY = os.environ.get('SECRET_KEY', '')

SERVER_EMAIL = ""
try:
    SERVER_EMAIL = os.environ['AKLUB_SERVER_EMAIL']
except KeyError:
    pass

DEFAULT_FROM_EMAIL = ""
try:
    DEFAULT_FROM_EMAIL = os.environ['AKLUB_DEFAULT_FROM_EMAIL']
except KeyError:
    pass

AKLUB_ADMINS = os.environ.get('AKLUB_ADMINS', '')
if AKLUB_ADMINS:
    ADMINS = [[s.strip() for s in admin.split(",")] for admin in AKLUB_ADMINS.strip().split("\n")]
    MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Prague'
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'cs'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.environ.get('AKLUB_MEDIA_ROOT', normpath(PROJECT_ROOT, 'data'))

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/upload/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.environ.get('AKLUB_STATIC_ROOT', normpath(PROJECT_ROOT, 'static'))

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/media/'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'djangobower.finders.BowerFinder',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            normpath(PROJECT_ROOT, 'apps/aklub/templates'),
            normpath(PROJECT_ROOT, 'apps/interactions/templates'),
        ],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': (
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                "sekizai.context_processors.sekizai",
            ),
            'loaders': (
                "admin_tools.template_loaders.Loader",
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ),
            'debug': DEBUG,
        },
    },
]

try:
    RELEASE = raven.fetch_git_sha(PROJECT_ROOT)
except raven.exceptions.InvalidGitRepository:
    RELEASE = os.getenv('HEROKU_SLUG_COMMIT')

RAVEN_CONFIG = {
    'dsn': os.environ.get('AKLUB_RAVEN_DNS', ''),
    'release': RELEASE,
}

MIDDLEWARE = (
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'author.middlewares.AuthorDefaultBackendMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
)

DATA_UPLOAD_MAX_NUMBER_FIELDS = None  # To allow more fields in administration

CORS_ORIGIN_WHITELIST = [
    'https://vyzva.auto-mat.cz',
]

if 'AKLUB_CORS_ORIGIN_WHITELIST' in os.environ:
    CORS_ORIGIN_WHITELIST += os.environ.get('AKLUB_CORS_ORIGIN_WHITELIST').split(',')

REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379')

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL + "/0",
        "KEY_PREFIX": 'aklub_default',
        "TIMEOUT": None,
    },
}

LOCALE_PATHS = [
    normpath(PROJECT_ROOT, 'apps/aklub/locale'),
]

USE_L10N = True

ROOT_URLCONF = 'urls'

INSTALLED_APPS = (
    'polymorphic',
    'django_grapesjs',
    'django.contrib.admindocs',
    'admin_tools_stats',
    'admin_tools',
    'admin_tools.theming',
    'admin_tools.menu',
    'admin_tools.dashboard',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django_nyt.apps.DjangoNytConfig',
    'stdimage',
    'dbbackup',
    'bootstrapform',
    'bootstrap4form',
    'django_extensions',
    'django_wysiwyg',
    'tinymce',
    'chart_tools',
    'markdown_deux',
    'post_office',
    'raven.contrib.django.raven_compat',
    'import_export',
    'import_export_celery',
    'import_export_celery_edit',
    'corsheaders',
    'daterange_filter',
    'admin_numeric_filter',
    'computedfields',
    'related_admin',
    'adminactions',
    'djangobower',
    'django_nvd3',
    'adminfilters',
    'advanced_filters',
    'aklub',
    'interactions',
    'helpdesk',
    'pdf_storage',
    'django_celery_beat',
    'django_celery_monitor',
    'djcelery_email',
    'nested_admin',
    'smmapdfs',
    'smmapdfs_edit',
    'repolinks',
    'mptt',
    'sekizai',
    'sorl.thumbnail',
    'wiki.apps.WikiConfig',
    'wiki.plugins.attachments.apps.AttachmentsConfig',
    'wiki.plugins.notifications.apps.NotificationsConfig',
    'wiki.plugins.images.apps.ImagesConfig',
    'wiki.plugins.macros.apps.MacrosConfig',
    'colorfield',
    'flexible_filter_conditions.apps.FlexibleFilterConditionsConfig',
    'rest_framework',
    'drf_yasg',
    'oauth2_provider',
    "account",
    "pinax.invitations",
    "pinax.teams",
    "reversion",
)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [ # noqa
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ],
}
OAUTH2_PROVIDER = {
    # sec * minutes * 24 =  24 hours * 1 year
    'ACCESS_TOKEN_EXPIRE_SECONDS': 60 * 60 * 24 * 365,
    # this is the list of available scopes
    # TODO: shoud be added by each application
    'SCOPES': {
        'read': 'Read scope',
        'write': 'Write scope',
        'can_create_profiles': 'Can create profiles by API',
        'can_check_if_exist': 'Can check slugs',
        'can_create_interactions': 'Can create interactions by API',
        'can_check_last_payments': 'Can check payments in dpch',
        'can_create_credit_card_payment': 'Can create credit card payment',
    },
    'OAUTH2_BACKEND_CLASS': 'oauth2_provider.oauth2_backends.JSONOAuthLibCore',

}

FLEXIBLE_FILTER_CONDITIONS_FIELD_MAP = {
    'User': ('aklub.models', 'User'),
    'Profile': ('aklub.models', 'Profile'),
    'User.userchannels.payment': ('aklub.models', 'Payment'),
    'User.userchannels.last_payment': ('aklub.models', 'Payment'),
    'User.userchannels': ('aklub.models', 'DonorPaymentChannel'),
}


BOWER_INSTALLED_APPS = (
    'jquery#3.4.1',
    'jquery-ui#~1.12.1',
    'd3#3.3.13',
    'nvd3#1.7.1',
)

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',

    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

EMAIL_BACKEND = 'post_office.EmailBackend'

ADMIN_TOOLS_INDEX_DASHBOARD = 'aklub.dashboard.AklubIndexDashboard'
ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'aklub.dashboard.AklubAppIndexDashboard'

UPLOAD_PATH = '/upload/'

DJANGO_WYSIWYG_FLAVOR = "tinymce_advanced_noentities"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s',
        },
        'simple': {
            'format': '%(levelname)s %(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
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
        },
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
        },
    },
}

ALLOWED_HOSTS = os.environ.get('AKLUB_ALLOWED_HOSTS', '').split(':')
AKLUB_CORS_ORIGIN_REGEX_WHITELIST = os.environ.get('AKLUB_CORS_ORIGIN_REGEX_WHITELIST', '').split(':')

TEST_RUNNER = 'aklub.tests.AklubTestSuiteRunner'

MIGRATION_MODULES = {
    'auth': 'local_migrations.migrations_auth',
    'admin': 'local_migrations.migrations_admin',
    'advanced_filters': 'local_migrations.migrations_advanced_filters',
    'menu': 'local_migrations.migrations_admin_tools.menu',
    'dashboard': 'local_migrations.migrations_admin_tools.dashboard',
    'helpdesk': 'local_migrations.migrations_helpdesk',
    'import_export_celery': 'local_migrations.migrations_import_export_celery',
}

AUTH_USER_MODEL = "aklub.Profile"

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

HELPDESK_DEFAULT_SETTINGS = {
    'use_email_as_submitter': True,
    'email_on_ticket_assign': True,
    'email_on_ticket_change': True,
    'login_view_ticketlist': True,
    'email_on_ticket_apichange': True,
    'preset_replies': True,
    'tickets_per_page': 25,
}

# Should the public web portal be enabled?
HELPDESK_VIEW_A_TICKET_PUBLIC = False
HELPDESK_SUBMIT_A_TICKET_PUBLIC = True
HELPDESK_STAFF_ONLY_TICKET_OWNERS = True

HELPDESK_PUBLIC_TICKET_PRIORITY = 3
HELPDESK_PUBLIC_TICKET_DUE_DATE = ''

# Should the Knowledgebase be enabled?
HELPDESK_KB_ENABLED = True

# Instead of showing the public web portal first,
# we can instead redirect users straight to the login page.
HELPDESK_REDIRECT_TO_LOGIN_BY_DEFAULT = False


def get_helpdesk_query_class():
    from aklub.timeline import Query
    return Query


HELPDESK_QUERY_CLASS = get_helpdesk_query_class

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/login/'

CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 60
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

BROKER_URL = os.environ.get('REDIS_URL', 'redis://redis')
SMMAPDFS_CELERY = True


def get_user_profile_resource():
    from aklub.admin import UserProfileResource
    return UserProfileResource


def get_company_profile_resource():
    from aklub.admin import CompanyProfileResource
    return CompanyProfileResource


def get_donor_payment_channel_resource():
    from aklub.admin import DonorPaymentChannelResource
    return DonorPaymentChannelResource


def get_interaction_resource():
    from interactions.admin import InteractionResource
    return InteractionResource


def get_payment_channel_resource():
    from aklub.admin import PaymentResource
    return PaymentResource


IMPORT_EXPORT_CELERY_MODELS = {
    "User profile": {
        'app_label': 'aklub',
        'model_name': 'UserProfile',
        'resource': get_user_profile_resource,
    },
    "Company profile": {
        'app_label': 'aklub',
        'model_name': 'CompanyProfile',
        'resource': get_company_profile_resource,
    },
    "Donor Payment Channel": {
        'app_label': 'aklub',
        'model_name': 'DonorPaymentChannel',
        'resource': get_donor_payment_channel_resource,
    },
    "Interaction": {
        'app_label': 'interactions',
        'model_name': 'Interaction',
        'resource': get_interaction_resource,
    },
    "Payments": {
        'app_label': 'aklub',
        'model_name': 'payment',
        'resource': get_payment_channel_resource,
    },
}

# Django - wiki settings
SITE_ID = 1
WIKI_ACCOUNT_SIGNUP_ALLOWED = False
WIKI_ACCOUNT_HANDLING = False
WIKI_ANONYMOUS = False
WIKI_CAN_READ = lambda _, user: user.is_staff  # noqa

# django server variables
WEB_URL = os.environ.get('WEB_URL', '')
SITE_NAME = os.environ.get('SITE_NAME', '')

# django admin action ignored_fields
UPDATE_ACTION_IGNORED_FIELDS = {
    'aklub': {
            'userprofile': ['is_staff', 'is_superuser', 'user_permissions', 'groups'],
            'companyprofile': ['is_staff', 'is_superuser', 'user_permissions', 'groups'],
    },
}
MERGE_ACTION_IGNORED_FIELDS = {
    'aklub': {
            'userprofile': ['is_staff', 'is_superuser', 'user_permissions', 'groups'],
            'companyprofile': ['is_staff', 'is_superuser', 'user_permissions', 'groups'],
    },
}
