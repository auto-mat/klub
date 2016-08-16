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

from aklub import autocom
from aklub.models import Communication, TaxConfirmation, UserInCampaign, Payment, UserProfile
from django.contrib.auth.models import User as DjangoUser
from django.utils.translation import ugettext as _
import copy
import datetime

"""Mailing"""


def send_mass_communication(obj, users, sending_user, save=True):
    for userincampaign in users:
        if userincampaign == "fake_user":
            # create fake values
            user = DjangoUser(
                email=sending_user.email,
                first_name=sending_user.first_name,
                last_name=sending_user.last_name,
            )
            userprofile = UserProfile(
                user=user,
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
        if userincampaign.userprofile.language == 'cs':
            template, subject = obj.template, obj.subject
        else:
            template, subject = obj.template_en, obj.subject_en
        if userincampaign.userprofile.user.is_active and subject.strip() != '':
            if not subject or subject.strip() == '' or not template or template.strip('') == '':
                raise Exception("Message template is empty for one of the language variants.")
            if hasattr(obj, "attach_tax_confirmation") and not obj.attach_tax_confirmation:
                attachment = copy.copy(obj.attachment)
            else:
                tax_confirmations = TaxConfirmation.objects.filter(
                    user=userincampaign, year=datetime.datetime.now().year-1)
                if len(tax_confirmations) > 0:
                    attachment = copy.copy(tax_confirmations[0].file)
                else:
                    attachment = None
            c = Communication(user=userincampaign, method=obj.method, date=datetime.datetime.now(),
                              subject=subject,
                              summary=autocom.process_template(template, userincampaign),
                              attachment=attachment,
                              note=_("Prepared by auto*mated mass communications at %s") % datetime.datetime.now(),
                              send=True, created_by=sending_user, handled_by=sending_user,
                              type='mass')
            c.dispatch(save=save)
