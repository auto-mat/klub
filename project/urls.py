from django.conf.urls import include, url
from aklub.views import stat_payments, stat_members

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'^admin/aklub/stat-members/', stat_members, name="stay-members"),
    url(r'^admin/aklub/stat-payments/', stat_payments, name="stay-payments"),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include(admin.site.urls)),
    url(r'^admin/', include("massadmin.urls")),
    url(r'^jsi18n', 'django.views.i18n.javascript_catalog'),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'', include("aklub.urls")),
]
