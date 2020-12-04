# -*- coding: utf-8 -*-

from rest_framework import filters, generics
from rest_framework.parsers import FormParser, MultiPartParser

from .models import TemplateContent
from .serializers import TemplateContentSerializer

#
# Mixin for all company views.
# Defines serializers, queryset and permissions
#


class TemplateContentMixin(object):
    def get_queryset(self):
        return TemplateContent.objects.filter()

    def get_serializer_class(self):
        return TemplateContentSerializer


class TemplateContentAdd(TemplateContentMixin, generics.CreateAPIView):
    parser_classes = (MultiPartParser, FormParser,)

    def perform_create(self, serializer):
        regions = self.request.data.get('regions')
        images = self.request.data.get('images')
        page = self.request.data.get('page')
        styles = self.request.data.get('styles')

        serializer.save(
            regions=regions,
            images=images,
            page=page,
            styles=styles,
        )


class TemplateContentRetrieve(TemplateContentMixin, generics.RetrieveAPIView):
    lookup_field = 'uuid'


class TemplateContentUpdate(TemplateContentMixin, generics.UpdateAPIView):
    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save()


class TemplateContentList(TemplateContentMixin, generics.ListAPIView):
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('created')
    ordering = ('-created',)


class TemplateContentDelete(TemplateContentMixin, generics.DestroyAPIView):
    lookup_field = 'uuid'
