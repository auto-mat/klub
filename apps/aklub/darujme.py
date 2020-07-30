# -*- coding: utf-8 -*-
""" Parse reports from Darujme.cz """
import datetime
import logging
import urllib
import xml
from collections import OrderedDict
from xml.dom import minidom

from aklub.models import (
    AccountStatements, ApiAccount, DonorPaymentChannel, Payment, ProfileEmail, Telephone, UserProfile, str_to_datetime,
    str_to_datetime_xml,
)
from aklub.views import get_unique_username

from django.core.exceptions import ValidationError

import xlrd


# Text constants in Darujme.cz report
STATE_OK_MAP = {
    'OK, převedeno': True,
    'OK': True,
    'neproběhlo': False,
    'neuzavřeno': False,
    'příslib': False,
}

FREQUENCY_MAP = {
    'měsíční': "monthly",
    "roční": "annually",
    "jednorázový": None,
}
UNLIMITED = "na dobu neurčitou"

log = logging.getLogger(__name__)


def parse_string(value):
    if type(value) == float:
        return int(value)
    return value


def parse_float_to_int(value):
    return int(float(value))


def map_ano_ne(value):
    if value == "Ano":
        return True
    if value == "Ne":
        return False
    return value


def parse_darujme_xml(xmlfile):
    xmldoc = minidom.parse(xmlfile)
    darujme_api = xmldoc.getElementsByTagName('darujme_api')[0]
    payments = []
    skipped_payments = []
    for record in darujme_api.getElementsByTagName('record'):
        data = {}
        trans_id = record.getElementsByTagName('transaction_id')[0].firstChild
        if trans_id:
            data['id'] = trans_id.nodeValue
        else:
            data['id'] = ""
        data['projekt'] = record.getElementsByTagName('projekt')[0].firstChild.nodeValue
        data['cislo_projektu'] = record.getElementsByTagName('cislo_projektu')[0].firstChild.nodeValue
        data['cetnost'] = record.getElementsByTagName('cetnost')[0].firstChild.nodeValue
        data['stav'] = record.getElementsByTagName('stav')[0].firstChild.nodeValue
        data['datum_daru'] = record.getElementsByTagName('datum_daru')[0].firstChild.nodeValue
        data['uvedena_castka'] = parse_float_to_int(record.getElementsByTagName('uvedena_castka')[0].firstChild.nodeValue)
        data['telefon'] = ""
        cetnost_konec = record.getElementsByTagName('cetnost_konec')[0].firstChild
        if cetnost_konec and cetnost_konec.nodeValue != UNLIMITED:
            data['cetnost_konec'] = str_to_datetime_xml(cetnost_konec.nodeValue)
        else:
            data['cetnost_konec'] = UNLIMITED
        for hodnota in record.getElementsByTagName('uzivatelska_pole')[0].getElementsByTagName('hodnota'):
            if hodnota.hasChildNodes():
                value = map_ano_ne(hodnota.firstChild.nodeValue)
            else:
                value = ""
            data[hodnota.attributes['nazev'].value] = value

        platby = record.getElementsByTagName('platby')
        if len(platby) > 0:
            for platba in platby[0].getElementsByTagName('platba'):
                data['id_platby'] = platba.getElementsByTagName('id_platby')[0].firstChild.nodeValue
                data['datum_prichozi_platby'] = platba.getElementsByTagName('datum_prichozi_platby')[0].firstChild.nodeValue
                data['obdrzena_castka'] = parse_float_to_int(platba.getElementsByTagName('obdrzena_castka')[0].firstChild.nodeValue)
                create_payment(data, payments, skipped_payments)
        else:
            data['id_platby'] = None
            data['datum_prichozi_platby'] = None
            data['obdrzena_castka'] = None
            create_payment(data, payments, skipped_payments)
    return payments, skipped_payments


def create_statement_from_file(xmlfile):
    payments, skipped_payments = parse_darujme_xml(xmlfile)
    if len(payments) > 0:
        a = AccountStatements(type="darujme")
        a.payments = payments
        a.save()
    else:
        a = None
    return a, skipped_payments


def create_statement_from_API(campaign):
    url = 'https://www.darujme.cz/dar/api/darujme_api.php?api_id=%s&api_secret=%s&typ_dotazu=1' % (
        campaign.api_id,
        campaign.api_secret,
    )
    response = urllib.request.urlopen(url)
    try:
        return create_statement_from_file(response)
    except xml.parsers.expat.ExpatError as e:
        print("Error while parsing url: %s" % url)
        raise e


def get_campaign(data):
    if 'cislo_projektu' in data:
        return ApiAccount.objects.get(project_id=data['cislo_projektu'])
    else:
        return ApiAccount.objects.get(project_name=data['projekt'])


def get_cetnost_konec(data):
    if data['cetnost_konec'] in (UNLIMITED, ""):
        return None
    else:
        return data['cetnost_konec']


def get_cetnost_regular_payments(data):
    cetnost = FREQUENCY_MAP[data['cetnost']]
    state_ok = STATE_OK_MAP[data['stav'].strip()]
    if not cetnost:
        return cetnost, "onetime"
    else:
        if state_ok:
            return cetnost, "regular"
        else:
            return cetnost, "promise"


# class PaymentForm(forms.ModelForm):
#     class Meta:
#         model = Payment


def create_payment(data, payments, skipped_payments):  # noqa
    if data['email'] == '':
        return
    id_platby = data.get('id_platby')
    campaign = get_campaign(data)

    if id_platby and Payment.objects.filter(type='darujme', SS=data['id'], operation_id=None).exists():
        payment = Payment.objects.filter(type='darujme', SS=data['id'], operation_id=None).first()
        payment.operation_id = id_platby
        payment.date = data['datum_prichozi_platby'] or data['datum_daru']
        payment.recipient_account = campaign
        payment.save()
        return None

    filter_kwarg = {
        "type": 'darujme',
        "SS": data['id'],
        "date": data['datum_prichozi_platby'] or data['datum_daru'],
        # TODO:
        # "recipient_account": campaign, # this cant be done because  this wont find old payments without recipient account
        # we need to set recipient_account to all payments first!
    }
    if id_platby:
        filter_kwarg["operation_id"] = id_platby
    existed_payments = Payment.objects.filter(**filter_kwarg)
    if existed_payments.exists():
        # TODO: this can be removed after all payments in db has updated recipient_account
        for pay in existed_payments:
            if not pay.recipient_account:
                pay.recipient_account = campaign
                pay.save()

        skipped_payments.append(
            OrderedDict(
                [
                    ('ss', data['id']),
                    ('date', data['datum_daru']),
                    ('name', data['jmeno']),
                    ('surname', data['prijmeni']),
                    ('email', data['email']),
                ],
            ),
        )
        log.info('Payment with type Darujme.cz and SS=%s already exists, skipping' % str(data['id']))
        return None

    cetnost_konec = get_cetnost_konec(data)

    cetnost, regular_payments = get_cetnost_regular_payments(data)

    amount = max(data['obdrzena_castka'] or data['uvedena_castka'], 0)
    p = None

    if STATE_OK_MAP[data['stav'].strip()]:
        p = Payment()
        p.type = 'darujme'
        p.SS = data['id']
        p.date = data['datum_prichozi_platby'] or data['datum_daru']
        p.operation_id = id_platby
        p.amount = amount
        p.account_name = u'%s, %s' % (data['prijmeni'], data['jmeno'])
        p.user_identification = data['email']
        p.recipient_account = campaign

    username = get_unique_username(data['email'])
    email, email_created = ProfileEmail.objects.get_or_create(
                email=data['email'],
            )
    if email_created:
        userprofile = UserProfile.objects.create(
                first_name=data['jmeno'],
                last_name=data['prijmeni'],
                username=username,
                street=data.get('ulice', ""),
                city=data.get('mesto', ""),
                zip_code=data.get('psc', ""),
        )
        email.user = userprofile
        email.save()
    else:
        log.info("Duplicate email %s" % email.email)
        userprofile = email.user
    userprofile.administrative_units.add(campaign.administrative_unit)
    if data.get('telefon'):

        try:
            Telephone(telephone=str(data['telefon']).replace(" ", "")).full_clean()

        except ValidationError:
            log.info(f"Duplicate telephone for email: {email.email}")
        else:
            telephone, tel_created = Telephone.objects.get_or_create(
                telephone=str(data['telefon']).replace(" ", ""),
                user=userprofile,
            )
            if tel_created:
                log.info(f"Duplicate telephone for email: {email.email}")

    donorpaymentchannel, donorpaymentchannel_created = DonorPaymentChannel.objects.get_or_create(
        user=userprofile,
        event=campaign.event,
        money_account=campaign,
        defaults={
            'regular_frequency': cetnost,
            'regular_payments': regular_payments,
            'regular_amount': amount if cetnost else None,
            'end_of_regular_payments': cetnost_konec,
        },
    )
    if donorpaymentchannel_created:
        log.info('DonorPaymentChannel with email %s created' % data['email'])
    else:
        if cetnost and donorpaymentchannel.regular_payments != "regular":
            donorpaymentchannel.regular_frequency = cetnost
            donorpaymentchannel.regular_payments = regular_payments
            donorpaymentchannel.regular_amount = amount if cetnost else None
            donorpaymentchannel.save()
    if p:
        p.user_donor_payment_channel = donorpaymentchannel
        p.save()
        payments.append(p)


def parse_darujme(xlsfile):
    log.info('Darujme.cz import started at %s' % datetime.datetime.now())
    book = xlrd.open_workbook(file_contents=xlsfile.read())
    sheet = book.sheet_by_index(0)
    payments = []
    skipped_payments = []
    for ir in range(1, sheet.nrows):
        data = {}

        row = sheet.row(ir)
        log.debug('Parsing transaction: %s' % row)

        # Darujme.cz ID of the transaction
        if row[0].value:
            data['id'] = int(row[0].value)
        else:
            data['id'] = ""

        # Skip all non klub transactions (e.g. PNK)
        data['projekt'] = row[2].value

        # Amount sent by the donor in CZK
        # The money we receive is smaller by Darujme.cz
        # margin, but we must count the whole ammount
        # to issue correct tax confirmation to the donor
        data['stav'] = row[9].value
        if row[5].value:
            data['obdrzena_castka'] = int(row[5].value)
        else:
            data['obdrzena_castka'] = None
        data['uvedena_castka'] = int(row[4].value)

        data['datum_daru'] = str_to_datetime(row[11].value)
        data['datum_prichozi_platby'] = str_to_datetime(row[12].value)
        data['jmeno'] = row[17].value
        data['prijmeni'] = row[18].value
        data['email'] = row[19].value
        data['telefon'] = parse_string(row[20].value)
        data['ulice'] = row[21].value
        data['mesto'] = row[22].value
        data['psc'] = parse_string(row[23].value)
        data['potvrzeni_daru'] = row[24].value
        data['cetnost'] = row[13].value
        cetnost_konec = row[14].value
        if cetnost_konec and cetnost_konec != UNLIMITED:
            data['cetnost_konec'] = str_to_datetime(cetnost_konec)
        else:
            data['cetnost_konec'] = cetnost_konec
        create_payment(data, payments, skipped_payments)
    return payments, skipped_payments


def check_for_new_payments(log_function=None):
    if log_function is None:
        log_function = lambda _: None # noqa
    for campaign in ApiAccount.objects.filter(api_secret__isnull=False).exclude(api_secret=""):
        log_function(campaign)
        payment, skipped = create_statement_from_API(campaign)
        log_function(payment)
        log_function("Skipped: %s" % skipped)
