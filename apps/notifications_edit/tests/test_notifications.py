from api.tests.utils import app_login_mixin

from django.test import TestCase
from django.urls import reverse

from model_mommy import mommy


class ApiCreateNotificationTest(TestCase):
    """
    Test every module where notification is created (and how is created)
    """
    def setUp(self):
        app_login_mixin()
        unit = mommy.make('aklub.administrativeunit', name='test_unit')
        self.event = mommy.make('events.event', slug='event_slug', administrative_units=[unit, ])
        self.bank_acc = mommy.make('aklub.bankaccount', bank_account='11122/111', slug='bank_slug', administrative_unit=unit)
        self.user = mommy.make('aklub.UserProfile', administrated_units=[unit, ], is_superuser=True, is_staff=True)

    def test_wrong_crm_log(self):
        url = reverse('companyprofile_vs')
        header = {'Authorization': 'Bearer foo'}
        data = {
            'crn': '1234567',
            'name': 'company_name',
            'email': 'Company@Test.Com',
            'contact_first_name': 'tester',
            'contact_last_name': 'tester_last',
            'telephone': '111222333',
            'money_account': 'bank_slug',
            'event': 'event_slug',
            'amount': '111',
            'regular': True,
        }
        response = self.client.post(url, data=data, **header)
        self.assertEqual(response.status_code, 400)
        notifications = self.user.notifications.all()
        self.assertEqual(notifications.count(), 1)
        notif = notifications.first()
        self.assertEqual(notif.verb, 'Wrong format of crn')
        self.assertEqual(notif.description, 'User input was: 1234567 and was not create in system')
