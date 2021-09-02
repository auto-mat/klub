from django.test import TestCase
from django.urls import reverse

from model_mommy import mommy

from .utils import app_login_mixin, user_login_mixin


class LoginByClientCredentialsTest(TestCase):
    def setUp(self):
        self.token = app_login_mixin()

    def test_app_can_not_log_to_is_authenticated(self):
        """
        Check if 3rd application is logged by Client credentials => can not access IsAuthenticated perm
        """
        url = reverse("check_last_payment")
        header = {"Authorization": f"Bearer {self.token.token}"}
        response = self.client.get(url, **header)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "K této akci nemáte oprávnění.")


class LoginByUserPasswordTest(TestCase):
    def setUp(self):
        self.user = user_login_mixin()

    def test_user_can_not_log_to_scopes(self):
        """
        Check if user with password can not log to scopes based vies => missing scope
        """
        unit = mommy.make("aklub.AdministrativeUnit", name="test_unit")
        event = mommy.make(
            "events.event",
            slug="event_slug",
            administrative_units=[
                unit,
            ],
        )

        url = reverse("check_event", kwargs={"slug": f"{event.slug}"})
        header = {"Authorization": "Bearer foo"}
        response = self.client.get(url, **header)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "K této akci nemáte oprávnění.")
