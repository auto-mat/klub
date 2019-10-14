
import os
import pathlib
import re

from PIL import Image

import cairosvg

import cssutils


from django.contrib.staticfiles import finders
from django.core.management import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Convert automat newsletter background vector (svg) image -> raster (jpg|png)' # noqa

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--width',
            dest='width',
            type=int,
            help='Image width (px)',
        )
        parser.add_argument(
            '--height',
            dest='height',
            type=int,
            help='Image height (px)',
        )
        parser.add_argument(
            '--dpi',
            dest='dpi',
            type=int,
            default=96,
            help='Image dpi',
        )

        parser.add_argument(
            '--format',
            dest='format',
            choices=['jpeg', 'png'],
            default='png',
            help='Image format (png|jpeg)',
        )

    def __parse_css_file(self, css):
        result = {}
        sheet = cssutils.parseString(css)

        for rule in sheet:
            selector = rule.selectorText
            styles = rule.style.cssText
            result[selector] = styles

        return result

    def handle(self, *args, **options):
        width = options.get('width')
        height = options.get('height')
        image_format = options.get('format')
        dpi = options.get('dpi')

        _finders = finders.AppDirectoriesFinder()
        images_dir = _finders.find_in_app(app='aklub', path='aklub/images')
        css_dir = _finders.find_in_app(app='aklub', path='aklub/css')
        css_file = pathlib.PurePath(css_dir) / 'automat_newsletter.css'

        if not width and height:
            raise CommandError('set image --width please')
        if not height and width:
            raise CommandError('set image --height please')
        if not width and not height:
            with open(css_file, 'r') as f:
                css = f.read()
                css_rules = self.__parse_css_file(css=css)
                css_image_size = css_rules['.newsletter-section']

                width_match = re.search('width: [0-9]*', css_image_size)
                if width_match:
                    width = int(width_match.group(0).split(':')[1])

                height_match = re.search('height: [0-9]*', css_image_size)
                if height_match:
                    height = int(height_match.group(0).split(':')[1])

        image_name = '^automat_.*._newsletter.svg$'
        for image in [i for i in os.listdir(images_dir) if re.match(image_name, i)]:
            png_image = image.replace('svg', 'png')
            svg_image_path = pathlib.PurePath(images_dir) / image
            png_image_path = pathlib.PurePath(images_dir) / png_image
            svg_image_path = svg_image_path.as_posix()
            png_image_path = png_image_path.as_posix()
            cairosvg.svg2png(
                url=svg_image_path,
                write_to=png_image_path,
                # output_width=width,
                # output_height=height,
                dpi=dpi,
            )
            if image_format == 'jpeg':
                jpeg_image = image.replace('svg', 'jpeg')
                jpeg_image_path = pathlib.PurePath(images_dir) / jpeg_image
                jpeg_image_path = jpeg_image_path.as_posix()
                im = Image.open(png_image_path)
                rgb_im = im.convert('RGB')
                rgb_im.save(jpeg_image_path, quality=95)
                os.remove(png_image_path)
