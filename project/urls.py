from aklub.views import stat_members, stat_payments

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, re_path
from django.views.i18n import JavaScriptCatalog

from js_urls.views import JsUrlsView

from rest_framework.authtoken.views import obtain_auth_token

from rest_framework_swagger.views import get_swagger_view

admin.autodiscover()
schema_view = get_swagger_view(title='API')


urlpatterns = [
    url(r'^desk/', include("helpdesk.urls")),
    url(r'^admin/passreset/$', auth_views.PasswordResetView.as_view(), name='admin_password_reset'),
    url(r'^admin/passresetdone/$', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    url(
        r'^admin/passresetconfirm/(?P<uidb64>[-\w]+)/(?P<token>[-\w]+)/$',
        auth_views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    url(r'^admin/passresetcomplete/$', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    url(r'^admin/aklub/stat-members/', stat_members, name="stat-members"),
    url(r'^admin/aklub/stat-payments/', stat_payments, name="stat-payments"),
    url(r'^', admin.site.urls),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^jsi18n', JavaScriptCatalog.as_view()),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'^adminactions/', include('adminactions.urls')),
    url(r'^advanced_filters/', include('advanced_filters.urls')),
    url(r'^nested_admin/', include('nested_admin.urls')),
    path('admin_tools_stats/', include('admin_tools_stats.urls')),
    path('notifications/', include('django_nyt.urls')),
    path('help/', include('wiki.urls')),
    path('api/', include('api.urls')),
    url(r'', include(('aklub.urls', 'aklub'), namespace='aklub')),
    re_path(
        r'^html_template_editor/',
        include(
            ('html_template_editor.urls', 'html_template_editor'),
            namespace='html_template_editor')
    ),
    re_path(r'^docs/', schema_view),
    re_path(r'^api-auth/', include('rest_framework.urls')),
    re_path(r'^token-auth/', obtain_auth_token),
    re_path(r'^js-urls/$', JsUrlsView.as_view(), name='js_urls'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    url(r'', include("aklub.urls")),
)

try:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
except ImportError:
    pass
