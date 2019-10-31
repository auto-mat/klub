from django.test import TestCase
from django.urls import reverse

from freezegun import freeze_time

from helpdesk.query import query_to_base64

from model_mommy import mommy

from .recipes import donor_payment_channel_recipe, user_profile_recipe
from .test_admin import CreateSuperUserMixin


class TimelineTest(CreateSuperUserMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.superuser)

    @freeze_time("2017-5-1")
    def test_timeline(self):
        foo_user = user_profile_recipe.make(id=2978, first_name="Foo", email="foo@bar.cz")
        foo_user_pc = donor_payment_channel_recipe.make(user=foo_user)
        mommy.make("aklub.Payment", amount=350, date="2016-01-02", user_donor_payment_channel=foo_user_pc, type="cash")
        mommy.make("aklub.Interaction", user=foo_user, subject="interaction subject")
        urlsafe_query = query_to_base64({
            'search_string': 'foo@bar.cz',
        })
        address = reverse('helpdesk:timeline_ticket_list', args=[urlsafe_query])
        response = self.client.get(address)
        self.assertEqual(response.json()['events'][0]['text']['headline'], 'interaction subject')
        self.assertEqual(response.json()['events'][1]['text']['headline'], '350 Kč')
