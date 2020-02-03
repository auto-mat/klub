import os

import django_heroku

from .base import *  # noqa

ALLOWED_HOSTS = [
    "klub.auto-mat.cz",
    os.environ.get('HEROKU_APP_URL'),
]

SITE_ID = 1

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'eu-west-1')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'klub')
AWS_QUERYSTRING_EXPIRE = os.environ.get('AWS_QUERYSTRING_EXPIRE', 60 * 60 * 24 * 365 * 10)
AWS_DEFAULT_ACL = "private"


if AWS_ACCESS_KEY_ID:
    THUMBNAIL_DEFAULT_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    POST_OFFICE = {
        'BACKENDS': {
            'default': 'django_ses.SESBackend',
        },
    }
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
