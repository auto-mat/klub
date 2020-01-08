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
        unit = mommy.make('aklub.AdministrativeUnit')
        bank_acc = mommy.make('aklub.BankAccount', administrative_unit=unit)
        foo_user_pc = donor_payment_channel_recipe.make(user=foo_user, money_account=bank_acc)
        mommy.make("aklub.Payment", amount=350, date="2016-01-02", user_donor_payment_channel=foo_user_pc, type="cash")
        mommy.make("aklub.Interaction", user=foo_user, subject="interaction subject", administrative_unit=unit)
        # Search by email
        urlsafe_query = query_to_base64({
            'search_string': 'foo@bar.cz',
        })
        address = reverse('helpdesk:timeline_ticket_list', args=[urlsafe_query])
        response = self.client.get(address)
        self.assertEqual(response.json()['events'][1]['text']['headline'], '<p style="color:#000000;">interaction subject</p>')
        self.assertEqual(response.json()['events'][2]['text']['headline'], '<p style="color:#000000;">350 Kč</p>')
        # Search by pk
        urlsafe_query = query_to_base64({
            'search_profile_pks': [foo_user.pk],
        })
        address = reverse('helpdesk:timeline_ticket_list', args=[urlsafe_query])
        response = self.client.get(address)
        self.assertEqual(response.json()['events'][1]['text']['headline'], '<p style="color:#000000;">interaction subject</p>')
        self.assertEqual(response.json()['events'][2]['text']['headline'], '<p style="color:#000000;">350 Kč</p>')
