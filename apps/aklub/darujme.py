# -*- coding: utf-8 -*-
""" Parse reports from Darujme.cz """

import xlrd
import logging
import datetime

from aklub.models import Payment, UserInCampaign, str_to_datetime, UserProfile, Campaign
from aklub.views import generate_variable_symbol
from django.contrib.auth.models import User as DjangoUser
from django.core.exceptions import MultipleObjectsReturned
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

# Text constants in Darujme.cz report
OK_STATES = ('OK, převedeno', 'OK')

log = logging.getLogger(__name__)


def parse_darujme(xlsfile):
    log.info('Darujme.cz import started at %s' % datetime.datetime.now())
    book = xlrd.open_workbook(file_contents=xlsfile.read())
    sheet = book.sheet_by_index(0)
    payments = []
    skipped_payments = []
    for ir in range(1, sheet.nrows):
        row = sheet.row(ir)
        log.debug('Parsing transaction: %s' % row)

        # Darujme.cz ID of the transaction
        id = int(row[0].value)

        # Skip all non klub transactions (e.g. PNK)
        prj = row[2].value

        # Amount sent by the donor in CZK
        # The money we receive is smaller by Darujme.cz
        # margin, but we must count the whole ammount
        # to issue correct tax confirmation to the donor
        state = row[9].value
        if state not in OK_STATES:
            continue

        ammount = int(row[5].value)

        received = str_to_datetime(row[12].value)
        name = row[17].value
        surname = row[18].value
        email = row[19].value

        if Payment.objects.filter(type='darujme', SS=id, date=received).exists():
            skipped_payments.append({'ss': id, 'date': received, 'name': name, 'surname': surname, 'email': email})
            log.info('Payment with type Darujme.cz and SS=%d already exists, skipping' % id)
            continue

        p = Payment()
        p.type = 'darujme'
        p.SS = id
        p.date = received
        p.amount = ammount
        p.account_name = u'%s, %s' % (surname, name)
        p.user_identification = email

        try:
            campaign = Campaign.objects.get(darujme_name=prj)
            user, user_created = DjangoUser.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': name,
                    'last_name': surname,
                })
            userprofile, userprofile_created = UserProfile.objects.get_or_create(
                user=user,
            )
            userincampaign, userincampaign_created = UserInCampaign.objects.get_or_create(
                userprofile=userprofile,
                campaign=campaign,
                defaults={
                    'variable_symbol': generate_variable_symbol(),
                })
            p.user = userincampaign

            if userincampaign_created:
                log.info('UserInCampaign with email %s created' % email)
        except MultipleObjectsReturned:
            log.info('Duplicate email %s' % email)
            raise ValidationError(_('Duplicate email %(email)s'), params={'email': email})

        payments.append(p)
    return payments, skipped_payments
