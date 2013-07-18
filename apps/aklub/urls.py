from django.conf.urls import *

urlpatterns = patterns('',
       (r'^regular/', 'aklub.views.regular'),
       (r'^regular-wp/', 'aklub.views.regular_wp'),
       (r'^onetime/', 'aklub.views.onetime'),
       (r'^thanks/', 'aklub.views.thanks'),
       (r'^thanks-wp/', 'aklub.views.thanks_wp'),
       (r'^donators/', 'aklub.views.donators'),
       (r'^profiles/', 'aklub.views.profiles'),
)
