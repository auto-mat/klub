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

from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


def _localize_enum(descr, val, lang):
    for t in descr:
        if t[0] == val:
            # Hack! Here we should use the Gettext localization
            # based on the value of 'lang' -- this is however
            # not easy due to lazy translations and t[1] already
            # being wrapped by a foreign translator
            if lang == "cs":
                return t[1].lower()
            else:
                # less wrong would be to retrieve the original untranslated version of t[1]...
                return t[0]
    # Translation not found
    return val


KNOWN_VARIABLES = [
    "addressment",
    "name",
    "firstname",
    "surname",
    "street",
    "city",
    "zipcode",
    "email",
    "telephone",
    "regular_amount",
    "regular_frequency",
    "var_symbol",
    "last_payment_amount",
    "auth_token",
]


def min_non_negative(i, j):
    if i < 0:
        return j
    if j < 0:
        return i
    return min(i, j)


def gendrify_text(text, sex=""):
    # Modify text according to gender
    # Example: Vazen{y|a} {pane|pani} -> [male] -> Vazeny pane
    gender_text = ""
    o = 0
    i = 0
    while i < len(text):
        if text[i] == "{":
            gender_text += text[o:i]
            sep_pos = min_non_negative(text.find("|", i), text.find("/", i))
            end_pos = text.find("}", i)
            if sep_pos <= i or end_pos <= sep_pos:
                raise ValidationError(
                    "Gender strings must look like {male_variant|female_variant} or {male_variant/female_variant}"
                )
            male_variant = text[i + 1 : sep_pos]
            female_variant = text[sep_pos + 1 : end_pos]
            if sex == "male":
                gender_text += male_variant
            elif sex == "female":
                gender_text += female_variant
            else:
                gender_text += male_variant + "/" + female_variant
            o = end_pos + 1
            i = end_pos
        i += 1
    gender_text += text[o:]
    return gender_text


def process_template(template_string, user, payment_channel):
    from aklub.models import DonorPaymentChannel
    from sesame import utils as sesame_utils

    template = string.Template(template_string)
    if payment_channel:

        payment_substitutes = {
            "regular_amount": payment_channel.regular_amount,
            "regular_frequency": _localize_enum(
                DonorPaymentChannel.REGULAR_PAYMENT_FREQUENCIES,
                payment_channel.regular_frequency,
                user.language,
            ),
            "var_symbol": payment_channel.VS,
            "last_payment_amount": payment_channel.last_payment.amount
            if payment_channel.last_payment
            else None,
        }

    else:
        payment_substitutes = {}

    # Make variable substitutions
    text = template.substitute(
        addressment=user.get_addressment(),
        last_name_vokativ=user.get_last_name_vokativ(),
        name=user.first_name if hasattr(user, "first_name") else user.name,
        firstname=user.first_name if hasattr(user, "first_name") else user.name,
        surname=user.last_name if hasattr(user, "first_name") else user.name,
        street=user.street,
        city=user.city,
        zipcode=user.zip_code,
        email=user.email,
        telephone=user.get_telephone(),
        auth_token=sesame_utils.get_query_string(user),
        **payment_substitutes,
    )
    return gendrify_text(text, user.sex if hasattr(user, "sex") else "")


def check(user_profiles=None, action=None):  # noqa
    from aklub.models import AutomaticCommunication, DonorPaymentChannel, UserProfile
    from interactions.models import Interaction

    if not user_profiles:
        user_profiles = UserProfile.objects.all()

    # limit autocoms only for autocoms where action is used
    if action:
        # TODO: handle nested conditions?
        from flexible_filter_conditions.models import TerminalCondition

        conditions = TerminalCondition.objects.filter(
            variable="action", value=action
        ).values_list("condition")
        auto_coms = AutomaticCommunication.objects.filter(
            condition__conditions__in=conditions
        )
    else:
        auto_coms = AutomaticCommunication.objects.all()
    for auto_comm in auto_coms:
        logger.info(
            'Processin condition "%s" for autocom "%s", method: "%s", action: "%s"'
            % (
                auto_comm.condition,
                auto_comm,
                auto_comm.method_type,
                action,
            ),
        )
        filtered_user_profiles = auto_comm.condition.filter_queryset(
            user_profiles, action
        )
        for user in filtered_user_profiles:
            try:
                if auto_comm.event:
                    payment_channel = user.userchannels.get(event=auto_comm.event)
                else:
                    payment_channel = None
            except DonorPaymentChannel.DoesNotExist:
                payment_channel = None
            if (
                auto_comm.only_once
                and auto_comm.sent_to_users.filter(pk=user.pk).exists()
            ):
                continue

            if user.language == "cs":
                template = auto_comm.template
                subject = auto_comm.subject
            else:
                template = auto_comm.template_en
                subject = auto_comm.subject_en
            if template and template != "":
                logger.info(
                    'Added new automatic communication "%s" for user "%s", action "%s"'
                    % (auto_comm, user, action)
                )
                c = Interaction(
                    user=user,
                    type=auto_comm.method_type,
                    date_from=datetime.datetime.now(),
                    subject=subject,
                    summary=process_template(template, user, payment_channel),
                    note="Prepared by automated mailer at %s" % datetime.datetime.now(),
                    settlement="a",
                    administrative_unit=auto_comm.administrative_unit,
                )
                auto_comm.sent_to_users.add(user)
                c.save()
