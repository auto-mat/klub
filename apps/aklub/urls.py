from aklub import views

from django.conf.urls import url

urlpatterns = [
    url(
        r'^regular/',
        views.RegularView.as_view(),
        name="regular",
    ),
    url(
        r'^regular-wp/',
        views.RegularView.as_view(
            template_name='regular-wp.html',
            form_class=views.RegularUserFormWithProfile,
            success_template='thanks-wp.html',
        ),
        name="regular-wp",
    ),
    url(
        r'^regular-dpnk/',
        views.RegularView.as_view(
            template_name='regular-dpnk.html',
            form_class=views.RegularUserFormDPNK,
            success_template='thanks-dpnk.html',
            source_slug='dpnk',
        ),
        name="regular-dpnk",
    ),
    url(
        r'^regular-darujme/',
        views.RegularView.as_view(
            template_name='regular.html',
            form_class=views.RegularDarujmeUserForm,
            success_template='thanks-darujme.html',
        ),
        name="regular-darujme",
    ),
    url(
        r'^campaign-statistics/(?P<campaign_slug>[^&]+)/$',
        views.CampaignStatistics.as_view(),
        name="campaign-statistics",
    ),
    url(r'^onetime/', views.onetime, name="onetime"),
    url(r'^donators/', views.donators, name="donators"),
    url(r'^profiles/', views.profiles, name="profiles"),
]
