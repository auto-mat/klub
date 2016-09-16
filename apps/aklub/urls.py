from aklub.views import CampaignStatistics, RegularUserFormDPNK, RegularUserFormWithProfile, RegularView, donators, onetime, profiles

from django.conf.urls import url

urlpatterns = [
    url(r'^regular/', RegularView.as_view(), name="regular"),
    url(
        r'^regular-wp/',
        RegularView.as_view(
            template_name='regular-wp.html',
            form_class=RegularUserFormWithProfile,
            success_template='thanks-wp.html',
        ),
        name="regular-wp",
    ),
    url(
        r'^regular-dpnk/',
        RegularView.as_view(
            template_name='regular-dpnk.html',
            form_class=RegularUserFormDPNK,
            success_template='thanks-dpnk.html',
            source_slug='dpnk',
        ),
        name="regular-dpnk",
    ),
    url(
        r'^campaign-statistics/(?P<campaign_slug>[^&]+)/$',
        CampaignStatistics.as_view(),
        name="campaign-statistics",
    ),
    url(r'^onetime/', onetime, name="onetime"),
    url(r'^donators/', donators, name="donators"),
    url(r'^profiles/', profiles, name="profiles"),
]
