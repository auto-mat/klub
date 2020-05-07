from django.urls import path

from . import views

urlpatterns = [
    path('userprofile/vs', views.CreateDpchUserProfileView.as_view()),
    path('companyprofile/vs', views.CreateDpchCompanyProfileView.as_view()),

]
