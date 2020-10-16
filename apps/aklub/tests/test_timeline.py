import datetime

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
    def test_timeline_userprofile(self):
        foo_user = user_profile_recipe.make(id=2978, first_name="Foo", email="foo@bar.cz")
        unit = mommy.make('aklub.AdministrativeUnit')
        bank_acc = mommy.make('aklub.BankAccount', administrative_unit=unit)
        foo_user_pc = donor_payment_channel_recipe.make(user=foo_user, money_account=bank_acc)
        mommy.make("aklub.Payment", amount=350, date="2016-01-02", user_donor_payment_channel=foo_user_pc, type="cash")
        category = mommy.make("interactions.InteractionCategory", category='testcategory')
        int_type = mommy.make("interactions.InteractionType", name='testtype', category=category)
        mommy.make(
                "interactions.Interaction",
                type=int_type,
                user=foo_user,
                subject="interaction subject",
                date_from=datetime.datetime(2005, 7, 14, 12, 30),
                administrative_unit=unit,
        )

        # Search by id
        urlsafe_query = query_to_base64({
            'search_profile_pks': ['2978'],
        })
        address = reverse('helpdesk:timeline_ticket_list', args=[urlsafe_query])
        response = self.client.get(address)
        self.assertEqual(response.json()['events'][2]['text']['headline'], '<p style="color:#000000;">interaction subject</p>')
        self.assertEqual(response.json()['events'][3]['text']['headline'], '<p style="color:#000000;">350 Kč</p>')
        # Search by pk
        urlsafe_query = query_to_base64({
            'search_profile_pks': [foo_user.pk],
        })
        address = reverse('helpdesk:timeline_ticket_list', args=[urlsafe_query])
        response = self.client.get(address)
        self.assertEqual(response.json()['events'][2]['text']['headline'], '<p style="color:#000000;">interaction subject</p>')
        self.assertEqual(response.json()['events'][3]['text']['headline'], '<p style="color:#000000;">350 Kč</p>')

    def test_timeline_companyprofile(self):
        company = mommy.make('aklub.companyprofile', id=999, name='company_name', email="foo@bar.cz")
        unit = mommy.make('aklub.AdministrativeUnit')
        mommy.make('aklub.companycontact', email='email_company@gmail.com')
        bank_acc = mommy.make('aklub.BankAccount', administrative_unit=unit)
        foo_company_pc = donor_payment_channel_recipe.make(user=company, money_account=bank_acc)
        mommy.make("aklub.Payment", amount=958, date="2015-01-02", user_donor_payment_channel=foo_company_pc, type="cash")
        category = mommy.make("interactions.InteractionCategory", category='testcategory')
        int_type = mommy.make("interactions.InteractionType", name='test_company_type', category=category)
        mommy.make(
                "interactions.Interaction",
                type=int_type,
                user=company,
                subject="interaction company subject",
                date_from=datetime.datetime(2002, 7, 14, 12, 30),
                administrative_unit=unit,
        )

        # Search by id
        urlsafe_query = query_to_base64({
            'search_profile_pks': [company.id],
        })
        address = reverse('helpdesk:timeline_ticket_list', args=[urlsafe_query])
        response = self.client.get(address)
        self.assertEqual(response.json()['events'][2]['text']['headline'], '<p style="color:#000000;">interaction company subject</p>')
        self.assertEqual(response.json()['events'][3]['text']['headline'], '<p style="color:#000000;">958 Kč</p>')
        # Search by pk
        urlsafe_query = query_to_base64({
            'search_profile_pks': [company.pk],
        })
        address = reverse('helpdesk:timeline_ticket_list', args=[urlsafe_query])
        response = self.client.get(address)
        self.assertEqual(response.json()['events'][2]['text']['headline'], '<p style="color:#000000;">interaction company subject</p>')
        self.assertEqual(response.json()['events'][3]['text']['headline'], '<p style="color:#000000;">958 Kč</p>')
