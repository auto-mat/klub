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
from aklub.models import Communication, TaxConfirmation, User, Payment
import datetime
from aklub import autocom
from django.utils.translation import ugettext as _

"""Mailing"""


def send_mass_communication(obj, users, request, save=True):
    for user in users:
        if user == "fake_user":
            # create fake values
            user = User(
                email=request.user.email,
                language='cs',
                active=True,
                addressment=None,
                sex='male',
                firstname=request.user.first_name,
                surname=request.user.last_name,
                street=_('testing street'),
                city=_('testing city'),
                zip_code=12345,
                telephone="123 456 789",
                regular_amount=123456,
                regular_frequency="monthly",
                variable_symbol=12345678,
                last_payment=Payment(amount=12345),
                )
        if user.language == 'cs':
            template, subject = obj.template, obj.subject
        else:
            template, subject = obj.template_en, obj.subject_en
        if user.active and subject.strip() != '':
            if template.strip('') == '':
                raise Exception("Message template is empty for one of the language variants.")
            if hasattr(obj, "attach_tax_confirmation") and not obj.attach_tax_confirmation:
                attachment = copy.copy(obj.attachment)
            else:
                tax_confirmations = TaxConfirmation.objects.filter(
                    user=user, year=datetime.datetime.now().year-1)
                if len(tax_confirmations) > 0:
                    attachment = copy.copy(tax_confirmations[0].file)
                else:
                    attachment = None
            c = Communication(user=user, method=obj.method, date=datetime.datetime.now(),
                              subject=subject,
                              summary=autocom.process_template(template, user),
                              attachment=attachment,
                              note=_("Prepared by auto*mated mass communications at %s") % datetime.datetime.now(),
                              send=True, created_by=request.user, handled_by=request.user,
                              type='mass')
            c.dispatch(save=save)
