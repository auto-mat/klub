from PIL import Image

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_logo_image(image):
    max_width = 300
    megabyte_limit = 5.0 * 1024 * 1024

    width, height = Image.open(image).size
    image_file_size = image.tell()

    print(width, image_file_size)
    if width > max_width:
        raise ValidationError(
            _("Width is larger than what is allowed %(max_width)s px"),
            params={'max_width': max_width},
        )

    if image_file_size > megabyte_limit:
        raise ValidationError(
            _("Image size is larger than what is allowed "
              "%(max_file_size)s MB"),
            params={'max_file_size': megabyte_limit},
        )
