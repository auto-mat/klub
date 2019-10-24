from aklub import views

from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import path

from . import tasks # noqa

urlpatterns = [
    url(r'^regular/', views.RegularView.as_view(), name="regular"),
    url(r'^regular-wp/', views.RegularWPView.as_view(), name="regular-wp"),
    url(r'^regular-dpnk/', views.RegularDPNKView.as_view(), name="regular-dpnk"),
    url(r'^regular-darujme/', views.RegularDarujmeView.as_view(), name="regular-darujme"),
    url(r'^sign-petition/', views.PetitionView.as_view(), name="petition"),
    url(r'^petition-signatures/(?P<campaign_slug>[^&]+)/', views.PetitionSignatures.as_view(), name="petition-signatures"),
    url(r'^campaign-statistics/(?P<campaign_slug>[^&]+)/$', views.CampaignStatistics.as_view(), name="campaign-statistics"),
    url(r'^donators/', views.donators, name="donators"),
    url(r'^profiles/', views.profiles, name="profiles"),
    url(r'^mailing/', views.MailingFormSetView.as_view(), name="mailing-configuration"),
    url(r'^email_confirmation/(?P<campaign_slug>[^&]+)/$', views.ConfirmEmailView.as_view(), name="email-confirmation"),

    # userfriendly password reset
    path("password_reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path(
        'password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='password/password_reset_done.html'),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name="password/password_reset_confirm.html"),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(template_name='password/password_reset_complete.html'),
        name='password_reset_complete',
    ),
    path('get_email_template/<template_name>/', views.get_email_template, name='get_email_template'),
    path(
        'get_email_template/<template_name>/',
        login_required(views.get_email_template),
        name='get_email_template',
    ),
    path(
        'get_email_template/new_empty_template/<template_name>/',
        login_required(views.get_email_template_from_db),
        name='get_email_template_from_db',
    ),
]
