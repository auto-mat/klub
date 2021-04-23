from django.urls import include, path

from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from rest_framework import permissions

from . import views

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns_bronto = [
    path('register_userprofile_interaction/', views.UserProfileInteractionView.as_view(), name='userprofile_interaction'),
    path('event/', views.EventListView.as_view(), name='event'),
    path('administrative_unit/', views.AdministrativeUnitView.as_view(), name='administrative_unit'),
]
# TODO: separate others as bronto (if possible)
urlpatterns = [
    # auth
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    # vizus
    path('check_event/<slug:slug>/', views.CheckEventView.as_view(), name='check_event'),
    path('check_moneyaccount/<slug:slug>/', views.CheckMoneyAccountView.as_view(), name='check_moneyaccount'),
    path('check_last_payments/', views.CheckPaymentView.as_view(), name='check_last_payments'),
    path('interaction/', views.CreateInteractionView.as_view(), name='create_interaction'),
    path('create_credit_card_payment/', views.CreateCreditCardPaymentView.as_view(), name='create_credit_card_payment'),
    path('userprofile/vs/', views.CreateDpchUserProfileView.as_view(), name='userprofile_vs'),
    path('companyprofile/vs/', views.CreateDpchCompanyProfileView.as_view(), name='companyprofile_vs'),

    # invest
    path('pdf_storage/', include('pdf_storage.urls')),
    path('register_userprofile/', views.CreateUserProfileView.as_view(), name='register_userprofile'),
    path('check_last_payment/', views.CheckLastPaymentView.as_view(), name='check_last_payment'),

    # bronto
    path("bronto/", include(urlpatterns_bronto)),  # handle better url


    # reset email viewss
    path('reset_password_email/', views.ResetPasswordbyEmailView.as_view(), name='reset_password_email'),
    path(
        'reset_password_email_confirm/<slug:uid>/<slug:token>/',
        views.ResetPasswordbyEmailConfirmView.as_view(),
        name='reset_password_email_confirm',
    ),

    # docs
    path('docs/', schema_view.with_ui('swagger', cache_timeout=None), name='schema-swagger-ui'),
]
