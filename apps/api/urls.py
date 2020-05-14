from django.urls import include, path

from . import views

urlpatterns = [
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    path('userprofile/vs', views.CreateDpchUserProfileView.as_view()),
    path('companyprofile/vs', views.CreateDpchCompanyProfileView.as_view()),

]
