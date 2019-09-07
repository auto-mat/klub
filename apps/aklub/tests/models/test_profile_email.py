# -*- coding: utf-8 -*-

from django.test import TestCase

from model_mommy import mommy

from ...models import Profile, ProfileEmail


class ProfileEmailTest(TestCase):
    """ Test ProfileEmail model """

    def test_create_profile_email(self):
        """ Test create ProfileEmail model """
        # User/CompanyProfile model name
        child_models = [model._meta.model_name for model in Profile.__subclasses__()]
        for model in child_models:
            username = 'test.{}'.format(model)
            profile = mommy.make(
                model,
                username=username,
            )
            self.assertEqual(profile.email, None)

            user_profile_email1 = '{0}1@{0}1.test'.format(username)
            mommy.make(
                'aklub.ProfileEmail',
                email=user_profile_email1,
                is_primary=True,
                user=profile,
            )
            self.assertEqual(Profile.objects.get(username=username).email, user_profile_email1)
            emails = ProfileEmail.objects.filter(user=profile)
            self.assertEqual(emails.count(), 1)

            user_profile_email2 = '{0}2@t{0}2.test'.format(username)
            mommy.make(
                'aklub.ProfileEmail',
                email=user_profile_email2,
                is_primary='',
                user=profile,
            )
            emails = ProfileEmail.objects.filter(user=profile)
            self.assertEqual(emails.count(), 2)
