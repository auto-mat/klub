# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2017 o.s. Auto*Mat
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.contrib import admin as django_admin, auth
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.urls import reverse

from django_admin_smoke_tests import tests

from freezegun import freeze_time

from interactions.models import Interaction

from model_mommy import mommy
from model_mommy.recipe import seq

from .recipes import donor_payment_channel_recipe, user_profile_recipe
from .test_admin_helper import TestProfilePostMixin
from .utils import RunCommitHooksMixin
from .utils import print_response  # noqa
from .. import admin
from .. models import (
    AccountStatements, AutomaticCommunication, CompanyContact, DonorPaymentChannel, MassCommunication,
    Profile, Telephone, UserProfile,
)


class CreateSuperUserMixin:

    def setUp(self):
        self.superuser = auth.get_user_model().objects.create_superuser(
            username='testuser',
            email='testuser@example.com',
            password='foo',
            polymorphic_ctype_id=ContentType.objects.get(model=UserProfile._meta.model_name).id,
        )


class AdminSmokeTest(CreateSuperUserMixin, tests.AdminSiteSmokeTest):
    fixtures = ['conditions', 'users']
    exclude_apps = ['helpdesk', 'postoffice', 'advanced_filters', 'celery_monitor', 'import_export_celery', 'wiki_attachments']

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

        if not self.modeladmins:
            self.modeladmins = admin.site._registry.items()

        try:
            admin.autodiscover()
        except Exception:
            pass

    def post_request(self, post_data={}, params=None):
        request = super().post_request(post_data, params)
        request.session = 'session'
        request._messages = FallbackStorage(request)
        return request


@override_settings(
    CELERY_ALWAYS_EAGER=True,
)
class AdminTest(CreateSuperUserMixin, TestProfilePostMixin, RunCommitHooksMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def get_request(self, params=None):
        request = self.factory.get('/', params)

        request.user = self.superuser
        return request

    def post_request(self, post_data={}, params=None):
        request = self.factory.post('/', data=post_data)
        request.user = self.superuser
        request._dont_enforce_csrf_checks = True
        request.session = 'session'
        request._messages = FallbackStorage(request)
        return request

    def test_send_mass_communication(self):
        users = user_profile_recipe.make(username=seq("Foo "), _quantity=5)
        for u in users:
            donor_payment_channel_recipe.make(user=u)
            mommy.make('Preference', send_mailing_lists=True, user=u)
        model_admin = django_admin.site._registry[DonorPaymentChannel]
        request = self.post_request({})
        for queryset in (UserProfile.objects.filter(id__in=(u.id for u in users)), DonorPaymentChannel.objects.all()):
            response = admin.send_mass_communication_action(model_admin, request, queryset)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(
                response.url,
                "/aklub/masscommunication/add/?send_to_users=%s" % "%2C".join(str(getattr(u, 'user', u).id) for u in queryset),
            )
            self.client.force_login(self.superuser)
            response = self.client.get(response.url, follow=True)
            for u in queryset:
                user = getattr(u, 'user', u)
                self.assertContains(response, '<option value="%s" selected>%s</option>' % (user.id, str(user)), html=True)

    @freeze_time("2015-5-1")
    def test_account_statement_changelist_post(self):
        event = mommy.make("aklub.Event", name="Klub přátel Auto*Matu")
        unit = mommy.make("aklub.administrativeunit", name='test,unit')
        mommy.make("aklub.ApiAccount", project_name="Klub přátel Auto*Matu", event=event, administrative_unit=unit)
        mommy.make("aklub.Payment", SS=22258, type="darujme", operation_id="13954", date="2016-02-09")
        donor_payment_channel_recipe.make(id=2979, userprofile__email="bar@email.com", userprofile__language="cs")
        model_admin = django_admin.site._registry[AccountStatements]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        with open("apps/aklub/test_data/test_darujme.xls", "rb") as f:
            post_data = {
                '_save': 'Save',
                "type": "darujme",
                "date_from": "2010-10-01",
                "csv_file": f,
                'payment_set-TOTAL_FORMS': 0,
                'payment_set-INITIAL_FORMS': 0,
                'administrative_unit': unit.id,
            }
            request = self.post_request(post_data=post_data)
            response = model_admin.add_view(request)
            self.run_commit_hooks()
            self.assertEqual(response.status_code, 302)
            obj = AccountStatements.objects.get(date_from="2010-10-01")
            self.assertEqual(response.url, "/aklub/accountstatements/")
            self.assertEqual(obj.payment_set.count(), 6)

            # self.assertEqual(request._messages._queued_messages[0].message, 'Skipped payments: Testing User 1 (test.user1@email.cz)')
            self.assertEqual(
                request._messages._queued_messages[0].message,
                'Položka typu Výpis z účtu "<a href="/aklub/accountstatements/%(id)s/change/">%(id)s (2015-05-01 00:00:00+00:00)</a>"'
                ' byla úspěšně přidána.' % {'id': obj.id},
            )

    @freeze_time("2015-5-1")
    def test_account_statement_changelist_post_bank_statement(self):
        donor_payment_channel_recipe.make(VS=120127010)
        unit = mommy.make("aklub.administrativeunit", name='test_name')
        mommy.make("aklub.bankaccount", bank_account_number='2400063333/2010', administrative_unit=unit)
        model_admin = django_admin.site._registry[AccountStatements]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        with open("apps/aklub/test_data/Pohyby_5_2016.csv", "rb") as f:
            post_data = {
                '_save': 'Save',
                "type": "account",
                "csv_file": f,
                'payment_set-TOTAL_FORMS': 0,
                'payment_set-INITIAL_FORMS': 0,
                'administrative_unit': unit.id,
            }

            request = self.post_request(post_data=post_data)
            response = model_admin.add_view(request)
            self.run_commit_hooks()
            self.assertEqual(response.status_code, 302)
            obj = AccountStatements.objects.get(date_from="2016-01-25")
            self.assertEqual(response.url, "/aklub/accountstatements/")
            self.assertEqual(obj.payment_set.count(), 4)

            # self.assertEqual(
            #     request._messages._queued_messages[0].message,
            #     'Payments without user: Testing user 1 (Bezhotovostní příjem), '
            #     'KRE DAN (KRE DAN), '
            #     'without variable symbol (without variable symbol)',
            # )
            self.assertEqual(
                request._messages._queued_messages[0].message,
                'Položka typu Výpis z účtu "<a href="/aklub/accountstatements/%(id)s/change/">%(id)s (2015-05-01 00:00:00+00:00)</a>"'
                ' byla úspěšně přidána.' % {'id': obj.id},
            )

    @override_settings(
        LANGUAGE_CODE='en',
    )
    def test_mass_communication_changelist_post_send_mails(self):
        unit = mommy.make("aklub.AdministrativeUnit", name="test1")
        company_profile1 = mommy.make(
            "CompanyProfile",
            id=2978,
            is_active=True,
            email="foo@email.com",
            language="cs",
        )
        user_profile1 = mommy.make(
            "UserProfile",
            id=2979,
            is_active=True,
            email="bar@email.com",
            language="cs",
        )
        user_profile2 = mommy.make(
            "UserProfile",
            id=3,
            is_active=True,
            email="baz@email.com",
            language="en",
        )
        inter_category = mommy.make('interactions.interactioncategory', category='testcategory')
        inter_type = mommy.make('interactions.interactiontype', category=inter_category, name='testtype', send_email=True)
        for profile in [company_profile1, user_profile1, user_profile2]:
            mommy.make('Preference', send_mailing_lists=True, user=profile)
        model_admin = django_admin.site._registry[MassCommunication]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        post_data = {
            '_continue': 'send_mails',
            'name': 'test communication',
            "method_type": inter_type.id,
            'date': "2010-03-03",
            "subject": "Subject",
            "send_to_users": [2978, 2979, 3],
            "administrative_unit": unit.id,
            "template": "Test template",
        }
        request = self.post_request(post_data=post_data)
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 302)
        obj = MassCommunication.objects.get(name="test communication")
        self.assertEqual(obj.subject, "Subject")
        self.assertEqual(response.url, "/aklub/masscommunication/%s/change/" % obj.id)
        self.assertEqual(
            request._messages._queued_messages[0].message,
            "Communication sending was queued for 3 users",
        )
        edit_text = 'You may edit it again below.'
        self.assertEqual(
            request._messages._queued_messages[1].message,
            'The Mass Communication "<a href="/aklub/masscommunication/%s/change/">test communication</a>"'
            ' was added successfully. %s' % (obj.id, edit_text),
        )

    def test_mass_communication_changelist_post(self):
        unit = mommy.make("aklub.AdministrativeUnit", name="test1")
        inter_category = mommy.make('interactions.interactioncategory', category='testcategory')
        inter_type = mommy.make('interactions.interactiontype', category=inter_category, name='testtype', send_email=True)
        model_admin = django_admin.site._registry[MassCommunication]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)
        attachment = SimpleUploadedFile("attachment.txt", b"attachment", content_type="text/plain")
        post_data = {
            '_continue': 'test_mail',
            'name': 'test communication',
            "method_type": inter_type.id,
            'date': "2010-03-03",
            "subject": "Subject",
            "attach_tax_confirmation": False,
            "attachment": attachment,
            "administrative_unit": unit.id,
            "template": "Test template",
        }
        request = self.post_request(post_data=post_data)
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 302)
        obj = MassCommunication.objects.get(name="test communication")
        self.assertEqual(obj.subject, "Subject")
        self.assertEqual(response.url, "/aklub/masscommunication/%s/change/" % obj.id)

    def test_automatic_communication_changelist_post(self):
        unit = mommy.make("aklub.AdministrativeUnit", name="test1")
        inter_category = mommy.make('interactions.interactioncategory', category='testcategory')
        inter_type = mommy.make('interactions.interactiontype', category=inter_category, name='testtype', send_email=True)
        mommy.make("flexible_filter_conditions.NamedCondition", id=1)
        model_admin = django_admin.site._registry[AutomaticCommunication]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        post_data = {
            '_continue': 'test_mail',
            'name': 'test communication',
            'condition': 1,
            "method_type": inter_type.id,
            "subject": "Subject",
            "administrative_unit": unit.id,
            "template": "Test template",
        }
        request = self.post_request(post_data=post_data)
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 302)
        obj = AutomaticCommunication.objects.get(name="test communication")
        self.assertEqual(obj.subject, "Subject")
        self.assertEqual(response.url, "/aklub/automaticcommunication/%s/change/" % obj.id)

    def test_communication_changelist_post(self):
        user_profile = mommy.make('aklub.UserProfile')
        unit = mommy.make('aklub.AdministrativeUnit')

        interaction_category = mommy.make('interactions.interactioncategory')
        interaction_type = mommy.make('interactions.interactiontype', category=interaction_category)
        model_admin = django_admin.site._registry[Interaction]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        post_data = {
            '_save': 'test_mail',
            "user": user_profile.id,
            "date_from_0": "2015-03-1",
            "date_from_1": "12:43",
            "method": "email",
            "subject": "Subject 123",
            "summary": "Test template",
            "administrative_unit": unit.id,
            "type": interaction_type.id,
        }
        request = self.post_request(post_data=post_data)
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 302)
        obj = Interaction.objects.get()
        self.assertEqual(obj.subject, "Subject 123")
        self.assertEqual(obj.summary, "Test template")
        self.assertEqual(response.url, "/interactions/interaction/")

    def test_user_in_campaign_changelist_post(self):
        mommy.make("aklub.Event", id=1)
        mommy.make("aklub.Userprofile", id=2978)
        au = mommy.make("aklub.AdministrativeUnit", name="test")
        mommy.make("aklub.BankAccount", administrative_unit=au, id=1)
        model_admin = django_admin.site._registry[DonorPaymentChannel]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)
        post_data = {
            '_continue': 'Save',
            'money_account': 1,
            'user': 2978,
            'VS': 1234,
            'activity_points': 13,
            'registered_support_0': "2010-03-03",
            'registered_support_1': "12:35",
            'regular_payments': 'promise',
            'campaign': '1',
            'verified': 1,
            'communications-TOTAL_FORMS': 1,
            'communications-INITIAL_FORMS': 0,
            'payment_set-TOTAL_FORMS': 0,
            'payment_set-INITIAL_FORMS': 0,
            "communications-0-method": "phonecall",
            "communications-0-subject": "Subject 1",
            "communications-0-summary": "Text 1",
            "communications-0-date_0": "2010-01-01",
            "communications-0-date_1": "11:11",
        }
        request = self.post_request(post_data=post_data)
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 302)
        donorpaymentchannel = DonorPaymentChannel.objects.get(VS=1234)
        self.assertEqual(response.url, "/aklub/donorpaymentchannel/%s/change/" % donorpaymentchannel.id)

        # self.assertEqual(donorpaymentchannel.activity_points, 13)
        # self.assertEqual(donorpaymentchannel.verified_by.username, 'testuser')

    def test_pair_payments_with_dpch(self):
        """ Test pair_payment_with_dpch action """
        unit = mommy.make('aklub.AdministrativeUnit', name='test')
        money_acc = mommy.make('aklub.MoneyAccount', administrative_unit=unit)
        payment_channel = donor_payment_channel_recipe.make(VS=123, money_account=money_acc)
        payment = mommy.make("aklub.Payment", VS=123)
        account_statement = mommy.make(
            "aklub.AccountStatements",
            payment_set=[payment],
            administrative_unit=unit,
        )
        request = self.post_request()
        admin.pair_payment_with_dpch(None, request, [account_statement])
        payment.refresh_from_db()
        self.assertEqual(payment.user_donor_payment_channel, payment_channel)

    def test_profile_post(self):
        """ Test Profile admin model add/change view """
        self.create_group()
        event = self.create_event()
        actions = ['add_view', 'change_view']
        child_models = Profile.__subclasses__()

        for index, child_model in enumerate(child_models):
            admin_model = self.register_admin_model(admin_model=child_model)
            for view_method_name in actions:
                action = view_method_name.split('_')[0]
                model_name = child_model._meta.model_name
                test_str = '{}.{}'.format(action, model_name)

                administrative_unit = mommy.make(
                    'aklub.AdministrativeUnit',
                    name='test_AU',
                )
                bank_account = mommy.make(
                    'aklub.BankAccount',
                    bank_account=test_str,
                    bank_account_number=index,
                    note='test',
                )
                profile_post_data = self.get_profile_post_data(
                    administrative_units=administrative_unit,
                    event=event,
                    index=index,
                    bank_account=bank_account,
                    test_str=test_str,
                    action=action,
                    child_model=child_model,
                )
                post_data = self.update_profile_post_data(
                    action=action,
                    post_data=profile_post_data,
                    child_model=child_model,
                )
                view_method = getattr(admin_model, view_method_name)
                request = self.post_request(post_data=post_data)
                if action == 'change':
                    user_id = str(Profile.objects.get(username='add.{}'.format(model_name)).id)
                    response = view_method(request, object_id=user_id)
                else:
                    response = view_method(request)
                self.assertEqual(response.status_code, 302)

                profile = Profile.objects.get(username='{}'.format(test_str))
                # Personal info
                self.compare_profile_personal_info(
                    action=action, post_data=post_data, profile=profile,
                )

                # Telephone
                if profile.is_userprofile():
                    telephone = set(Telephone.objects.filter(user=profile).values_list('telephone', flat=True))
                    if action == 'add':
                        self.assertEqual(telephone, {post_data['telephone']})
                    else:
                        self.assertEqual(telephone, {post_data['telephone_set-0-telephone']})
                else:
                    telephone = set(CompanyContact.objects.filter(company=profile).values_list('telephone', flat=True))
                    if action == 'add':
                        self.assertEqual(telephone, {post_data['telephone']})
                    else:
                        self.assertEqual(telephone, {post_data['companycontact_set-0-telephone']})

        new_profiles = Profile.objects.exclude(username=self.superuser.username)
        self.assertEqual(new_profiles.count(), len(child_models))
        # Delete profiles
        self.delete_profile(new_profiles)
        self.assertEqual(Profile.objects.exclude(username=self.superuser.username).count(), 0)


class UserProfileAdminTests(TestCase):
    def test_unit_admin(self):
        au1 = mommy.make("aklub.AdministrativeUnit", name="test1")
        au2 = mommy.make("aklub.AdministrativeUnit", name="test2")

        user = mommy.make('UserProfile', is_staff=True, administrated_units=[au1])
        self.client.force_login(user)

        u1 = mommy.make('UserProfile', administrative_units=[au1], first_name="Foo")
        mommy.make('UserProfile', administrative_units=[au2], first_name="Bar")
        channel = mommy.make(
            'DonorPaymentChannel', user=u1, money_account__administrative_unit=au1,
            regular_payments="regular", regular_amount=120,
        )
        mommy.make('Payment', user_donor_payment_channel=channel, amount=100)
        user.user_permissions.add(Permission.objects.get(codename='view_userprofile'))
        response = self.client.get(reverse('admin:aklub_userprofile_changelist'), follow=True)
        self.assertContains(response, '<td class="field-get_administrative_units">test1</td>', html=True)
        self.assertContains(response, '<td class="field-get_sum_amount">100</td>', html=True)
        self.assertContains(response, '<td class="field-regular_amount"><nobr>120</nobr></td>', html=True)
        self.assertNotContains(response, '<td class="field-get_administrative_units">test2</td>', html=True)


class AdminActionsTests(CreateSuperUserMixin, RunCommitHooksMixin, TestCase):
    """ Admin actions tests """

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.client.force_login(self.superuser)

    def get_request(self, params=None):
        request = self.factory.get('/', params)
        request.user = self.superuser
        return request

    def post_request(self, post_data={}, params=None):
        request = self.factory.post('/', data=post_data)
        request.user = self.superuser
        request._dont_enforce_csrf_checks = True
        request.session = 'session'
        request._messages = FallbackStorage(request)
        return request

    def test_delete_selected_profiles(self):
        """
        Test admin userprofile and companyprofile model 'Delete method'
        action
        """
        user_profile = mommy.make(
            'aklub.UserProfile',
            username='test.userprofile',
        )
        mommy.make(
            'aklub.ProfileEmail',
            email='test.userprofile@test.userprofile.test',
            is_primary=True,
            user=user_profile,
        )
        company_profile = mommy.make(
            'aklub.CompanyProfile',
            username='test.companyprofile',
        )
        mommy.make(
            'aklub.CompanyContact',
            email='test.companyprofile@test.companyprofile.test',
            is_primary=True,
            company=company_profile,
        )

        self.assertEqual(Profile.objects.exclude(username=self.superuser.username).count(), 2)
        post_data = {
            '_selected_action': [user_profile.id],
            'action': 'delete_selected',
            'post': 'yes',
        }
        address = reverse('admin:aklub_userprofile_changelist')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=address)
        self.assertEqual(Profile.objects.exclude(username=self.superuser.username).count(), 1)

        post_data = {
            '_selected_action': [company_profile.id],
            'action': 'delete_selected',
            'post': 'yes',
        }
        address = reverse('admin:aklub_companyprofile_changelist')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=address)
        self.assertEqual(Profile.objects.exclude(username=self.superuser.username).count(), 0)


class AdminRemoveAdministrativeUnitTests(CreateSuperUserMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.client.force_login(self.superuser)

        self.unit = mommy.make(
            'aklub.AdministrativeUnit',
            name='test_unit',
        )
        mommy.make(
            'aklub.UserProfile',
            username='test.userprofile',
            id=11111,
            administrative_units=[self.unit],
            is_active=True,
        )
        # add administrative_units to superuser
        self.superuser.administrated_units.add(self.unit)
        self.superuser.administrative_units.add(self.unit)

    def test_remove_administrative_unit_succes(self):
        """
        Test admin view remove_contact_from_unit to remove administrative_unit from profile succesfully
        """
        address = reverse('admin:aklub_remove_contact_from_unit', args=(11111,))
        response = self.client.post(address)
        self.assertEqual(response.status_code, 302)
        profile = Profile.objects.get(pk=11111)
        self.assertEqual(profile.administrative_units.count(), 0)
        self.assertEqual(profile.preference_set.count(), 0)
        self.assertEqual(profile.is_active, False)

    def test_remove_administrative_unit_fail(self):
        """
        Test admin view remove_contact_from_unit to remove administrative_unit from own profile unsuccesfully
        """
        address = reverse('admin:aklub_remove_contact_from_unit', args=(self.superuser.id,))
        response = self.client.post(address, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You can not remove administrative unit from your own profile', html=True)

        profile = Profile.objects.get(pk=self.superuser.id)
        self.assertEqual(profile.administrative_units.first(), self.unit)
        self.assertEqual(profile.preference_set.count(), 1)
