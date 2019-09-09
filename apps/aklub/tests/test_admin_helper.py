# -*- coding: utf-8 -*-

from django.contrib import admin as django_admin
from django.contrib.auth.models import Group

from model_mommy import mommy

from .. models import ProfileEmail, UserProfile


class TestProfilePostMixin:
    """ 'test_profile_post' test helper class """

    def register_admin_model(self, admin_model):
        admin_model = django_admin.site._registry[admin_model]
        request = self.get_request()
        response = admin_model.add_view(request)
        self.assertEqual(response.status_code, 200)

        return admin_model

    def create_group(self):
        admin_model = self.register_admin_model(admin_model=Group)
        group_post_data = {
            'name': 'test',
            'permissions': 1,
        }
        request = self.post_request(post_data=group_post_data)
        response = admin_model.add_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Group.objects.count(), 1)

    def create_event(self):
        event = mommy.make(
            'aklub.Event',
            name='Klub přátel Auto*Matu',
            created='2015-12-16',
            slug='klub',
            allow_statistics=True,
            darujme_api_id=38571205,
            darujme_project_id=38571205,
            acquisition_campaign=True,
            enable_signing_petitions=True,
            enable_registration=True,
            darujme_name='Klub přátel Auto*Matu',
        )

        return event

    def get_profile_formset_data(self):
        managementform_data = {
            'preference_set-TOTAL_FORMS': 1,
            'preference_set-INITIAL_FORMS': 0,
            'preference_set-MIN_NUM_FORMS': 0,
            'preference_set-MAX_NUM_FORMS': 1000,
            'profileemail_set-TOTAL_FORMS': 2,
            'profileemail_set-INITIAL_FORMS': 0,
            'profileemail_set-MIN_NUM_FORMS': 0,
            'profileemail_set-MAX_NUM_FORMS': 1000,
            'telephone_set-TOTAL_FORMS': 1,
            'telephone_set-INITIAL_FORMS': 0,
            'telephone_set-MIN_NUM_FORMS': 0,
            'telephone_set-MAX_NUM_FORMS': 1000,
            'userchannels-TOTAL_FORMS': 1,
            'userchannels-INITIAL_FORMS': 0,
            'userchannels-MIN_NUM_FORMS': 0,
            'userchannels-MAX_NUM_FORMS': 1000,
            'interaction_set-TOTAL_FORMS': 1,
            'interaction_set-INITIAL_FORMS': 0,
            'interaction_set-MIN_NUM_FORMS': 0,
            'interaction_set-MAX_NUM_FORMS': 1000,
        }

        return managementform_data

    def get_profile_post_data(self, event, index, bank_account, test_str):
        profile_post_data = {
            'username': '{}'.format(test_str),
            'language': 'cs',
            'is_staff': 'on',
            'groups': Group.objects.get().id,
            'preference_set-0-newsletter_on': True,
            'preference_set-0-call_on': True,
            'profileemail_set-0-email': '{0}@{0}.test'.format(test_str),
            'profileemail_set-0-is_primary': True,
            'profileemail_set-1-email': '{0}@{0}{1}.test'.format(test_str, index),
            'telephone_set-0-telephone': '+421111222333',
            'userchannels-0-bank_account': bank_account.id,
            'userchannels-0-regular_payments': 'regular',
            'userchannels-0-event': event.id,
        }

        return profile_post_data

    def update_profile_post_data(self, action, post_data, child_model):
        post_data.update(self.get_profile_formset_data())
        if action == 'change':
            post_data['preference_set-TOTAL_FORMS'] = 0
            post_data['profileemail_set-TOTAL_FORMS'] = 0
            post_data['telephone_set-TOTAL_FORMS'] = 0
            post_data['userchannels-TOTAL_FORMS'] = 0
            post_data['interaction_set-TOTAL_FORMS'] = 0
        if 'sex' in (f.name for f in child_model._meta.fields):
            post_data.update(
                {
                    'sex': 'male',
                    'first_name': 'First name' if action == 'add' else 'First name edit',
                    'last_name': 'Last name' if action == 'add' else 'Last name edit',
                }
            )
        if 'crn' in (f.name for f in child_model._meta.fields):
            post_data.update(
                {
                    'crn': '00000000' if action == 'add' else '11111111',
                    'name': 'Company' if action == 'add' else 'Company edit',
                }
            )
        return post_data

    def compare_profile_personal_info(self, action, post_data, profile):
        group_id = profile.groups.all().values_list("id", flat=True)[0]
        primary_email = ProfileEmail.objects.get(user=profile, is_primary=True).email
        emails = set(
            ProfileEmail.objects.filter(user=profile).values_list('email', flat=True),
        )
        self.assertEqual(profile.username, post_data['username'])

        if action == 'add':
            if isinstance(profile, UserProfile):
                self.assertEqual(profile.first_name, post_data['first_name'])
                self.assertEqual(profile.last_name, post_data['last_name'])
            else:
                self.assertEqual(profile.name, post_data['name'])
                self.assertEqual(profile.crn, post_data['crn'])

            self.assertEqual(profile.email, post_data['profileemail_set-0-email'])
            self.assertEqual(profile.email, primary_email)
            self.assertEqual(
                emails,
                {
                    post_data['profileemail_set-0-email'],
                    post_data['profileemail_set-1-email'],
                },
            )
        else:
            if isinstance(profile, UserProfile):
                self.assertEqual(profile.first_name, 'First name edit')
                self.assertEqual(profile.last_name, 'Last name edit')
            else:
                self.assertEqual(profile.name, 'Company edit')
                self.assertEqual(profile.crn, '11111111')

            self.assertEqual(profile.email, None)

        self.assertEqual(profile.is_staff, True)
        self.assertEqual(group_id, post_data['groups'])
        self.assertEqual(group_id, post_data['groups'])

    def compare_profile_preference(self, action, profile, post_data):
        preference = profile.preference_set.first()
        self.assertEqual(profile.preference_set.count(), 1)
        if action == 'add':
            self.assertEqual(
                preference.newsletter_on,
                post_data['preference_set-0-newsletter_on'],
            )
            self.assertEqual(
                preference.call_on,
                post_data['preference_set-0-call_on'],
            )

    def delete_profile(self, new_profiles):
        for profile in new_profiles:
            admin_model = django_admin.site._registry[profile._meta.model]
            delete_post_data = {
                'submit': 'Ano, jsem si jist(a)',
            }
            request = self.post_request(post_data=delete_post_data)
            response = admin_model.delete_view(request, object_id=str(profile.id))
            self.assertEqual(response.status_code, 302)
