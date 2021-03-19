from aklub.models import AdministrativeUnit, UserProfile

import pytest


@pytest.fixture(scope='function')
def administrative_unit_1():
    au = AdministrativeUnit.objects.create(
        name="Auto*mat",
    )
    yield au
    au.delete()


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
