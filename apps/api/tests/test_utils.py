import json
from unittest.mock import patch

from api.utils import check_last_month_year_payment

from django.core.cache import cache
from django.test import TestCase, override_settings

from freezegun import freeze_time

from model_mommy import mommy


@freeze_time("2015-5-1")
class CheckLastMonthYearPaymentTest(TestCase):
    def setUp(self):
        self.user = mommy.make('aklub.UserProfile', username='Testeretes')
        cache.delete(f"{self.user.id}_paid_section")
        self.unit = mommy.make('aklub.administrativeunit', name='test_unit')
        self.event = mommy.make('events.event', slug='event_slug', administrative_units=[self.unit, ])
        self.bank_acc = mommy.make('aklub.bankaccount', bank_account='11122/111', slug='bank_slug', administrative_unit=self.unit)
        self.dpch = mommy.make('aklub.DonorPaymentChannel', event=self.event, money_account=self.bank_acc, VS=1111, user=self.user)

        self.api = mommy.make(
            'aklub.ApiAccount',
            project_name='test_project',
            project_id='22222',
            api_id='11111',
            api_secret='secret_hash',
            api_organization_id="123",
            event=self.event,
            administrative_unit=self.unit,
        )

    def _mock_darujme_url(self, mock_get):
        with open('apps/aklub/test_data/darujme_response.json') as json_file:
            mock_get.return_value.json.return_value = json.load(json_file)
            mock_get.return_value.status_code = 200

    @override_settings(SUM_LAST_YEAR_PAYMENTS=3000, SUM_LAST_MONTH_PAYMENTS=100)
    def test_payment_found_month(self):
        """
        Regular payment for last month accepted
        """
        mommy.make('aklub.Payment', date='2015-04-15', amount=100, user_donor_payment_channel=self.dpch)
        result = check_last_month_year_payment(self.user)
        self.assertTrue(result)

    @override_settings(SUM_LAST_YEAR_PAYMENTS=3000, SUM_LAST_MONTH_PAYMENTS=100)
    def test_payment_found_year(self):
        """
        Regular payment for last year accepted
        """
        mommy.make('aklub.Payment', date='2014-12-15', amount=1000, user_donor_payment_channel=self.dpch)
        mommy.make('aklub.Payment', date='2015-1-15', amount=2000, user_donor_payment_channel=self.dpch)
        result = check_last_month_year_payment(self.user)
        self.assertTrue(result)

    @override_settings(SUM_LAST_YEAR_PAYMENTS=3000, SUM_LAST_MONTH_PAYMENTS=100)
    def test_paymend_expired_year(self):
        """
        Regular payment for last month accepted, but not enought and last payment for year expired
        """
        mommy.make('aklub.Payment', date='2015-04-15', amount=50, user_donor_payment_channel=self.dpch)
        mommy.make('aklub.Payment', date='2012-04-15', amount=5000, user_donor_payment_channel=self.dpch)
        result = check_last_month_year_payment(self.user)
        self.assertFalse(result)

    @override_settings(SUM_LAST_YEAR_PAYMENTS=3000, SUM_LAST_MONTH_PAYMENTS=100)
    def test_paymend_expired_month(self):
        """
        Regular payment for last month expired
        """
        mommy.make('aklub.Payment', date='2015-02-15', amount=200, user_donor_payment_channel=self.dpch)
        result = check_last_month_year_payment(self.user)
        self.assertFalse(result)

    @override_settings(SUM_LAST_YEAR_PAYMENTS=3000, SUM_LAST_MONTH_PAYMENTS=100)
    def test_payment_cached(self):
        mommy.make('aklub.Payment', date='2015-05-15', amount=200, user_donor_payment_channel=self.dpch)
        result = check_last_month_year_payment(self.user)
        self.assertTrue(result)
        self.assertTrue(cache.get(f"{self.user.id}_paid_section"))

    @override_settings(SUM_LAST_YEAR_PAYMENTS=3000, SUM_LAST_MONTH_PAYMENTS=100)
    @patch('api.utils.requests.get')
    def test_darujme_found_payment(self, mock_get):
        self._mock_darujme_url(mock_get)

        self.dpch.money_account = self.api
        self.dpch.save()

        mommy.make("aklub.ProfileEmail", email="big@tester.com", is_primary=True, user=self.user)

        result = check_last_month_year_payment(self.user)
        self.assertTrue(result)
        self.assertTrue(cache.get(f"{self.user.id}_paid_section"))

    @override_settings(SUM_LAST_YEAR_PAYMENTS=3000, SUM_LAST_MONTH_PAYMENTS=100)
    @patch('api.utils.requests.get')
    def test_darujme_email_not_found(self, mock_get):
        self._mock_darujme_url(mock_get)

        self.dpch.money_account = self.api
        self.dpch.save()

        mommy.make("aklub.ProfileEmail", email="this_email@no_exist.eu", is_primary=True, user=self.user)

        result = check_last_month_year_payment(self.user)
        self.assertFalse(result)

    @override_settings(SUM_LAST_YEAR_PAYMENTS=3000, SUM_LAST_MONTH_PAYMENTS=100)
    @patch('api.utils.requests.get')
    def test_darujme_payment_not_done(self, mock_get):
        self._mock_darujme_url(mock_get)

        self.dpch.money_account = self.api
        self.dpch.save()

        mommy.make("aklub.ProfileEmail", email="trickyone@test.cz", is_primary=True, user=self.user)

        result = check_last_month_year_payment(self.user)
        self.assertFalse(result)
