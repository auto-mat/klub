from aklub import views

from django.conf.urls import url

urlpatterns = [
    url(r'^regular/', views.RegularView.as_view(), name="regular"),
    url(r'^regular-wp/', views.RegularWPView.as_view(), name="regular-wp"),
    url(r'^regular-dpnk/', views.RegularDPNKView.as_view(), name="regular-dpnk"),
    url(r'^regular-darujme/', views.RegularDarujmeView.as_view(), name="regular-darujme"),
    url(r'^campaign-statistics/(?P<campaign_slug>[^&]+)/$', views.CampaignStatistics.as_view(), name="campaign-statistics"),
    url(r'^donators/', views.donators, name="donators"),
    url(r'^profiles/', views.profiles, name="profiles"),
    url(r'^mailing/', views.MailingFormSetView.as_view(), name="mailing-configuration"),
]
