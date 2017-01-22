# -*- coding: utf-8 -*-
# Author: Hynek Hanke <hynek.hanke@auto-mat.cz>
#
# Copyright (C) 2010 o.s. Auto*Mat
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

"""Automatic communications for club management"""
import datetime
import logging
import string

from .models import AutomaticCommunication, Communication, UserInCampaign
logger = logging.getLogger(__name__)


def _localize_enum(descr, val, lang):
    for t in descr:
        if t[0] == val:
            # Hack! Here we should use the Gettext localization
            # based on the value of 'lang' -- this is however
            # not easy due to lazy translations and t[1] already
            # being wrapped by a foreign translator
            if lang == 'cs':
                return t[1].lower()
            else:
                # less wrong would be to retrieve the original untranslated version of t[1]...
                return t[0]
    # Translation not found
    return val


def process_template(template_string, user):
    template = string.Template(template_string)

    if user.userprofile.addressment and user.userprofile.addressment != '':
        addressment = user.userprofile.addressment
    else:
        if user.userprofile.language == 'cs':
            if user.userprofile.sex == 'male':
                addressment = u'člene Klubu přátel Auto*Matu'
            elif user.userprofile.sex == 'female':
                addressment = u'členko Klubu přátel Auto*Matu'
            else:
                addressment = u'člene/členko Klubu přátel Auto*Matu'
        else:
            addressment = u'member of the Auto*Mat friends club'
    # Make variable substitutions
    text = template.substitute(
        addressment=addressment,
        name=user.userprofile.user.first_name,
        firstname=user.userprofile.user.first_name,
        surname=user.userprofile.user.last_name,
        street=user.userprofile.street,
        city=user.userprofile.city,
        zipcode=user.userprofile.zip_code,
        email=user.userprofile.user.email,
        telephone=user.userprofile.telephone,
        regular_amount=user.regular_amount,
        regular_frequency=_localize_enum(UserInCampaign.REGULAR_PAYMENT_FREQUENCIES, user.regular_frequency, user.userprofile.language),
        var_symbol=user.variable_symbol,
        last_payment_amount=user.last_payment and user.last_payment.amount or None,
    )

    # Modify text according to gender
    # Example: Vazeny{y|a} {pane|pani} -> [male] -> Vazeny pane
    gender_text = ""
    o = 0
    i = 0
    while i < len(text):
        if text[i] == '{':
            gender_text += text[o:i]
            sep_pos = text.find('|', i)
            end_pos = text.find('}', i)
            assert sep_pos > i
            assert end_pos > sep_pos, "Wrong format of template, no separator | or after end mark }"
            male_variant = text[i + 1:sep_pos]
            female_variant = text[sep_pos + 1:end_pos]
            if user.userprofile.sex == 'male':
                gender_text += male_variant
            elif user.userprofile.sex == 'female':
                gender_text += female_variant
            else:
                gender_text += male_variant + "/" + female_variant
            o = end_pos + 1
            i = end_pos
        i += 1
    gender_text += text[o:]

    return gender_text


def check(users=None, action=None):
    if not users:
        users = UserInCampaign.objects.all()
    for auto_comm in AutomaticCommunication.objects.all():
        logger.info(
            u"Processin condition \"%s\" for autocom \"%s\", method: \"%s\", action: \"%s\"" % (
                auto_comm.condition,
                auto_comm,
                auto_comm.method,
                action,
            ),
        )

        filtered_users = users.filter(auto_comm.condition.get_query(action))
        for user in filtered_users:
            if auto_comm.only_once and auto_comm.sent_to_users.filter(pk=user.pk).exists():
                continue
            if user.userprofile.language == 'cs':
                template = auto_comm.template
                subject = auto_comm.subject
            else:
                template = auto_comm.template_en
                subject = auto_comm.subject_en
            if template and template != '':
                logger.info(u"Added new automatic communication \"%s\" for user \"%s\", action \"%s\"" % (auto_comm, user, action))
                c = Communication(
                    user=user, method=auto_comm.method, date=datetime.datetime.now(),
                    subject=subject, summary=process_template(template, user),
                    note="Prepared by auto*mated mailer at %s" % datetime.datetime.now(),
                    send=auto_comm.dispatch_auto, type='auto',
                )
                auto_comm.sent_to_users.add(user)
                c.save()
