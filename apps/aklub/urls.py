from aklub import views

from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.urls import path

from . import tasks # noqa

urlpatterns = [
    url(r'^regular/', views.RegularView.as_view(), name="regular"),
    url(r'^regular-wp/', views.RegularWPView.as_view(), name="regular-wp"),
    url(r'^regular-dpnk/', views.RegularDPNKView.as_view(), name="regular-dpnk"),
    url(r'^regular-darujme/', views.RegularDarujmeView.as_view(), name="regular-darujme"),

    path('register-without-payment/<slug:unit>/', views.RegisterWithoutPaymentView.as_view(), name='register-withou-payment'),

    url(r'^sign-petition/', views.PetitionView.as_view(), name="petition"),
    url(r'^sing-petition-confirm/(?P<campaign_slug>[^&]+)/$', views.PetitionConfirmEmailView.as_view(), name="sing-petition-confirm"),
    url(r'^petition-signatures/(?P<campaign_slug>[^&]+)/', views.PetitionSignatures.as_view(), name="petition-signatures"),

    path('send-mailing-lists/<slug:unit>/<slug:unsubscribe>/', views.SendMailingListView.as_view(), name="send-mailing-list"),

    url(r'^campaign-statistics/(?P<campaign_slug>[^&]+)/$', views.CampaignStatistics.as_view(), name="campaign-statistics"),
    path('donators/<slug:unit>/', views.DonatorsView.as_view(), name="donators"),
    path('views_docs/', views.ViewDocView.as_view(), name="views_docs"),


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
]
