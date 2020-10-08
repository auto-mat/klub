from django.db.models.expressions import F, Func

from rest_framework import serializers

from .models import PdfStorage


class PdfStorageListSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField('full_name')

    class Meta:
        model = PdfStorage
        fields = [
            'id', 'name', 'topic', 'author', 'created',
            ]

    def full_name(self, pdf):
        return pdf.author.person_name()


class PaidPdfDownloadLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = PdfStorage
        fields = ['pdf_file']


class AllRelatedIdsSerializer(serializers.Serializer):
    ids = serializers.SerializerMethodField()

    class Meta:
        fields = ['ids']

    def get_ids(self, obj):
        all_ids = PdfStorage.objects\
            .annotate(ids=Func(F('related_ids'), function='unnest'))\
            .values_list('ids', flat=True)\
            .distinct()
        return all_ids
