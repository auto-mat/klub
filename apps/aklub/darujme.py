# -*- coding: utf-8 -*-
""" Parse reports from Darujme.cz """

import xlrd
import logging
import datetime

from aklub.models import AccountStatements, Payment, User, str_to_datetime

# Text constants in Darujme.cz report
KLUB = u'Klub přátel Auto*Matu'
OK_STATE = u'OK, převedeno'

log = logging.getLogger(__name__)

def parse_darujme(statement, xlsfile):
    log.info('Darujme.cz import started at %s' % datetime.datetime.now())
    book = xlrd.open_workbook(xlsfile)
    sheet = book.sheet_by_index(0)
    for ir in range(1,sheet.nrows):
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
        
        received = row[12].value
        name = row[17].value
        surname = row[18].value
        email = row[19].value

        if Payment.objects.filter(type='darujme', SS=id).exists():
            log.info('Payment with type Darujme.cz and SS=%d already exists, skipping' % id)
            continue

        p = Payment()
        p.account_statement = statement
        p.type = 'darujme'
        p.SS = id
        p.date = str_to_datetime(received)
        p.amount = ammount
        p.account_name = u'%s, %s' % (surname, name)
        p.user_identification = email

        try:
            user = User.objects.get(email=email)
            p.user = user
        except User.DoesNotExist:
            log.info('User with email %s not found' % email)

        p.save()

if __name__ == '__main__':
    import os, sys
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
    import django
    django.setup()

    p = AccountStatements()
    parse_darujme(p, sys.argv[1])
