from api.utils import check_last_month_year_payment

from django.test import TestCase, override_settings

from freezegun import freeze_time

from model_mommy import mommy

from .utils import app_login_mixin


@freeze_time("2015-5-1")
class CheckLastMonthYearPaymentTest(TestCase):
    def setUp(self):
        app_login_mixin()
        self.user = mommy.make('aklub.UserProfile', username='Testeretes')
        unit = mommy.make('aklub.administrativeunit', name='test_unit')
        event = mommy.make('aklub.event', slug='event_slug', administrative_units=[unit, ])
        bank_acc = mommy.make('aklub.bankaccount', bank_account='11122/111', slug='bank_slug', administrative_unit=unit)
        self.dpch = mommy.make('aklub.DonorPaymentChannel', event=event, money_account=bank_acc, VS=1111, user=self.user)

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
