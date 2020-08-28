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


class PaidPdfDownloadLinkSerialiser(serializers.ModelSerializer):
    class Meta:
        model = PdfStorage
        fields = ['pdf_file']
