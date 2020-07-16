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

    path('check_event/<slug:slug>/', views.CheckEventView.as_view(), name='check_event'),
    path('check_moneyaccount/<slug:slug>/', views.CheckMoneyAccountView.as_view(), name='check_event'),
    path('check_last_payments/', views.CheckPaymentView.as_view(), name='check_last_payments'),
    path('interaction/', views.CreateInteraction.as_view(), name='create_interaciton'),

    path('userprofile/vs/', views.CreateDpchUserProfileView.as_view(), name='userprofile_vs'),
    path('companyprofile/vs/', views.CreateDpchCompanyProfileView.as_view(), name='companyprofile_vs'),

    path('docs/', schema_view.with_ui('swagger', cache_timeout=None), name='schema-swagger-ui'),

]
