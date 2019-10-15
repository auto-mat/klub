
import decimal

from PIL import Image

from rest_framework import generics, permissions

from .models import Images
from .serializers import ImagesSerializer

#
# Mixin for all company views.
# Defines serializers, queryset and permissions
#


class ImagesMixin(object):

    def get_queryset(self):
        return Images.objects.filter()

    def get_serializer_class(self):
        return ImagesSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated()]


class ImagesAdd(ImagesMixin, generics.CreateAPIView):

    def perform_create(self, serializer):
        serializer.save(
            image=self.request.data['image'],
            name=self.request.data['image'].name,
            edited_width=self.request.data['width'],
        )


class ImagesList(ImagesMixin, generics.ListAPIView):
    ordering_fields = ('created')
    ordering = ('-created',)


class ImagesUpdate(ImagesMixin, generics.UpdateAPIView):

    lookup_field = 'id'

    def post(self, request, *args, **kwargs):
        response = self.update(request, *args, **kwargs)
        return response

    def perform_update(self, serializer):
        # Get image from image model instance
        image = self.get_object().image

        if self.request.data.get('crop'):

            crop_values = self.request.data['crop'].split(',')

            # Crop values are percentages, so we need to convert them into
            # pixel values

            top = round(decimal.Decimal(crop_values[0]) * image.height)
            left = round(decimal.Decimal(crop_values[1]) * image.width)
            bottom = round(decimal.Decimal(crop_values[2]) * image.height)
            right = round(decimal.Decimal(crop_values[3]) * image.width)

            crop_box = (left, top, right, bottom)

            # Open the image with PIL
            im = Image.open(image.path)

            # Action the image rotation
            im = im.crop(crop_box)

            # Save the image
            im.save(image.path)

            serializer.save(
                edited_crop=self.request.data['crop'],
            )

        if self.request.data.get('direction'):
            angle = 270 if self.request.data['direction'] == "CW" else 90

            # Open the image with PIL
            im = Image.open(image.path)

            # Action the image rotation
            im = im.rotate(angle)

            # Save the image
            im.save(image.path)

            serializer.save(edited_direction=self.request.data['direction'])
