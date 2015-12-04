from django.conf.urls import include, patterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
   '',
   (r'^admin/aklub/stat-members/$', 'aklub.views.stat_members'),
   (r'^admin/aklub/stat-payments/$', 'aklub.views.stat_payments'),
   (r'^admin/', include(admin.site.urls)),
   (r'^$', include(admin.site.urls)),
   (r'^admin/', include("massadmin.urls")),
   (r'^jsi18n', 'django.views.i18n.javascript_catalog'),
   (r'^tinymce/', include('tinymce.urls')),
   (r'^admin_tools/', include('admin_tools.urls')),
   (r'', include("aklub.urls")),
)
