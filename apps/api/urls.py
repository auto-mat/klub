from django.urls import include, path, re_path
from django.conf.urls import url

from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from rest_framework import permissions

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from apps.api import frontend
from apps.api.frontend import whoami_unit
from apps.api.frontend.unknown_user_volunteer_unit import (
    VolunteerView,
)
from apps.api.frontend.unknown_user_sign_up_for_event_unit import (
    SignUpForEventView,
)
from apps.api.frontend.unknown_user_apply_for_membership_unit import (
    ApplyForMembershipView,
)

from . import views
from .rest_registration import (
    ConfirmEmailView,
    CustomRegisterView,
    HasUserVerifiedEmailAddress,
    SendRegistrationConfirmationEmail,
)
from .zmj.urls import urlpatterns as urlpatterns_zmj

schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version="v1",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns_bronto = [
    path("event/", views.EventListView.as_view(), name="event"),
    path("event/<int:id>/", views.EventRetrieveView.as_view(), name="event_detail"),
    path(
        "administrative_unit/",
        views.AdministrativeUnitView.as_view(),
        name="administrative_unit",
    ),
]

urlpatterns = [
    # auth
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path(
        "auth/",
        include("dj_rest_auth.urls"),
    ),
    path(
        "auth/registration/",
        CustomRegisterView.as_view(),
        name="custom_register",
    ),
    path(
        "auth/registration/account-confirm-email/<str:key>/",
        ConfirmEmailView.as_view(),
        name="account_confirm_email",
    ),
    path(
        "auth/registration/has-user-verified-email-address/",
        HasUserVerifiedEmailAddress.as_view(),
        name="has-user-verified-email-address",
    ),
    path(
        "auth/registration/send-confirmation-email/",
        SendRegistrationConfirmationEmail.as_view(),
        name="send-registration-confirmation-email",
    ),
    # Events
    path("event/", views.EventListView.as_view(), name="event"),
    path("event/<int:id>/", views.EventRetrieveView.as_view(), name="event_detail"),
    path(
        "administrative_unit/",
        views.AdministrativeUnitView.as_view(),
        name="administrative_unit",
    ),
    # vizus
    path(
        "check_event/<slug:slug>/", views.CheckEventView.as_view(), name="check_event"
    ),
    path(
        "check_moneyaccount/<slug:slug>/",
        views.CheckMoneyAccountView.as_view(),
        name="check_moneyaccount",
    ),
    path(
        "check_last_payments/",
        views.CheckPaymentView.as_view(),
        name="check_last_payments",
    ),
    path(
        "interaction/", views.CreateInteractionView.as_view(), name="create_interaction"
    ),
    path(
        "interaction-type/",
        views.InteractionTypeView.as_view(),
        name="interaction-type",
    ),
    url("frontend/whoami", whoami_unit.who_am_i, name="frontend_whoami"),
    url("frontend/", include(frontend.router.urls)),
    path(
        "create_credit_card_payment/",
        views.CreateCreditCardPaymentView.as_view(),
        name="create_credit_card_payment",
    ),
    path(
        "userprofile/vs/",
        views.CreateDpchUserProfileView.as_view(),
        name="userprofile_vs",
    ),
    path(
        "companyprofile/vs/",
        views.CreateDpchCompanyProfileView.as_view(),
        name="companyprofile_vs",
    ),
    # Unknown user endpoints
    re_path(
        r"^volunteer/",
        VolunteerView.as_view(),
        name="unknown_user_volunteer",
    ),
    re_path(
        r"^sign_up_for_event/",
        SignUpForEventView.as_view(),
        name="unknown_user_sign_up_for_event",
    ),
    re_path(
        r"^apply_for_membership/",
        ApplyForMembershipView.as_view(),
        name="unknown_user_apply_for_membership",
    ),
    # invest
    path("pdf_storage/", include("pdf_storage.urls")),
    path(
        "register_userprofile/",
        views.CreateUserProfileView.as_view(),
        name="register_userprofile",
    ),
    path(
        "check_last_payment/",
        views.CheckLastPaymentView.as_view(),
        name="check_last_payment",
    ),
    # bronto
    path("bronto/", include(urlpatterns_bronto)),  # handle better url
    # reset email viewss
    path(
        "reset_password_email/",
        views.ResetPasswordbyEmailView.as_view(),
        name="reset_password_email",
    ),
    path(
        "reset_password_email_confirm/<slug:uid>/<slug:token>/",
        views.ResetPasswordbyEmailConfirmView.as_view(),
        name="reset_password_email_confirm",
    ),
    # docs
    path(
        "docs/",
        schema_view.with_ui("swagger", cache_timeout=None),
        name="schema-swagger-ui",
    ),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # zmj
    path("zmj/", include(urlpatterns_zmj)),
]
