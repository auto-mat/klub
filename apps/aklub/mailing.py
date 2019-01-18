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

from django.contrib import messages
from django.utils.translation import ugettext as _

from . import autocom
from .models import Communication, MassCommunication, Payment, TaxConfirmation, UserInCampaign, UserProfile
"""Mailing"""


def create_fake_userincampaign(sending_user):
    # create fake values
    userprofile = sending_user
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


def send_mass_communication(mass_communication, users, sending_user, request, save=True):
    from .tasks import send_mass_communication_task
    for userincampaign in users:
        if userincampaign == 'fake_user':
            userincampaign_id = 'fake_user'
        else:
            userincampaign_id = userincampaign.id
        send_mass_communication_task.apply_async(args=(mass_communication.id, userincampaign_id, sending_user.id, save))
    messages.add_message(request, messages.INFO, _("Communication sending was queued for %s users") % len(users))


def send_communication_sync(mass_communication_id, userincampaign_id, sending_user_id, save=True):
    sending_user = UserProfile.objects.get(id=sending_user_id)
    if userincampaign_id == "fake_user":
        userincampaign = create_fake_userincampaign(sending_user)
    else:
        userincampaign = UserInCampaign.objects.get(id=userincampaign_id)
    mass_communication = MassCommunication.objects.get(id=mass_communication_id)

    template, subject = get_template_subject_for_language(mass_communication, userincampaign.userprofile.language)
    if userincampaign.userprofile.is_active and subject and subject.strip() != '':
        if not subject or subject.strip() == '' or not template or template.strip('') == '':
            raise Exception("Message template is empty for one of the language variants.")
        if hasattr(mass_communication, "attach_tax_confirmation") and not mass_communication.attach_tax_confirmation:
            attachment = copy.copy(mass_communication.attachment)
        else:
            tax_confirmations = TaxConfirmation.mass_communicationects.filter(
                user_profile=userincampaign.userprofile,
                year=datetime.datetime.now().year - 1,
            )
            if len(tax_confirmations) > 0:
                attachment = copy.copy(tax_confirmations[0].file)
            else:
                attachment = None
        c = Communication(
            user=userincampaign, method=mass_communication.method, date=datetime.datetime.now(),
            subject=autocom.process_template(subject, userincampaign),
            summary=autocom.process_template(template, userincampaign),
            attachment=attachment,
            note=_("Prepared by auto*mated mass communications at %s") % datetime.datetime.now(),
            send=True, created_by=sending_user, handled_by=sending_user,
            type='mass',
        )
        c.dispatch(save=save)
