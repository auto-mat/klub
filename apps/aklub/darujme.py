# -*- coding: utf-8 -*-
""" Parse reports from Darujme.cz """

import xlrd
import logging
import datetime

from aklub.models import AccountStatements, Payment, UserInCampaign, str_to_datetime, UserProfile
from django.contrib.auth.models import User as DjangoUser
from django.core.exceptions import MultipleObjectsReturned
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

# Text constants in Darujme.cz report
KLUB = u'Klub přátel Auto*Matu'
OK_STATE = u'OK, převedeno'

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
        if prj != KLUB:
            continue

        # Amount sent by the donor in CZK
        # The money we receive is smaller by Darujme.cz
        # margin, but we must count the whole ammount
        # to issue correct tax confirmation to the donor
        ammount = int(row[5].value)

        state = row[9].value
        if state != OK_STATE:
            continue

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
            user = DjangoUser.objects.get(email=email)
            userprofile = UserProfile.objects.get(user=user)
            userincampaign = UserInCampaign.objects.get(userprofile=userprofile)
            p.user = userincampaign
        except (UserInCampaign.DoesNotExist, UserProfile.DoesNotExist, DjangoUser.DoesNotExist):
            log.info('User with email %s not found' % email)
        except MultipleObjectsReturned:
            log.info('Duplicate email %s' % email)
            raise ValidationError(_('Duplicate email %(email)s'), params={'email': email})

        payments.append(p)
    return payments, skipped_payments

if __name__ == '__main__':
    import os
    import sys
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
    import django
    django.setup()

    p = AccountStatements()
    parse_darujme(p, sys.argv[1])
