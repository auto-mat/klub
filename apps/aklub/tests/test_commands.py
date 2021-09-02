from aklub.models import (
    AdministrativeUnit,
    BankAccount,
    CompanyContact,
    CompanyProfile,
    DonorPaymentChannel,
    Payment,
    ProfileEmail,
    Telephone,
    UserBankAccount,
    UserProfile,
)

from django.core import management
from django.test import TestCase

from events.models import Event


class DumpDataTest(TestCase):
    """
    python manage.py dump_data test => generate some data
    """

    def test_dump_data(self):
        management.call_command("dump_data", number_of_users=10, number_of_companies=10)

        self.assertEqual(UserProfile.objects.count(), 10)
        self.assertEqual(CompanyProfile.objects.count(), 10)

        # some other data were created
        self.assertTrue(Event.objects.exists())
        self.assertTrue(AdministrativeUnit.objects.exists())
        self.assertTrue(BankAccount.objects.exists())
        self.assertTrue(CompanyContact.objects.exists())
        self.assertTrue(CompanyProfile.objects.exists())
        self.assertTrue(DonorPaymentChannel.objects.exists())
        self.assertTrue(Payment.objects.exists())
        self.assertTrue(ProfileEmail.objects.exists())
        self.assertTrue(Telephone.objects.exists())
        self.assertTrue(UserBankAccount.objects.exists())


class CreateAdminTest(TestCase):
    """
    SuperUser and Admin of AdministrativeUnit => created
    """

    def test_create_admin(self):
        management.call_command("create_admin")
        superuser = UserProfile.objects.get(is_superuser=True)
        self.assertTrue(superuser.profileemail_set.exists())
        self.assertTrue(superuser.password)

        admins = UserProfile.objects.exclude(is_superuser=True)
        self.assertEqual(admins.count(), 1)
        admin = admins.first()
        self.assertTrue(admin.profileemail_set.exists())
        self.assertTrue(admin.password)
        self.assertEqual(admin.groups.count(), 1)
        self.assertEqual(
            admin.groups.first().name, "can_do_everything_under_administrative_unit"
        )
