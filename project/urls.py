from aklub.views import stat_members, stat_payments

from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.i18n import JavaScriptCatalog

admin.autodiscover()

urlpatterns = [
    url(r'^desk/', include("helpdesk.urls")),
    url(r'^admin/passreset/$', auth_views.PasswordResetView.as_view(), name='password_reset'),
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
    url(r'^admin/', include("massadmin.urls")),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^jsi18n', JavaScriptCatalog.as_view()),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'^adminactions/', include('adminactions.urls')),
    url(r'^advanced_filters/', include('advanced_filters.urls')),
    url(r'', include("aklub.urls")),
]

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
