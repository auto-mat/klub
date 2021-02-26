import datetime

from django.conf import settings

from model_mommy import mommy

from oauth2_provider.models import Application


def app_login_mixin():
    app = mommy.make(
         'oauth2_provider.application',
         name="Test Application",
         client_type=Application.CLIENT_CONFIDENTIAL,
         authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
    )
    token = mommy.make(
        'oauth2_provider.accesstoken',
        token='foo',
        application=app,
        expires=datetime.datetime.now() + datetime.timedelta(days=999),
        scope=" ".join(settings.OAUTH2_PROVIDER['SCOPES'].keys()),
    )
    return token


def user_login_mixin():
    user = mommy.make("aklub.UserProfile", username='user_can_access')
    app = mommy.make(
         'oauth2_provider.application',
         name="Test Application",
         client_type=Application.CLIENT_CONFIDENTIAL,
         authorization_grant_type=Application.GRANT_PASSWORD,
    )

    mommy.make(
        'oauth2_provider.accesstoken',
        token='foo',
        application=app,
        expires=datetime.datetime.now() + datetime.timedelta(days=999),
        user=user,
    )
    return user
