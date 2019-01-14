import os

import django_heroku

from .base import *  # noqa

ALLOWED_HOSTS = [
    "klub.auto-mat.cz",
    os.environ.get('HEROKU_APP_URL')
]

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_S3_HOST = os.environ.get('AWS_S3_HOST', 's3-eu-west-1.amazonaws.com')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'klub')
AWS_QUERYSTRING_AUTH = os.environ.get('AWS_QUERYSTRING_AUTH', False)
AWS_QUERYSTRING_EXPIRE = os.environ.get('AWS_QUERYSTRING_EXPIRE', 60 * 60 * 24 * 365 * 10)

if AWS_ACCESS_KEY_ID:
    THUMBNAIL_DEFAULT_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    CELERY_EMAIL_BACKEND = os.environ.get('CELERY_EMAIL_BACKEND', 'django_ses.SESBackend')
    AWS_SES_REGION_NAME = 'eu-west-1'
    AWS_SES_REGION_ENDPOINT = 'email.eu-west-1.amazonaws.com'

    DBBACKUP_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    DBBACKUP_STORAGE_OPTIONS = {
        'access_key': AWS_ACCESS_KEY_ID,
        'secret_key': AWS_SECRET_ACCESS_KEY,
        'bucket_name': 'klub-dbbackup',
    }

LOGGING['handlers']['logfile']['filename'] = "aklub.log" # noqa

CORS_ORIGIN_REGEX_WHITELIST = (
   r'.*\.dopracenakole\.cz$',
   r'.*\.zazitmestojinak\.cz',
   r'.*\.nakrmteautomat\.cz$',
   r'.*\.auto-mat\.cz$',
)

django_heroku.settings(locals())
