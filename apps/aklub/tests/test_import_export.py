
import datetime
import re
import pathlib
import os

from model_mommy import mommy

from django.test import RequestFactory, TestCase
from django.urls import reverse

from ..models import DonorPaymentChannel, ProfileEmail

from .test_admin import CreateSuperUserMixin


class AdminImportExportTests(CreateSuperUserMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.client.force_login(self.superuser)

        au = mommy.make(
                    'aklub.AdministrativeUnit',
                    name='test_unit'
        )
        self.bank_acc = mommy.make(
                    'aklub.BankAccount',
                    administrative_unit=au,
                    bank_account_number='1111/111'
        )
        self.event1 = mommy.make(
                    'aklub.Event',
                    name='test',
        )
        self.event2 = mommy.make(
                    'aklub.Event',
                    name='test_old',
        )
        user = mommy.make(
                    'aklub.UserProfile',
                    username='test1',
        )
        mommy.make(
                    'aklub.ProfileEmail',
                    email='test1@test.com',
                    user=user,
        )
        mommy.make(
                    'aklub.DonorPaymentChannel',
                    id=101,
                    user=user,
                    VS=9999,
                    SS=111,
                    regular_frequency='quaterly',
                    expected_date_of_first_payment=datetime.date(2010, 2, 11),
                    regular_amount=1000,
                    regular_payments='regular',
                    money_account=self.bank_acc,
                    event=self.event2,
                    end_of_regular_payments=datetime.date(2010, 2, 11)
        )

    def test_profile_import(self):
        "test donor payment channel import"
        address = reverse('admin:aklub_donorpaymentchannel_import')
        response_address = self.client.get(address)
        self.assertEqual(response_address.status_code, 200)

        p = pathlib.PurePath(__file__)
        csv_file_create_dpch = os.path.join(p.parents[1], 'test_data', 'test_donor_import.csv')

        with open(csv_file_create_dpch, "rb") as f:
            data = {
                'input_format': 0,
                'import_file': f,
            }
            response = self.client.post(address, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test1@test.com', html=True)
        self.assertContains(response, '9999/999', html=True)

        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )

        file_name = [val.split('=')[-1].replace('"', '') for val in result.group(0).split(' ') if 'value' in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': 'test_donor_import.csv',
            'input_format': 0,
        }
        address = reverse('admin:aklub_donorpaymentchannel_process_import')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_donorpaymentchannel_changelist'))

        # check new DonorPaymentChannel data
        email = ProfileEmail.objects.get(email='test1@test.com')
        new_dpch = DonorPaymentChannel.objects.get(user=email.user, event=self.event1)

        self.assertEqual(new_dpch.money_account, self.bank_acc)
        self.assertEqual(new_dpch.event, self.event1)
        self.assertEqual(new_dpch.VS, '1234')
        self.assertEqual(new_dpch.SS, '222')
        self.assertEqual(new_dpch.regular_frequency, 'monthly')
        self.assertEqual(new_dpch.expected_date_of_first_payment, datetime.date(2016, 9, 16))
        self.assertEqual(new_dpch.regular_amount, 1000)
        self.assertEqual(new_dpch.regular_payments, 'regular')
        self.assertEqual(new_dpch.user_bank_account.bank_account_number, '9999/999')
        self.assertEqual(new_dpch.end_of_regular_payments, datetime.date(2017, 9, 16))

        # check updated  DonorPaymentChannel data
        dpch_update = DonorPaymentChannel.objects.get(id=101)
        self.assertEqual(dpch_update.money_account, self.bank_acc)
        self.assertEqual(dpch_update.event, self.event2)
        self.assertEqual(dpch_update.VS, '1111')
        self.assertEqual(dpch_update.SS, '333')
        self.assertEqual(dpch_update.regular_frequency, 'monthly')
        self.assertEqual(dpch_update.expected_date_of_first_payment, datetime.date(2016, 1, 11))
        self.assertEqual(dpch_update.regular_amount, 100)
        self.assertEqual(dpch_update.regular_payments, 'regular')
        self.assertEqual(dpch_update.user_bank_account.bank_account_number, '9999/999')
        self.assertEqual(dpch_update.end_of_regular_payments, datetime.date(2017, 1, 11))
