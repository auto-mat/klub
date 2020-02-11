import pathlib

from django import template
from django.contrib.staticfiles import finders

register = template.Library()


@register.inclusion_tag('email_templates/automat_fonts.html')
def get_automat_fonts():
    fonts = []
    _finders = finders.AppDirectoriesFinder()
    automat_font_dir = _finders.find_in_app(
        app='aklub',
        path='aklub/fonts/automat',
    )
    automat_font_dir_content = pathlib.Path(automat_font_dir).glob('**/*')

    font_files = [(f.stem, f.name) for f in automat_font_dir_content if f.is_file()]
    for font_name, font_file_name in font_files:
        fonts.append((f'AutoMat-{font_name}', font_file_name))

    return {'automat_fonts': fonts}
