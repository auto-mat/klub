import urllib
from xml.dom import minidom

from aklub.models import ApiAccount

from django.http import HttpResponse
from django.utils import timezone

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .exceptions import HasNoPayment, PdfDoNotExist
from .models import PdfStorage
from .serializers import PaidPdfDownloadLinkSerialiser, PdfStorageListSerializer


class RelatedPdfListView(generics.ListAPIView):
    serializer_class = PdfStorageListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PdfStorage.objects.filter(related_ids__contains=[self.kwargs['related_id']])


class PaidPdfDownloadView(generics.RetrieveAPIView):
    serializer_class = PaidPdfDownloadLinkSerialiser
    model_class = PdfStorage
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs): # noqa
        user = self.request.user
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
        if found_payment:
            try:
                pdf = PdfStorage.objects.get(id=self.kwargs['id'])
            except PdfStorage.DoesNotExist:
                raise PdfDoNotExist()
            with open(pdf.pdf_file.path, "rb") as f:
                return HttpResponse(f.read(), content_type='application/pdf')
        else:
            raise HasNoPayment()
