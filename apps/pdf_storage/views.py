from api.utils import check_last_month_payment

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .exceptions import HasNoPayment, PdfDoNotExist
from .models import PdfStorage
from .serializers import AllRelatedIdsSerializer, PaidPdfDownloadLinkSerializer, PdfStorageListSerializer


class RelatedPdfListView(generics.ListAPIView):
    serializer_class = PdfStorageListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PdfStorage.objects.filter(related_ids__contains=[self.kwargs['related_id']])


class PaidPdfDownloadView(generics.RetrieveAPIView):
    serializer_class = PaidPdfDownloadLinkSerializer
    model_class = PdfStorage
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs): # noqa
        user = self.request.user
        found_payment = check_last_month_payment(user)
        if found_payment:
            try:
                pdf = PdfStorage.objects.get(id=self.kwargs['id'])
            except PdfStorage.DoesNotExist:
                raise PdfDoNotExist()
            return Response(self.serializer_class(pdf).data)
        else:
            raise HasNoPayment()


class AllRelatedIdsView(generics.RetrieveAPIView):
    serializer_class = AllRelatedIdsSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(self.serializer_class({}).data, status=status.HTTP_200_OK)
