from aklub.views import stat_payments, stat_members
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.i18n import javascript_catalog

admin.autodiscover()

urlpatterns = [
    url(r'^admin/passreset/$', auth_views.password_reset, name='password_reset'),
    url(r'^admin/passresetdone/$', auth_views.password_reset_done, name='password_reset_done'),
    url(r'^admin/passresetconfirm/(?P<uidb64>[-\w]+)/(?P<token>[-\w]+)/$', auth_views.password_reset_confirm, name='password_reset_confirm'),
    url(r'^admin/passresetcomplete/$', auth_views.password_reset_complete, name='password_reset_complete'),
    url(r'^admin/aklub/stat-members/', stat_members, name="stat-members"),
    url(r'^admin/aklub/stat-payments/', stat_payments, name="stat-payments"),
    url(r'^admin/', admin.site.urls),
    url(r'^', admin.site.urls),
    url(r'^admin/', include("massadmin.urls")),
    url(r'^jsi18n', javascript_catalog),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'', include("aklub.urls")),
]
