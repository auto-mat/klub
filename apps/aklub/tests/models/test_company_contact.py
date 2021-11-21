from django.test import TestCase

from model_mommy import mommy

from aklub.models import CompanyContact


class CompanyContactTest(TestCase):
    """Test CompanyContactTest model"""

    def test_create_company_contact(self):
        """Test create ContactTest model"""
        username = "test_user"
        profile = mommy.make(
            "aklub.CompanyProfile",
            username=username,
        )
        self.assertEqual(profile.email, None)

        user_profile_email1 = mommy.make(
            "aklub.CompanyContact",
            email="test_email@bla.com",
            is_primary=True,
            company=profile,
        )
        self.assertEqual(profile.companycontact_set.first(), user_profile_email1)
        emails = CompanyContact.objects.filter(company=profile)
        self.assertEqual(emails.count(), 1)

        mommy.make(
            "aklub.CompanyContact",
            email="test_email@blah.com2",
            is_primary="",
            company=profile,
        )

        emails = CompanyContact.objects.filter(company=profile)
        self.assertEqual(emails.count(), 2)
