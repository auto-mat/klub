import pathlib

from django.contrib.staticfiles import finders


def get_social_media_icons_names():
    social_media_choices = []
    _finders = finders.AppDirectoriesFinder()

    img_src_dir = _finders.find_in_app(
        app='aklub',
        path='aklub/images/social_media',
    )
    imgs = pathlib.Path(img_src_dir).glob('**/*')
    for img in imgs:
        social_media_choices.append((img.stem, (img.stem)))

    return sorted(social_media_choices, key=lambda tup: tup[0])
