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

from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.test import RequestFactory, TransactionTestCase
from django.test.utils import override_settings

from flexible_filter_conditions.models import NamedCondition

from freezegun import freeze_time

from model_mommy import mommy

from .. import mailing, models


@override_settings(
    CELERY_ALWAYS_EAGER=True,
)
class MailingTest(TransactionTestCase):
    fixtures = ['conditions', 'users']

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('')
        setattr(self.request, 'session', 'session')
        messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', messages)
        self.unit = mommy.make(
            "aklub.administrativeunit",
            name="test_unit",
            from_email_str="<example@some.com>",
            from_email_address="example@some.com",
        )

    @freeze_time("2015-5-1")
    def test_mailing_fake_user(self):
        sending_user = mommy.make('aklub.userprofile', first_name="Testing", last_name="UserInCampaign")
        mommy.make("ProfileEmail", user=sending_user, email="test@test.com", is_primary=True)
        inter_category = mommy.make('interactions.interactioncategory', category='testcategory')
        inter_type = mommy.make('interactions.interactiontype', category=inter_category, name='testtype', send_email=True)
        condition = mommy.make("flexible_filter_conditions.NamedCondition")

        c = mommy.make(
            "aklub.AutomaticCommunication",
            condition=condition,
            template="Testing template",
            subject="Testing email",
            method_type=inter_type,
            administrative_unit=self.unit,
        )
        # test userprofile email
        mailing.send_fake_communication(c, sending_user, self.request)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['<example@some.com>'])
        self.assertEqual(msg.subject, 'Testing email')
        self.assertIn("Testing template", msg.body)

    @freeze_time("2015-5-1")
    def test_mailing_fake_company(self):
        sending_company = mommy.make('aklub.companyprofile', name="Testing Company")
        mommy.make(
            "aklub.companycontact",
            company=sending_company,
            email="test_company@test.com",
            is_primary=True,
            administrative_unit=self.unit,
        )

        inter_category = mommy.make('interactions.interactioncategory', category='testcategory')
        inter_type = mommy.make('interactions.interactiontype', category=inter_category, name='testtype', send_email=True)
        condition = mommy.make("flexible_filter_conditions.NamedCondition")

        c = mommy.make(
            "aklub.AutomaticCommunication",
            condition=condition,
            template="Testing template",
            subject="Testing email",
            method_type=inter_type,
            administrative_unit=self.unit,
        )
        mailing.send_fake_communication(c, sending_company, self.request)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['<example@some.com>'])
        self.assertEqual(msg.subject, 'Testing email')
        self.assertIn("Testing template", msg.body)

    @freeze_time("2015-5-1")
    def test_mailing_fail_user(self):
        sending_user = models.UserProfile.objects.create(
            first_name="Testing",
            last_name="UserInCampaign",
        )
        inter_category = mommy.make('interactions.interactioncategory', category='testcategory')
        inter_type = mommy.make('interactions.interactiontype', category=inter_category, name='testtype', send_email=True)
        mommy.make("ProfileEmail", user=sending_user, email="test@test.com", is_primary=True)
        c = models.AutomaticCommunication.objects.create(
            condition=NamedCondition.objects.create(),
            template="Testing template",
            subject="Testing email",
            subject_en="Testing email",
            method_type=inter_type,
            administrative_unit=self.unit,
        )
        u = models.Profile.objects.get(email='test.user1@email.cz')
        with self.assertRaises(Exception) as ex:
            mailing.send_communication_sync(c.id, 'automatic', u.id, sending_user.id)
        self.assertEqual(str(ex.exception), "Message template is empty for one of the language variants.")

    @freeze_time("2015-5-1")
    def test_mailing_fail_company(self):
        sending_company = mommy.make('aklub.companyprofile', name="Testing Company")
        mommy.make(
            "aklub.companycontact",
            company=sending_company,
            email="test_company@test.com",
            is_primary=True,
            administrative_unit=self.unit,
        )
        inter_category = mommy.make('interactions.interactioncategory', category='testcategory')
        inter_type = mommy.make('interactions.interactiontype', category=inter_category, name='testtype', send_email=True)
        c = models.AutomaticCommunication.objects.create(
            condition=NamedCondition.objects.create(),
            template="Testing template",
            subject="Testing email",
            subject_en="Testing email",
            method_type=inter_type,
            administrative_unit=self.unit,
        )
        u = models.Profile.objects.get(email='test.user1@email.cz')
        with self.assertRaises(Exception) as ex:
            mailing.send_communication_sync(c.id, 'automatic', u.id, sending_company.id)
        self.assertEqual(str(ex.exception), "Message template is empty for one of the language variants.")

    @freeze_time("2015-5-1")
    def test_mailing_user(self):
        sending_user = models.UserProfile.objects.create(
            first_name="Testing",
            last_name="UserInCampaign",
        )
        mommy.make("ProfileEmail", user=sending_user, email="test@test.com", is_primary=True)
        inter_category = mommy.make('interactions.interactioncategory', category='testcategory')
        inter_type = mommy.make('interactions.interactiontype', category=inter_category, name='testtype', send_email=True)
        c = models.MassCommunication.objects.create(
            template="Testing template",
            template_en="Testing template en",
            subject="Testing email",
            subject_en="Testing email en",
            method_type=inter_type,
            date="2015-5-1",
            administrative_unit=self.unit,
        )
        c.send_to_users.set(models.Profile.objects.filter(pk__in=[3, 2978, 2979]))
        mailing.send_mass_communication(c, sending_user, self.request)
        self.assertEqual(len(mail.outbox), 3)
        mail.outbox.sort(key=lambda m: m.recipients()[0])
        msg = mail.outbox[2]
        self.assertEqual(msg.recipients(), ['without_payments@email.cz'])
        self.assertEqual(msg.subject, 'Testing email')
        self.assertIn("Testing template", msg.body)
        msg = mail.outbox[1]
        self.assertEqual(msg.recipients(), ['test.user@email.cz'])
        self.assertEqual(msg.subject, 'Testing email')
        self.assertIn("Testing template", msg.body)
        msg1 = mail.outbox[0]
        self.assertEqual(msg1.recipients(), ['test.user1@email.cz'])
        self.assertEqual(msg1.subject, 'Testing email en')
        self.assertIn("Testing template", msg1.body)

    @freeze_time("2015-5-1")
    def test_mailing_company(self):
        sending_user = models.UserProfile.objects.create(
            first_name="Testing",
            last_name="UserInCampaign",
        )
        mommy.make("ProfileEmail", user=sending_user, email="test@test.com", is_primary=True)

        company1 = mommy.make('aklub.companyprofile', name="Testing Company")
        mommy.make(
            "aklub.companycontact",
            company=company1,
            email="test_company@test.com",
            is_primary=True,
            administrative_unit=self.unit,
        )
        company2 = mommy.make('aklub.companyprofile', name="Testing Company2", language='en')
        mommy.make(
            "aklub.companycontact",
            company=company2,
            email="test_company2@test.com",
            is_primary=True,
            administrative_unit=self.unit,
        )
        inter_category = mommy.make('interactions.interactioncategory', category='testcategory')
        inter_type = mommy.make('interactions.interactiontype', category=inter_category, name='testtype', send_email=True)
        c = models.MassCommunication.objects.create(
            template="Testing template",
            template_en="Testing template en",
            subject="Testing email",
            subject_en="Testing email en",
            method_type=inter_type,
            date="2015-5-1",
            administrative_unit=self.unit,
        )
        c.send_to_users.set([company1.id, company2.id])
        mailing.send_mass_communication(c, sending_user, self.request)
        self.assertEqual(len(mail.outbox), 2)
        mail.outbox.sort(key=lambda m: m.recipients()[0])
        msg = mail.outbox[1]
        self.assertEqual(msg.recipients(), ['test_company@test.com'])
        self.assertEqual(msg.subject, 'Testing email')
        self.assertIn("Testing template", msg.body)
        msg1 = mail.outbox[0]
        self.assertEqual(msg1.recipients(), ['test_company2@test.com'])
        self.assertEqual(msg1.subject, 'Testing email en')
        self.assertIn("Testing template", msg1.body)
