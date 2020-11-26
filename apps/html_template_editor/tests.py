# -*- coding: utf-8 -*-
import io

from PIL import Image

from django.core.files.base import ContentFile
from django.urls import reverse


from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from aklub.tests.test_admin import CreateSuperUserMixin


# Create your tests here.
class TemplateContentTests(CreateSuperUserMixin, APITestCase):

    def setUp(self):
        super().setUp()
        self.token = Token.objects.create(user=self.superuser)
        self.client = APIClient()

    def test_add(self):
        """ Test if we can add, retrieve and list """
        self.client.credentials(HTTP_AUTHORIZATION='Token {}'.format(self.token.key))

        # Create the add URL
        url = reverse('api:add')

        data = {
            'images': ['{}'],
            'regions': [
                ''.join([
                    """{"article": "<h3 class='author__about'>""",
                    """About the author</h3>""",
                    """<img alt='Anthony Blackshaw' class='[ author__pic ]  [ align-right ]'""",
                    """height='80' src='/static/author-pic.jpg' width='80'>""",
                    """<p class='author__bio'>""",
                    """Anthony Blackshaw is a co-founder of Getme, an employee owned""",
                    """company with a focus on web tech. He enjoys writing and talking""",
                    """about tech, especially code and the occasional""",
                    """Montecristo No.2s./p>"}""",
                ])
                ],
            'page': ['/']
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        object_id = response.data['uuid']

        # Retrieve
        url = reverse('api:retrieve', args=[object_id])
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ImageUploadTests(CreateSuperUserMixin, APITestCase):

    def setUp(self):
        super().setUp()
        self.token = Token.objects.create(user=self.superuser)
        self.client = APIClient()

    def test_upload_image(self):
        """ Test if we can add, update image """
        self.client.credentials(HTTP_AUTHORIZATION='Token {}'.format(self.token.key))

        url = reverse('api:images_add')

        file_obj = io.BytesIO()
        image = Image.new("RGBA", size=(50, 50), color=(256, 0, 0))
        image.save(file_obj, 'png')

        file_obj.seek(0)

        django_friendly_file = ContentFile(file_obj.read(), 'test.png')

        data = {
            'width': ['600'],
            'image': django_friendly_file
            }

        # Upload a file with an authenticated user
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('created', response.data)

        image_id = response.data['id']

        #
        # Crop Image
        #

        url = reverse('api:images_update', args=[image_id])

        data = {
            'crop': ['0,0,10,10']
            }

        response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert unauthenticated user can not upload file
        self.client.logout()
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
