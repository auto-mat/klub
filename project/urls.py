from django.conf.urls import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^klub/', include('klub.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
                           (r'^admin/aklub/stat-members/$', 'aklub.views.stat_members'),
                           (r'^admin/aklub/stat-payments/$', 'aklub.views.stat_payments'),
                           (r'^regular/', 'aklub.views.regular'),
                           (r'^regular-wp/', 'aklub.views.regular_wp'),
                           (r'^onetime/', 'aklub.views.onetime'),
                           (r'^thanks/', 'aklub.views.thanks'),
                           (r'^thanks-wp/', 'aklub.views.thanks_wp'),
                           (r'^donators/', 'aklub.views.donators'),
                           (r'^profiles/', 'aklub.views.profiles'),
                           (r'^admin/', include(admin.site.urls)),
                           (r'^jsi18n', 'django.views.i18n.javascript_catalog'),
                           (r'^tinymce/', include('tinymce.urls')),
                           (r'^admin_tools/', include('admin_tools.urls')),
                           #(r'', include(admin.site.urls)),
)
