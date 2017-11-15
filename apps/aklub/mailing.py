# -*- coding: utf-8 -*-
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2013 o.s. Auto*Mat
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
import copy
import datetime

from aklub import autocom
from aklub.models import Communication, Payment, TaxConfirmation, UserInCampaign, UserProfile

from django.contrib import messages
from django.utils.translation import ugettext as _
"""Mailing"""


def create_fake_userincampaign(sending_user):
    # create fake values
    userprofile = UserProfile(
        email=sending_user.email,
        first_name=sending_user.first_name,
        last_name=sending_user.last_name,
        sex='male',
        street=_('testing street'),
        city=_('testing city'),
        zip_code=12345,
        telephone="123 456 789",
        language='cs',
        addressment=None,
    )
    userincampaign = UserInCampaign(
        userprofile=userprofile,
        regular_amount=123456,
        regular_frequency="monthly",
        variable_symbol=12345678,
        last_payment=Payment(amount=12345),
    )
    return userincampaign


def get_template_subject_for_language(obj, language):
    if language == 'cs':
        return obj.template, obj.subject
    else:
        return obj.template_en, obj.subject_en


def report_emails(request, message, communications, level=messages.INFO):
    messages.add_message(request, level, message % ", ".join(communications))


def send_mass_communication(obj, users, sending_user, request, save=True):
    sent_communications = []
    unsent_communications = []
    for userincampaign in users:
        if userincampaign == "fake_user":
            userincampaign = create_fake_userincampaign(sending_user)

        template, subject = get_template_subject_for_language(obj, userincampaign.userprofile.language)
        if userincampaign.userprofile.is_active and subject and subject.strip() != '':
            if not subject or subject.strip() == '' or not template or template.strip('') == '':
                raise Exception("Message template is empty for one of the language variants.")
            if hasattr(obj, "attach_tax_confirmation") and not obj.attach_tax_confirmation:
                attachment = copy.copy(obj.attachment)
            else:
                tax_confirmations = TaxConfirmation.objects.filter(
                    user_profile=userincampaign.userprofile,
                    year=datetime.datetime.now().year - 1,
                )
                if len(tax_confirmations) > 0:
                    attachment = copy.copy(tax_confirmations[0].file)
                else:
                    attachment = None
            c = Communication(
                user=userincampaign, method=obj.method, date=datetime.datetime.now(),
                subject=subject,
                summary=autocom.process_template(template, userincampaign),
                attachment=attachment,
                note=_("Prepared by auto*mated mass communications at %s") % datetime.datetime.now(),
                send=True, created_by=sending_user, handled_by=sending_user,
                type='mass',
            )
            c.dispatch(save=save)
            if not c.dispatched:
                unsent_communications.append(userincampaign.userprofile.get_email_str())
            else:
                sent_communications.append(userincampaign.userprofile.get_email_str())
        else:
            unsent_communications.append(userincampaign.userprofile.get_email_str())
    if unsent_communications != []:
        report_emails(request, _("Following emails had errors: %s"), unsent_communications, level=messages.ERROR)
    report_emails(request, _("Emails sent to following addreses: %s"), sent_communications)
