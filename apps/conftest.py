import datetime

from aklub.models import AdministrativeUnit, UserProfile

from django.conf import settings

from oauth2_provider.models import AccessToken, Application

import pytest

from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture(scope='function')
def administrative_unit_1(userprofile_superuser_2):
    au = AdministrativeUnit.objects.create(
        name="Auto*mat",
        slug="automat",
        street="street",
        city="he",
        gps_latitude=51.15151,
        gps_longitude=45.11515,
        zip_code="000 00",
        web_url="www.smth.eu",
        from_email_address="auto@mat.cz",
        telephone="+420123456789",
        president=userprofile_superuser_2,
        manager=userprofile_superuser_2,
    )
    yield au
    au.delete()


@pytest.fixture(scope='function')
def userprofile_superuser_2():
    user = UserProfile.objects.create(
        username="admin_2",
        first_name="admin_2",
        last_name="admin_2",
        is_staff=True,
        is_superuser=True,
    )
    yield user
    user.delete()


@pytest.fixture(scope='function')
def userprofile_superuser_1(administrative_unit_1):
    user = UserProfile.objects.create(
        username="admin",
        first_name="admin_first",
        last_name="admin_last",
        is_staff=True,
        is_superuser=True,
    )
    user.administrated_units.add(administrative_unit_1)
    yield user
    user.delete()


@pytest.fixture(scope='function')
def application_api_access():
    app = Application.objects.create(
         name="Test Application",
         client_type=Application.CLIENT_CONFIDENTIAL,
         authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
    )
    AccessToken.objects.create(
        token='foo',
        application=app,
        expires=datetime.datetime.now() + datetime.timedelta(days=999),
        scope=" ".join(settings.OAUTH2_PROVIDER['SCOPES'].keys()),
    )
    yield app
    app.delete()


@pytest.fixture(scope='function')
def app_request(application_api_access):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Bearer foo')
    yield client
