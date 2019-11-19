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

import pathlib
import re
from datetime import datetime

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

from .recipes import donor_payment_channel_recipe, generic_profile_recipe, user_profile_recipe
from .test_admin_helper import TestProfilePostMixin
from .utils import RunCommitHooksMixin
from .utils import print_response  # noqa
from .. import admin
from .. models import (
    AccountStatements, AutomaticCommunication, BankAccount,
    CompanyProfile, DonorPaymentChannel, Event, Interaction, MassCommunication,
    Preference, Profile, TaxConfirmation, Telephone, UserBankAccount, UserProfile,
    UserYearPayments,
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
    exclude_apps = ['helpdesk', 'postoffice', 'advanced_filters', 'celery_monitor']

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
        foo_user = donor_payment_channel_recipe.make(user=_foo_user)
        bar_user = donor_payment_channel_recipe.make(user=_bar_user)
        mommy.make("aklub.Payment", amount=350, date="2016-01-02", user_donor_payment_channel=foo_user, type="cash")
        mommy.make("aklub.Payment", amount=130, date="2016-01-02", user_donor_payment_channel=bar_user, type="cash")
        model_admin = django_admin.site._registry[TaxConfirmation]
        request = self.post_request({})
        response = model_admin.generate(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/aklub/taxconfirmation/")
        self.assertEqual(TaxConfirmation.objects.get(user_profile__id=2978, year=2016).amount, 350)
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
        mommy.make("aklub.Condition", id=1)
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

    def test_pair_variable_symbols(self):
        """ Test pair_variable_symbols action """
        payment_channel = donor_payment_channel_recipe.make(VS=123)
        payment = mommy.make("aklub.Payment", VS=123)
        account_statement = mommy.make(
            "aklub.AccountStatements",
            payment_set=[payment],
        )
        request = self.post_request()
        admin.pair_variable_symbols(None, request, [account_statement])
        payment.refresh_from_db()
        self.assertEqual(payment.user_donor_payment_channel, payment_channel)
        self.assertEqual('Variabilní symboly úspěšně spárovány.', request._messages._queued_messages[0].message)

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


class AdminImportExportTests(CreateSuperUserMixin, TestCase):
    fixtures = ['conditions', 'users', 'communications']

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

    def test_paymetnchannel_export(self):
        address = "/aklub/donorpaymentchannel/export/"
        post_data = {
            'file_format': 0,
        }
        response = self.client.post(address, post_data)
        self.assertContains(
            response,
            '2978,2,2978,,Test,User,,male,test.user@email.cz,,Praha 4,,120127010,,0,regular,monthly,2015-12-16 17:22:30,1,cs,,,,100,',
            # TODO: check transforming following data into another models
            # ',Test,User,,male,,test.user@email.cz,,Praha 4,,120127010,0,1,regular,monthly,2015-12-16 17:22:30,'
            # '"Domníváte se, že má město po zprovoznění tunelu Blanka omezit tranzit historickým centrem? '
            # 'Ano, hned se zprovozněním tunelu",editor,1,cs,,,,0,0.0,100',
        )

    def create_profiles(self):
        profiles_data = [
            {
                'type': 'user',
                'model_name': UserProfile._meta.model_name,
                'vs': '140147010',
                'extra_fields': {
                    'sex': 'male',
                    'title_before': 'Ing.',
                    'title_after': 'Phdr.',
                    'first_name': 'Foo',
                    'last_name': 'Bar',
                },
            },
            {
                'type': 'company',
                'model_name': CompanyProfile._meta.model_name,
                'vs': '150157010',
                'extra_fields': {
                    'crn': '11223344',
                    'tin': '55667788',
                    'name': 'Company',
                },
            },
        ]
        # event = mommy.make(
        #     'aklub.Event',
        #     name='Klub přátel Auto*Matu',
        #     created='2015-12-16',
        #     slug='klub',
        #     allow_statistics=True,
        #     darujme_api_id=38571205,
        #     darujme_project_id=38571205,
        #     acquisition_campaign=True,
        #     enable_signing_petitions=True,
        #     enable_registration=True,
        #     darujme_name='Klub přátel Auto*Matu',
        # )
        administrative_units = ['AU1', 'AU2']
        event = Event.objects.get(pk=2)
        for index, profile_type in enumerate(profiles_data):
            model_name = profile_type['model_name']
            generic_profile_recipe._model = 'aklub.{}'.format(model_name)
            fields = {
                'username': 'test.{}'.format(model_name),
                'email': 'test.{0}@{0}.test'.format(model_name),
            }
            fields.update(profile_type['extra_fields'])
            user = generic_profile_recipe.make(**fields)
            administrative_unit = mommy.make(
                'aklub.AdministrativeUnit',
                id=index,
                name=administrative_units[index],
            )
            user.administrated_units.add(administrative_unit)
            mommy.make(
                'aklub.Interaction',
                dispatched=False,
                date='2016-2-9',
                user=user,
            )
            mommy.make(
                'aklub.TaxConfirmation',
                user_profile=user,
                year=2014,
                amount=2014,
            )
            mommy.make(
                'aklub.DonorPaymentChannel',
                user=user,
                expected_date_of_first_payment=datetime.strptime('2015-12-16', '%Y-%m-%d'),
                no_upgrade=False,
                registered_support='2015-12-16T18:22:30.128',
                regular_amount=100,
                regular_frequency='monthly',
                regular_payments='regular',
                event=event,
                VS=profile_type['vs'],
            )
            mommy.make(
                'aklub.Preference',
                user=user,
                administrative_unit=administrative_unit,
                newsletter_on=True,
                call_on=True,
                challenge_on=True,
                letter_on=True,
                send_mailing_lists=False,
                public=False,
            )
            user.administrative_units.add(administrative_unit)

    def test_profile_export(self):
        """ Test ProfileAdmin admin model export """
        self.create_profiles()
        address = reverse('admin:aklub_profile_export')
        post_data = {
            'file_format': 0,
        }
        response = self.client.post(address, post_data)
        self.assertContains(
            response,
            ''.join(
                [
                    '0,test.userprofile@userprofile.test,,',
                    '"VS:140147010\nevent:Klub přátel Auto*Matu\nbank_accout:\nuser_bank_account:\n\n",',
                    'test.userprofile,2016-09-16 16:22:30,,,en,,Praha 4,Česká republika,,1,,,Česká republika,',
                    ',,False,,False,True,True,True,True,,,,male,Phdr.,Foo,Bar,Ing.,,,userprofile,',
                ],
            ),
        )
        self.assertContains(
            response,
            ''.join(
                [
                    '1,test.companyprofile@companyprofile.test,,',
                    '"VS:150157010\nevent:Klub přátel Auto*Matu\nbank_accout:\nuser_bank_account:\n\n",',
                    'test.companyprofile,2016-09-16 16:22:30,,,en,,Praha 4,Česká republika,,1,,,Česká republika,',
                    ',,False,,False,True,True,True,True,Company,11223344,55667788,,,,,,,,companyprofile,',
                ],
            ),
        )

    def test_user_profile_export(self):
        """ Test UserProfileAdmin admin model export """
        self.create_profiles()
        address = reverse('admin:aklub_userprofile_export')
        post_data = {
            'file_format': 0,
        }
        response = self.client.post(address, post_data)
        self.assertContains(
            response,
            ''.join(
                [
                    '0,test.userprofile@userprofile.test,,',
                    '"VS:140147010\nevent:Klub přátel Auto*Matu\nbank_accout:\nuser_bank_account:\n\n",',
                    'test.userprofile,2016-09-16 16:22:30,,,en,,Praha 4,Česká republika,,1,,,Česká republika,',
                    ',,False,,False,True,True,True,True,Ing.,Foo,Bar,Phdr.,male,,,',
                ],
            ),
        )

    def test_company_profile_export(self):
        """ Test CompanyProfileAdmin admin model export """
        self.create_profiles()
        address = reverse('admin:aklub_companyprofile_export')
        post_data = {
            'file_format': 0,
        }
        response = self.client.post(address, post_data)
        self.assertContains(
            response,
            ''.join(
                [
                    '1,test.companyprofile@companyprofile.test,,',
                    '"VS:150157010\nevent:Klub přátel Auto*Matu\nbank_accout:\nuser_bank_account:\n\n",',
                    'test.companyprofile,2016-09-16 16:22:30,,,en,,Praha 4,Česká republika,,1,,,Česká republika,',
                    ',,False,,False,True,True,True,True,Company,11223344,55667788',
                ],
            ),
        )

    def test_profile_import(self):
        """ Test Profile admin model import """
        administrative_units = ['AU1', 'AU2']
        for index, au in enumerate(administrative_units, 1):
            mommy.make(
                'aklub.AdministrativeUnit',
                id=index,
                name=administrative_units[index - 1],
            )

        p = pathlib.PurePath(__file__)
        csv_file_create_profiles = p.parents[1] / 'test_data' / 'create_profiles.csv'
        address = reverse('admin:aklub_profile_import')
        with open(csv_file_create_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'test.companyprofile@companyprofile.test',
            html=True,
        )
        self.assertContains(
            response,
            'test.userprofile@userprofile.test',
            html=True,
        )
        self.assertContains(
            response,
            'male',
            html=True,
        )
        self.assertContains(
            response,
            '11223344',
            html=True,
        )
        self.assertContains(
            response,
            'Company',
            html=True,
        )

        # Create model
        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )
        file_name = [val.split('=')[-1].replace('"', '') for val in result.group(0).split(' ') if 'value' in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': csv_file_create_profiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_profile_process_import')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_profile_changelist'))

        user_profile = Profile.objects.filter(email='test.userprofile@userprofile.test')
        self.assertEqual(user_profile.count(), 1)
        self.assertEqual(user_profile[0].sex, 'male')
        donor = DonorPaymentChannel.objects.filter(user=user_profile[0])
        self.assertEqual(donor.count(), 1)
        self.assertEqual(donor[0].VS, '150157010')
        self.assertEqual(donor[0].event.name, 'Zažít město jinak')
        bank_account = BankAccount.objects.filter(bank_account_number='2233445566/0100')
        self.assertEqual(bank_account.count(), 1)
        self.assertEqual(donor[0].money_account, bank_account[0])
        user_bank_account = UserBankAccount.objects.filter(bank_account_number='9988776655/0100')
        self.assertEqual(user_bank_account.count(), 1)
        self.assertEqual(donor[0].user_bank_account, user_bank_account[0])
        self.assertEqual(user_profile[0].polymorphic_ctype, ContentType.objects.get(model='userprofile'))
        self.assertEqual(user_profile[0].username, 'test.userprofile')
        self.assertEqual(user_profile[0].title_before, 'Ing.')
        self.assertEqual(user_profile[0].title_after, 'Phdr.')
        self.assertEqual(user_profile[0].first_name, 'First_name_userprofile')
        self.assertEqual(user_profile[0].last_name, 'Last_name_userprofile')
        preference = Preference.objects.filter(user=user_profile[0])
        self.assertEqual(preference.count(), 1)
        self.assertEqual(preference[0].send_mailing_lists, True)
        self.assertEqual(preference[0].letter_on, True)

        company_profile = Profile.objects.filter(email='test.companyprofile@companyprofile.test')
        self.assertEqual(company_profile.count(), 1)
        self.assertEqual(company_profile[0].crn, '11223344')
        self.assertEqual(company_profile[0].tin, '55667788')
        self.assertEqual(company_profile[0].name, 'Company')
        donor = DonorPaymentChannel.objects.filter(user=company_profile[0])
        self.assertEqual(donor.count(), 1)
        self.assertEqual(donor[0].VS, '1960243939')
        self.assertEqual(donor[0].event.name, 'Zažít město jinak')
        bank_account = BankAccount.objects.filter(bank_account_number='1234567890/0200')
        self.assertEqual(bank_account.count(), 1)
        self.assertEqual(donor[0].money_account, bank_account[0])
        user_bank_account = UserBankAccount.objects.filter(bank_account_number='5554443331/0900')
        self.assertEqual(user_bank_account.count(), 1)
        self.assertEqual(donor[0].user_bank_account, user_bank_account[0])
        self.assertEqual(company_profile[0].polymorphic_ctype, ContentType.objects.get(model='companyprofile'))
        self.assertEqual(company_profile[0].username, 'test.companyprofile')
        preference = Preference.objects.filter(user=user_profile[0])
        self.assertEqual(preference.count(), 1)
        self.assertEqual(preference[0].send_mailing_lists, True)
        self.assertEqual(preference[0].letter_on, True)

        # Update model
        p = pathlib.PurePath(__file__)
        csv_file_update_profiles = p.parents[1] / 'test_data' / 'update_profiles.csv'
        address = reverse('admin:aklub_profile_import')
        with open(csv_file_update_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)

        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )
        file_name = [val.split("=")[-1].replace('"', '') for val in result.group(0).split(" ") if "value" in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': csv_file_create_profiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_profile_process_import')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_profile_changelist'))

        user_profile = Profile.objects.filter(email='test.userprofile@userprofile.test')
        self.assertEqual(user_profile.count(), 1)
        self.assertEqual(user_profile[0].sex, 'female')
        donor = DonorPaymentChannel.objects.filter(user=user_profile[0])
        self.assertEqual(donor.count(), 1)
        self.assertEqual(donor[0].VS, '150157010')
        self.assertEqual(donor[0].event.name, 'Zažít město jinak')
        bank_account = BankAccount.objects.filter(bank_account_number='2233445566/0100')
        self.assertEqual(bank_account.count(), 1)
        self.assertEqual(donor[0].money_account, bank_account[0])
        user_bank_account = UserBankAccount.objects.filter(bank_account_number='1111111111/0100')
        self.assertEqual(user_bank_account.count(), 1)
        self.assertEqual(user_profile[0].polymorphic_ctype, ContentType.objects.get(model='userprofile'))
        self.assertEqual(user_profile[0].username, 'test.userprofile')
        self.assertEqual(user_profile[0].title_before, 'Mgr.')
        preference = Preference.objects.filter(user=user_profile[0])
        self.assertEqual(preference.count(), 1)
        self.assertEqual(preference[0].send_mailing_lists, False)
        self.assertEqual(preference[0].letter_on, False)

        company_profile = Profile.objects.filter(email='test.companyprofile@companyprofile.test')
        self.assertEqual(company_profile.count(), 1)
        self.assertEqual(company_profile[0].crn, '22334455')
        self.assertEqual(company_profile[0].tin, '99887766')
        self.assertEqual(company_profile[0].name, 'Update Company')
        donor = DonorPaymentChannel.objects.filter(user=company_profile[0])
        self.assertEqual(donor.count(), 1)
        self.assertEqual(donor[0].event.name, 'Zažít město jinak')
        bank_account = BankAccount.objects.filter(bank_account_number='3333333333/0300')
        self.assertEqual(bank_account.count(), 1)
        self.assertEqual(donor[0].money_account, bank_account[0])
        user_bank_account = UserBankAccount.objects.filter(bank_account_number='5554443331/0900')
        self.assertEqual(user_bank_account.count(), 1)
        self.assertEqual(donor[0].user_bank_account, user_bank_account[0])
        self.assertEqual(company_profile[0].polymorphic_ctype, ContentType.objects.get(model='companyprofile'))
        self.assertEqual(company_profile[0].username, 'test.companyprofile')
        preference = Preference.objects.filter(user=company_profile[0])
        self.assertEqual(preference.count(), 1)
        self.assertEqual(preference[0].send_mailing_lists, False)
        self.assertEqual(preference[0].letter_on, False)

    def test_profile_minimal_fields_import(self):
        """ Test Profile admin model minimal fields import """
        p = pathlib.PurePath(__file__)
        csv_file = 'create_profiles_minimal_fields.csv'
        csv_file_create_profiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_profile_import')
        with open(csv_file_create_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '11223344',
            html=True,
        )
        self.assertContains(
            response,
            'male',
            html=True,
        )

        # Create model
        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )
        file_name = [val.split('=')[-1].replace('"', '') for val in result.group(0).split(' ') if 'value' in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': csv_file_create_profiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_profile_process_import')
        number_of_new_profiles = 2
        profile_count = Profile.objects.count() + number_of_new_profiles
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_profile_changelist'))
        self.assertEqual(profile_count, Profile.objects.count())

    def test_userprofile_import(self):
        """ Test UserProfile admin model import """
        administrative_units = ['AU1', 'AU2']
        for index, au in enumerate(administrative_units, 1):
            mommy.make(
                'aklub.AdministrativeUnit',
                id=index,
                name=administrative_units[index - 1],
            )

        p = pathlib.PurePath(__file__)
        csv_file = 'create_user_profiles.csv'
        csv_file_create_user_profiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_userprofile_import')
        with open(csv_file_create_user_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'test.userprofile@userprofile.test',
            html=True,
        )
        self.assertContains(
            response,
            'male',
            html=True,
        )

        # Create model
        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )
        file_name = [val.split('=')[-1].replace('"', '') for val in result.group(0).split(' ') if 'value' in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': csv_file_create_user_profiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_userprofile_process_import')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_userprofile_changelist'))

        user_profile = Profile.objects.filter(email='test.userprofile@userprofile.test')
        self.assertEqual(user_profile.count(), 1)
        self.assertEqual(user_profile[0].sex, 'male')
        donor = DonorPaymentChannel.objects.filter(user=user_profile[0])
        self.assertEqual(donor.count(), 1)
        self.assertEqual(donor[0].VS, '150157010')
        self.assertEqual(donor[0].event.name, 'Zažít město jinak')
        bank_account = BankAccount.objects.filter(bank_account_number='2233445566/0100')
        self.assertEqual(bank_account.count(), 1)
        self.assertEqual(donor[0].money_account, bank_account[0])
        user_bank_account = UserBankAccount.objects.filter(bank_account_number='9988776655/0100')
        self.assertEqual(user_bank_account.count(), 1)
        self.assertEqual(donor[0].user_bank_account, user_bank_account[0])
        self.assertEqual(user_profile[0].polymorphic_ctype, ContentType.objects.get(model='userprofile'))
        self.assertEqual(user_profile[0].username, 'test.userprofile')
        self.assertEqual(user_profile[0].title_before, 'Ing.')
        self.assertEqual(user_profile[0].title_after, 'Phdr.')
        self.assertEqual(user_profile[0].first_name, 'First_name_userprofile')
        self.assertEqual(user_profile[0].last_name, 'Last_name_userprofile')
        preference = Preference.objects.filter(user=user_profile[0])
        self.assertEqual(preference.count(), 1)
        self.assertEqual(preference[0].send_mailing_lists, True)
        self.assertEqual(preference[0].letter_on, True)

        # Update model
        p = pathlib.PurePath(__file__)
        csv_file = 'update_user_profiles.csv'
        csv_file_update_user_profiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_userprofile_import')
        with open(csv_file_update_user_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)

        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )
        file_name = [val.split("=")[-1].replace('"', '') for val in result.group(0).split(" ") if "value" in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': csv_file_update_user_profiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_userprofile_process_import')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_userprofile_changelist'))

        user_profile = Profile.objects.filter(email='test.userprofile@userprofile.test')
        self.assertEqual(user_profile.count(), 1)
        self.assertEqual(user_profile[0].sex, 'female')
        donor = DonorPaymentChannel.objects.filter(user=user_profile[0])
        self.assertEqual(donor.count(), 1)
        self.assertEqual(donor[0].VS, '150157010')
        self.assertEqual(donor[0].event.name, 'Zažít město jinak')
        bank_account = BankAccount.objects.filter(bank_account_number='2233445566/0100')
        self.assertEqual(bank_account.count(), 1)
        self.assertEqual(donor[0].money_account, bank_account[0])
        user_bank_account = UserBankAccount.objects.filter(bank_account_number='1111111111/0100')
        self.assertEqual(user_bank_account.count(), 1)
        self.assertEqual(user_profile[0].polymorphic_ctype, ContentType.objects.get(model='userprofile'))
        self.assertEqual(user_profile[0].username, 'test.userprofile')
        self.assertEqual(user_profile[0].title_before, 'Mgr.')
        preference = Preference.objects.filter(user=user_profile[0])
        self.assertEqual(preference.count(), 1)
        self.assertEqual(preference[0].send_mailing_lists, False)
        self.assertEqual(preference[0].letter_on, False)

    def test_userprofile_minimal_fields_import(self):
        """ Test UserProfile admin model minimal fields import """
        p = pathlib.PurePath(__file__)
        csv_file = 'create_user_profiles_minimal_fields.csv'
        csv_file_create_user_profiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_userprofile_import')
        with open(csv_file_create_user_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'male',
            html=True,
        )
        self.assertContains(
            response,
            'female',
            html=True,
        )

        # Create model
        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )
        file_name = [val.split('=')[-1].replace('"', '') for val in result.group(0).split(' ') if 'value' in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': csv_file_create_user_profiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_userprofile_process_import')
        number_of_new_user_profiles = 4
        user_profile_count = UserProfile.objects.count() + number_of_new_user_profiles
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_userprofile_changelist'))
        self.assertEqual(user_profile_count, UserProfile.objects.count())

    def test_companyprofile_minimal_fields_import(self):
        """ Test CompanyProfile admin model minimal fields import """
        p = pathlib.PurePath(__file__)
        csv_file = 'create_company_profiles_minimal_fields.csv'
        csv_file_create_company_profiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_companyprofile_import')
        with open(csv_file_create_company_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '11223344',
            html=True,
        )
        self.assertContains(
            response,
            '55667788',
            html=True,
        )

        # Create model
        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )
        file_name = [val.split('=')[-1].replace('"', '') for val in result.group(0).split(' ') if 'value' in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': csv_file_create_company_profiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_companyprofile_process_import')
        number_of_new_company_profiles = 4
        company_profile_count = CompanyProfile.objects.count() + number_of_new_company_profiles
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_companyprofile_changelist'))
        self.assertEqual(company_profile_count, CompanyProfile.objects.count())

    def test_companyprofile_import(self):
        """ Test CompanyProfile admin model import """
        administrative_units = ['AU1', 'AU2']
        for index, au in enumerate(administrative_units, 1):
            mommy.make(
                'aklub.AdministrativeUnit',
                id=index,
                name=administrative_units[index - 1],
            )

        p = pathlib.PurePath(__file__)
        csv_file = 'create_company_profiles.csv'
        csv_file_create_companyprofiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_companyprofile_import')
        with open(csv_file_create_companyprofiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'test.companyprofile@companyprofile.test',
            html=True,
        )
        self.assertContains(
            response,
            '11223344',
            html=True,
        )
        self.assertContains(
            response,
            'Company',
            html=True,
        )

        # Create model
        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )
        file_name = [val.split('=')[-1].replace('"', '') for val in result.group(0).split(' ') if 'value' in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': csv_file_create_companyprofiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_companyprofile_process_import')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_companyprofile_changelist'))

        company_profile = Profile.objects.filter(email='test.companyprofile@companyprofile.test')
        self.assertEqual(company_profile.count(), 1)
        self.assertEqual(company_profile[0].crn, '11223344')
        self.assertEqual(company_profile[0].tin, '55667788')
        self.assertEqual(company_profile[0].name, 'Company')
        donor = DonorPaymentChannel.objects.filter(user=company_profile[0])
        self.assertEqual(donor.count(), 1)
        self.assertEqual(donor[0].VS, '1960243939')
        self.assertEqual(donor[0].event.name, 'Zažít město jinak')
        bank_account = BankAccount.objects.filter(bank_account_number='1234567890/0200')
        self.assertEqual(bank_account.count(), 1)
        self.assertEqual(donor[0].money_account, bank_account[0])
        user_bank_account = UserBankAccount.objects.filter(bank_account_number='5554443331/0900')
        self.assertEqual(user_bank_account.count(), 1)
        self.assertEqual(donor[0].user_bank_account, user_bank_account[0])
        self.assertEqual(company_profile[0].polymorphic_ctype, ContentType.objects.get(model='companyprofile'))
        self.assertEqual(company_profile[0].username, 'test.companyprofile')
        preference = Preference.objects.filter(user=company_profile[0])
        self.assertEqual(preference.count(), 1)
        self.assertEqual(preference[0].send_mailing_lists, True)
        self.assertEqual(preference[0].letter_on, True)

        # Update model
        p = pathlib.PurePath(__file__)
        csv_file = 'update_company_profiles.csv'
        csv_file_update_company_profiles = p.parents[1] / 'test_data' / csv_file
        address = reverse('admin:aklub_companyprofile_import')
        with open(csv_file_update_company_profiles) as fp:
            post_data = {
                'import_file': fp,
                'input_format': 0,
            }
            response = self.client.post(address, post_data)

        result = re.search(
            r'<input type="hidden" name="import_file_name".*?>',
            response.rendered_content,
        )
        file_name = [val.split("=")[-1].replace('"', '') for val in result.group(0).split(" ") if "value" in val][0]
        post_data = {
            'import_file_name': file_name,
            'original_file_name': csv_file_update_company_profiles.name,
            'input_format': post_data['input_format'],
        }
        address = reverse('admin:aklub_companyprofile_process_import')
        response = self.client.post(address, post_data)
        self.assertRedirects(response, expected_url=reverse('admin:aklub_companyprofile_changelist'))

        company_profile = Profile.objects.filter(email='test.companyprofile@companyprofile.test')
        self.assertEqual(company_profile.count(), 1)
        self.assertEqual(company_profile[0].crn, '22334455')
        self.assertEqual(company_profile[0].tin, '99887766')
        self.assertEqual(company_profile[0].name, 'Update Company')
        donor = DonorPaymentChannel.objects.filter(user=company_profile[0])
        self.assertEqual(donor.count(), 1)
        self.assertEqual(donor[0].event.name, 'Zažít město jinak')
        bank_account = BankAccount.objects.filter(bank_account_number='3333333333/0300')
        self.assertEqual(bank_account.count(), 1)
        self.assertEqual(donor[0].money_account, bank_account[0])
        user_bank_account = UserBankAccount.objects.filter(bank_account_number='5554443331/0900')
        self.assertEqual(user_bank_account.count(), 1)
        self.assertEqual(donor[0].user_bank_account, user_bank_account[0])
        self.assertEqual(company_profile[0].polymorphic_ctype, ContentType.objects.get(model='companyprofile'))
        self.assertEqual(company_profile[0].username, 'test.companyprofile')
        preference = Preference.objects.filter(user=company_profile[0])
        self.assertEqual(preference.count(), 1)
        self.assertEqual(preference[0].send_mailing_lists, False)
        self.assertEqual(preference[0].letter_on, False)


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
