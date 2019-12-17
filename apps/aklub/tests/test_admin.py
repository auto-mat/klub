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
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import reverse

from django_admin_smoke_tests import tests

from freezegun import freeze_time

from model_mommy import mommy

from .recipes import donor_payment_channel_recipe, user_profile_recipe
from .test_admin_helper import TestProfilePostMixin
from .utils import RunCommitHooksMixin
from .utils import print_response  # noqa
from .. import admin
from .. models import (
    AccountStatements, AutomaticCommunication, DonorPaymentChannel, Interaction, MassCommunication,
    Profile, TaxConfirmation, Telephone, UserProfile, UserYearPayments,
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
        donor_payment_channel_recipe.make(id=3)
        donor_payment_channel_recipe.make(id=4)
        donor_payment_channel_recipe.make(id=2978)
        donor_payment_channel_recipe.make(id=2979)
        model_admin = django_admin.site._registry[DonorPaymentChannel]
        request = self.post_request({})
        queryset = DonorPaymentChannel.objects.all()
        response = admin.send_mass_communication_action(model_admin, request, queryset)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/aklub/masscommunication/add/?send_to_users=3%2C4%2C2978%2C2979")

    @freeze_time("2017-5-1")
    def test_tax_confirmation_generate(self):
        _foo_user = user_profile_recipe.make(id=2978, first_name="Foo")
        _bar_user = user_profile_recipe.make(id=2979, first_name="Bar")
        au1 = mommy.make("aklub.AdministrativeUnit", name="test1")
        au2 = mommy.make("aklub.AdministrativeUnit", name="test2")
        bank_acc1 = mommy.make("aklub.BankAccount", bank_account_number=111, administrative_unit=au1)
        bank_acc2 = mommy.make("aklub.BankAccount", bank_account_number=222, administrative_unit=au2)
        foo_user = donor_payment_channel_recipe.make(user=_foo_user, money_account=bank_acc1)
        bar_user = donor_payment_channel_recipe.make(user=_bar_user, money_account=bank_acc2)

        mommy.make("aklub.Payment", amount=350, date="2016-01-02", user_donor_payment_channel=foo_user, type="cash")
        mommy.make("aklub.Payment", amount=130, date="2016-01-02", user_donor_payment_channel=bar_user, type="cash")
        model_admin = django_admin.site._registry[TaxConfirmation]
        request = self.post_request({})
        response = model_admin.generate(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/aklub/taxconfirmation/")
        self.assertEqual(TaxConfirmation.objects.get(user_profile__id=2978, year=2016).amount, 350)
        self.assertEqual(TaxConfirmation.objects.get(user_profile__id=2979, year=2016).amount, 130)
        confirmation_values = TaxConfirmation.objects.filter(year=2016).values('user_profile', 'amount', 'year').order_by('user_profile')
        expected_confirmation_values = [
            {'year': 2016, 'user_profile': 2978, 'amount': 350},
            {'year': 2016, 'user_profile': 2979, 'amount': 130},
        ]
        self.assertListEqual(list(confirmation_values), expected_confirmation_values)

    def test_useryearpayments(self):
        """
        Test, that the resulting amount in selected period matches
        """
        for model in Profile.__subclasses__():
            model_name = model._meta.model_name
            profile = mommy.make(
                model_name,
                username='test.{}'.format(model_name),
            )
            donor_payment_channel_recipe.make(
                payment_set=[
                    mommy.make("aklub.Payment", date="2016-2-9", amount=150),
                    mommy.make("aklub.Payment", date="2016-1-9", amount=100),
                    mommy.make("aklub.Payment", date="2012-1-9", amount=100),
                    mommy.make("aklub.Payment", date="2016-12-9", amount=100),  # Payment outside of selected period
                ],
                user=profile,
            )
            model_admin = django_admin.site._registry[UserYearPayments]
            request = self.get_request({
                "drf__payment__date__gte": "01.07.2010",
                "drf__payment__date__lte": "10.10.2016",
            })
            response = model_admin.changelist_view(request)
            self.assertContains(response, '<td class="field-payment_total_by_year">350</td>', html=True)

    @freeze_time("2015-5-1")
    def test_account_statement_changelist_post(self):
        event = mommy.make("aklub.Event", name="Klub přátel Auto*Matu")
        mommy.make("aklub.ApiAccount", project_name="Klub přátel Auto*Matu", event=event)
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
        for profile in [company_profile1, user_profile1, user_profile2]:
            mommy.make('Preference', send_mailing_lists=True, user=profile)
        model_admin = django_admin.site._registry[MassCommunication]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        post_data = {
            '_continue': 'send_mails',
            'name': 'test communication',
            "method": "email",
            'date': "2010-03-03",
            "subject": "Subject",
            "send_to_users": [2978, 2979, 3],
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
        model_admin = django_admin.site._registry[MassCommunication]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        attachment = SimpleUploadedFile("attachment.txt", b"attachment", content_type="text/plain")
        post_data = {
            '_continue': 'test_mail',
            'name': 'test communication',
            "method": "email",
            'date': "2010-03-03",
            "subject": "Subject",
            "attach_tax_confirmation": False,
            "attachment": attachment,
            "template": "Test template",
        }
        request = self.post_request(post_data=post_data)
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 302)
        obj = MassCommunication.objects.get(name="test communication")
        self.assertEqual(obj.subject, "Subject")
        self.assertEqual(response.url, "/aklub/masscommunication/%s/change/" % obj.id)

    def test_automatic_communication_changelist_post(self):
        mommy.make("flexible_filter_conditions.NamedCondition", id=1)
        model_admin = django_admin.site._registry[AutomaticCommunication]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        post_data = {
            '_continue': 'test_mail',
            'name': 'test communication',
            'condition': 1,
            "method": "email",
            "subject": "Subject",
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
        model_admin = django_admin.site._registry[Interaction]
        request = self.get_request()
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        post_data = {
            '_save': 'test_mail',
            "user": user_profile.id,
            "date_0": "2015-03-1",
            "date_1": "12:43",
            "method": "email",
            "subject": "Subject 123",
            "summary": "Test template",
            "administrative_unit": unit.id,
        }
        request = self.post_request(post_data=post_data)
        response = model_admin.add_view(request)
        self.assertEqual(response.status_code, 302)
        obj = Interaction.objects.get()
        self.assertEqual(obj.subject, "Subject 123")
        self.assertEqual(obj.summary, "Test template")
        self.assertEqual(response.url, "/aklub/interaction/")

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
                telephone = set(
                        Telephone.objects.filter(user=profile).values_list('telephone', flat=True),
                    )
                if action == 'add':
                    self.assertEqual(telephone, {post_data['telephone']})
                else:
                    self.assertEqual(telephone, {post_data['telephone_set-0-telephone']})

        new_profiles = Profile.objects.exclude(username=self.superuser.username)
        self.assertEqual(new_profiles.count(), len(child_models))
        # Delete profiles
        self.delete_profile(new_profiles)
        self.assertEqual(Profile.objects.exclude(username=self.superuser.username).count(), 0)


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
        Test admin profile model 'Delete selected Profiles'
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
            'aklub.ProfileEmail',
            email='test.companyprofile@test.companyprofile.test',
            is_primary=True,
            user=company_profile,
        )
        post_data = {
            '_selected_action': [user_profile.id, company_profile.id],
            'action': 'delete_selected',
            'post': 'yes',
        }
        self.assertEqual(Profile.objects.exclude(username=self.superuser.username).count(), 2)
        address = reverse('admin:aklub_profile_changelist')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=address)
        self.assertEqual(Profile.objects.exclude(username=self.superuser.username).count(), 0)
