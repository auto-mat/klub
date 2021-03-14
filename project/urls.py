import logging

from aklub.views import stat_members, stat_payments

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.i18n import JavaScriptCatalog


logger = logging.getLogger(__name__)


def test_errors(request):
    """
    This is for testing error logging. Go to the /test_errors/ url and then check sentry to make sure the error reporting is working.
    """
    logger.info("Testing info message", extra={"test": "foobar"})
    logger.debug("Testing debug message", extra={"test": "foobar"})
    logger.warning("Testing warning message", extra={"test": "foobar"})
    logger.exception("Testing exception message", extra={"test": "foobar"})
    logger.error("Testing error message", extra={"test": "foobar"})
    return HttpResponse("Errors send")

admin.autodiscover()

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
    url(r'', include("aklub.urls")),
    path('notifications/', include('django_nyt.urls')),
    path('help/', include('wiki.urls')),
    path('api/', include('api.urls')),
    url('^{errors_url}/$'.format(errors_url=settings.TEST_ERRORS_URL), test_errors),
    path('model_schema/', include('django_spaghetti.urls')),
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
