from django.conf.urls import *
from aklub.views import RegularUserFormWithProfile, RegularView

urlpatterns = patterns('',
       url(r'^regular/', RegularView.as_view()),
       url(r'^regular-wp/', RegularView.as_view(
           template_name='regular-wp.html',
           form_class=RegularUserFormWithProfile,
           success_template='thanks-wp.html')
           ),
       (r'^onetime/', 'aklub.views.onetime'),
       (r'^donators/', 'aklub.views.donators'),
       (r'^profiles/', 'aklub.views.profiles'),
)
