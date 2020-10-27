import datetime
import urllib
from xml.dom import minidom

from aklub.models import ApiAccount, DonorPaymentChannel

from django.utils import timezone


def get_or_create_dpch(serializer, profile):
    dpch, created = DonorPaymentChannel.objects.get_or_create(
                    event=serializer.validated_data['event'],
                    money_account=serializer.validated_data['money_account'],
                    user=profile,
                    )
    if created:
        dpch.expected_date_of_first_payment = datetime.date.today() + datetime.timedelta(days=3)
        if serializer.validated_data.get('regular'):
            dpch.regular_payments = 'regular'
        else:
            dpch.regular_payments = 'onetime'
        dpch.regular_amount = serializer.validated_data['amount']
        dpch.save()
    return dpch


def check_last_month_payment(user):
    found_payment = False
    for dpch in user.userchannels.all():
        if found_payment:
            break
        # check if some donor payment channel has some payment for last mouth
        if dpch.last_payment and dpch.last_payment.date >= timezone.now().date() - timezone.timedelta(days=40):
            found_payment = True
        else:
            api = dpch.money_account
            if isinstance(api, ApiAccount) and dpch.payment_total == 0:
                # it can be first payment so we check if user confirmed it on darujme
                url = "https://www.darujme.cz/dar/api/darujme_api.php/?api_id=%s&api_secret=%s&od_data_daru=%s&typ_dotazu=1" % (
                    api.api_id,
                    api.api_secret,
                    dpch.registered_support.date()
                )
                xmlfile = urllib.request.urlopen(url)
                xmldoc = minidom.parse(xmlfile)
                darujme_api = xmldoc.getElementsByTagName('darujme_api')[0]
                for data in darujme_api.getElementsByTagName('record'):
                    for val in data.getElementsByTagName('uzivatelska_pole')[0].getElementsByTagName('hodnota'):
                        if val.attributes['nazev'].value == 'email' and val.firstChild.nodeValue == user.get_email_str():
                            status = data.getElementsByTagName('stav')[0].firstChild.nodeValue
                            if status == 'OK':
                                found_payment = True
                                break
    return found_payment
