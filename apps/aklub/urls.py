from django.conf.urls import patterns, url
from aklub.views import RegularUserFormWithProfile, RegularView, RegularUserFormDPNK

urlpatterns = patterns(
    '',
    url(r'^regular/', RegularView.as_view()),
    url(r'^regular-wp/', RegularView.as_view(
        template_name='regular-wp.html',
        form_class=RegularUserFormWithProfile,
        success_template='thanks-wp.html')
        ),
    url(r'^regular-dpnk/', RegularView.as_view(
        template_name='regular-dpnk.html',
        form_class=RegularUserFormDPNK,
        success_template='thanks-dpnk.html',
        source_slug='dpnk'),
        name="regular-dpnk",
        ),
    (r'^onetime/', 'aklub.views.onetime'),
    (r'^donators/', 'aklub.views.donators'),
    (r'^profiles/', 'aklub.views.profiles'),
)
