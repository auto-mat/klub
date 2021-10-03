import datetime

from aklub.models import AdministrativeUnit, ProfileEmail, Telephone, UserProfile

from django.conf import settings
from django.core.files import File

from events.models import (
    Event,
    EventType,
    Location,
    OrganizationPosition,
    OrganizationTeam,
)

from oauth2_provider.models import AccessToken, Application

import pytest

from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture(scope="function")
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
        level="regional_center",
    )
    yield au
    au.delete()


@pytest.fixture(scope="function")
def administrative_unit_2():
    au = AdministrativeUnit.objects.create(
        name="Auto*mat - slovakia",
        slug="automat_slovakia",
    )
    yield au
    au.delete()


@pytest.fixture(scope="function")
def telephone_2(userprofile_superuser_2):
    telephone = Telephone.objects.create(
        telephone="655455564",
        is_primary=True,
        user=userprofile_superuser_2,
    )
    yield telephone
    telephone.delete()


@pytest.fixture(scope="function")
def profileemail_2(userprofile_superuser_2):
    email = ProfileEmail.objects.create(
        email="ho@ha.com",
        is_primary=True,
        user=userprofile_superuser_2,
    )
    yield email
    email.delete()


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
def application_api_access():
    app = Application.objects.create(
        name="Test Application",
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
    )
    AccessToken.objects.create(
        token="foo",
        application=app,
        expires=datetime.datetime.now() + datetime.timedelta(days=999),
        scope=" ".join(settings.OAUTH2_PROVIDER["SCOPES"].keys()),
    )
    yield app
    app.delete()


@pytest.fixture(scope="function")
def app_request(application_api_access):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer foo")
    yield client


@pytest.fixture(scope="function")
def location_1(administrative_unit_1):
    location = Location.objects.create(
        name="location_name",
        place="here",
        region="Prague",
        gps_latitude=52.15151,
        gps_longitude=35.11515,
    )
    yield location
    location.delete()


@pytest.fixture(scope="function")
def organization_position_1():
    location = OrganizationPosition.objects.create(
        name="position",
    )
    yield location
    location.delete()


@pytest.fixture(scope="function")
def organization_team_1(userprofile_superuser_2, organization_position_1, event_1):
    organization_team = OrganizationTeam.objects.create(
        position=organization_position_1,
        profile=userprofile_superuser_2,
        event=event_1,
    )
    yield organization_team
    organization_team.delete()


@pytest.fixture(scope="function")
def event_type_1(administrative_unit_1):
    event_type = EventType.objects.create(
        name="Event name",
        slug="event_name",
        description="some description",
        administrative_unit=administrative_unit_1,
    )
    yield event_type
    event_type.delete()


@pytest.fixture(scope="function")
def event_1(administrative_unit_1, event_type_1, location_1):
    event = Event.objects.create(
        name="event_name",
        slug="event_slug",
        date_from="2020-02-02",
        date_to="2021-03-03",
        program="monuments",
        indended_for="everyone",
        location=location_1,
        event_type=event_type_1,
        age_from=10,
        age_to=99,
        start_date="2020-03-01T00:00:00+01:00",
        participation_fee="120kc",
        entry_form_url="http://www.example.com",
        web_url="http://www.example.com",
        additional_question_1="he_1?",
        additional_question_2="he_2?",
        additional_question_3="he_3?",
        additional_question_4="he_4?",
        invitation_text_1="text_1",
        invitation_text_2="text_2",
        invitation_text_3="text_3",
        invitation_text_4="text_4",
        accommodation="under the sky",
        diet=["vegetarian"],
        looking_forward_to_you="some name_1 name_2",
        working_hours=3,
        main_photo=File(open("apps/aklub/test_data/empty_pdf.pdf", "rb")),
        public_on_web=True,
        contact_person_name="Tester Testerovič",
        contact_person_email="now@ds.com",
        contact_person_telephone="999888777",
    )
    event.administrative_units.add(administrative_unit_1)
    yield event
    event.delete()


@pytest.fixture(scope="function")
def event_2(administrative_unit_2):
    event = Event.objects.create(
        name="event_name_2",
        slug="event_slug_2",
        public_on_web=True,
    )
    event.administrative_units.add(administrative_unit_2)
    yield event
    event.delete()
