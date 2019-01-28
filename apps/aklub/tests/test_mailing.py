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
from django.test import RequestFactory, TestCase

from freezegun import freeze_time

from .. import mailing, models


class MailingTest(TestCase):
    fixtures = ['conditions', 'users']

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('')
        setattr(self.request, 'session', 'session')
        messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', messages)

    @freeze_time("2015-5-1")
    def test_mailing_fake_user(self):
        sending_user = models.UserProfile.objects.create(
            first_name="Testing",
            last_name="UserInCampaign",
            email="test@test.com",
        )
        c = models.AutomaticCommunication.objects.create(
            condition=models.Condition.objects.create(),
            template="Testing template",
            subject="Testing email",
            method="email",
        )
        mailing.send_communication_sync(c.id, "automatic", "fake_user", sending_user.id)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test@test.com'])
        self.assertEqual(msg.subject, 'Testing email')
        self.assertIn("Testing template", msg.body)

    @freeze_time("2015-5-1")
    def test_mailing_fail(self):
        sending_user = models.UserProfile.objects.create(
            first_name="Testing",
            last_name="UserInCampaign",
            email="test@test.com",
        )
        c = models.AutomaticCommunication.objects.create(
            condition=models.Condition.objects.create(),
            template="Testing template",
            subject="Testing email",
            subject_en="Testing email",
            method="email",
        )
        u = models.UserInCampaign.objects.get(userprofile__email='test.user1@email.cz')
        with self.assertRaises(Exception) as ex:
            mailing.send_communication_sync(c.id, 'automatic', u.id, sending_user.id)
        self.assertEqual(str(ex.exception), "Message template is empty for one of the language variants.")

    @freeze_time("2015-5-1")
    def test_mailing(self):
        sending_user = models.UserProfile.objects.create(
            first_name="Testing",
            last_name="UserInCampaign",
            email="test@test.com",
        )
        c = models.AutomaticCommunication.objects.create(
            condition=models.Condition.objects.create(),
            template="Testing template",
            template_en="Testing template en",
            subject="Testing email",
            subject_en="Testing email en",
            method="email",
        )

        users = models.UserInCampaign.objects.filter(userprofile__email='without_payments@email.cz')
        for u in users:
            mailing.send_communication_sync(c.id, 'automatic', u.id, sending_user.id)
        self.assertEqual(len(mail.outbox), 2)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['without_payments@email.cz'])
        self.assertEqual(msg.subject, 'Testing email')
        self.assertIn("Testing template", msg.body)
        mail.outbox = []

        users = models.UserInCampaign.objects.filter(userprofile__email='without_payments@email.cz')
        for u in users:
            mailing.send_communication_sync(c.id, 'automatic', u.id, sending_user.id)
        self.assertEqual(len(mail.outbox), 2)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['without_payments@email.cz'])
        self.assertEqual(msg.subject, 'Testing email')
        self.assertIn("Testing template", msg.body)
        mail.outbox = []

        u = models.UserInCampaign.objects.get(userprofile__email='test.user@email.cz')
        mailing.send_communication_sync(c.id, 'automatic', u.id, sending_user.id)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test.user@email.cz'])
        self.assertEqual(msg.subject, 'Testing email')
        self.assertIn("Testing template", msg.body)
        mail.outbox = []

        u = models.UserInCampaign.objects.get(userprofile__email='test.user1@email.cz')
        mailing.send_communication_sync(c.id, 'automatic', u.id, sending_user.id)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test.user1@email.cz'])
        self.assertEqual(msg.subject, 'Testing email en')
        self.assertIn("Testing template", msg.body)
