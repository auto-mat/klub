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


urlpatterns = [
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('pdf_storage/', include('pdf_storage.urls')),

    path('check_event/<slug:slug>/', views.CheckEventView.as_view(), name='check_event'),
    path('check_moneyaccount/<slug:slug>/', views.CheckMoneyAccountView.as_view(), name='check_moneyaccount'),
    path('check_last_payments/', views.CheckPaymentView.as_view(), name='check_last_payments'),
    path('interaction/', views.CreateInteractionView.as_view(), name='create_interaction'),
    path('create_credit_card_payment/', views.CreateCreditCardPaymentView.as_view(), name='create_credit_card_payment'),

    path('userprofile/vs/', views.CreateDpchUserProfileView.as_view(), name='userprofile_vs'),
    path('companyprofile/vs/', views.CreateDpchCompanyProfileView.as_view(), name='companyprofile_vs'),
    path('register_userprofile/', views.CreateUserProfileView.as_view(), name='register_userprofile'),

    path('check_last_payment/', views.CheckLastPaymentView.as_view(), name='check_last_payment'),

    path('reset_password_email/', views.ResetPasswordbyEmailView.as_view(), name='reset_password_email'),
    path(
        'reset_password_email_confirm/<slug:uid>/<slug:token>/',
        views.ResetPasswordbyEmailConfirmView.as_view(),
        name='reset_password_email_confirm',
    ),

    path('docs/', schema_view.with_ui('swagger', cache_timeout=None), name='schema-swagger-ui'),

]
