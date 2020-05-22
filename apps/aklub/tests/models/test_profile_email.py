# -*- coding: utf-8 -*-

from django.test import TestCase

from model_mommy import mommy

from ...models import ProfileEmail


class ProfileEmailTest(TestCase):
    """ Test ProfileEmail model """

    def test_create_profile_email(self):
        """ Test create ProfileEmail model """
        username = 'test_user'
        profile = mommy.make(
            'aklub.UserProfile',
            username=username,
        )
        self.assertEqual(profile.email, None)

        user_profile_email1 = mommy.make(
            'aklub.ProfileEmail',
            email='test_email@bla.com',
            is_primary=True,
            user=profile,
        )
        self.assertEqual(profile.profileemail_set.first(), user_profile_email1)
        emails = ProfileEmail.objects.filter(user=profile)
        self.assertEqual(emails.count(), 1)

        mommy.make(
            'aklub.ProfileEmail',
            email='test_email@blah.com2',
            is_primary='',
            user=profile,
        )

        emails = ProfileEmail.objects.filter(user=profile)
        self.assertEqual(emails.count(), 2)
