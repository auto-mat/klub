# -*- coding: utf-8 -*-

from django.test import TestCase
from django.utils.translation import ugettext as _

from model_mommy import mommy

from ..admin import ProfileEmailAdminForm
from ..models import Profile, ProfileEmail


class FormTest(TestCase):
    def setUp(self):
        super().setUp()

    def test_profile_email_admin_form(self):
        child_models = [model._meta.model_name for model in Profile.__subclasses__()]
        for model in child_models:
            username1 = 'test.{}1'.format(model)
            user1 = mommy.make(
                'aklub.UserProfile',
                username=username1,
            )
            mommy.make(
                'aklub.ProfileEmail',
                email='{0}@{0}.test'.format(username1),
                is_primary=True,
                user=user1,
            )
            username2 = 'test.{}2'.format(model)
            user2 = mommy.make(
                'aklub.UserProfile',
                username=username2,
            )
            mommy.make(
                'aklub.ProfileEmail',
                email='{0}@{0}.test'.format(username2),
                is_primary=True,
                user=user2,
            )

            # Duplicate email address
            form_data = {
                'user': user1.id,
                'email': '{0}@{0}.test'.format(username1),
            }
            form = ProfileEmailAdminForm(form_data)
            self.assertEqual(form['email'].errors[0], _('Duplicate email address for this user'))
            self.assertEqual(form.is_valid(), False)

            # Email address exist
            form_data = {
                'user': user1.id,
                'email': '{0}@{0}.test'.format(username2),
            }
            form = ProfileEmailAdminForm(form_data)
            self.assertEqual(form['email'].errors[0], _('Email address exist'))
            self.assertEqual(form.is_valid(), False)

            # Create new email address
            form_data = {
                'user': user1.id,
                'email': '{0}.new@{0}.new.test'.format(username1),
            }
            form = ProfileEmailAdminForm(form_data)
            self.assertEqual(len(form['email'].errors), 0)
            self.assertEqual(form.is_valid(), True)
            form.save()
            emails = ProfileEmail.objects.filter(user=user1).values_list('email', flat=True)
            self.assertIn('{0}.new@{0}.new.test'.format(username1), tuple(emails))
