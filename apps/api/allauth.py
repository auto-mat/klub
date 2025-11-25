from urllib.parse import urlparse

from django.conf import settings
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_pk_to_url_str
from dj_rest_auth.serializers import PasswordResetSerializer


class AccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        if hasattr(settings, "ACCOUNT_EMAIL_CONFIRMATION_URL"):
            key = emailconfirmation.key
            email = emailconfirmation.email_address.email
            return f"{settings.ACCOUNT_EMAIL_CONFIRMATION_URL}?{urlencode({'key': key, 'email': email})}"
        else:
            return super().get_email_confirmation_url(request, emailconfirmation)

    def render_mail(self, template_prefix, email, context, headers=None):
        ced_app_base_url = getattr(settings, "CED_FRONTEND_APP_BASE_URL")
        if ced_app_base_url:

            class CurrentSite:
                name = _("City experience differently")
                domain = urlparse(ced_app_base_url).netloc

            # Override context current site
            context["current_site"] = CurrentSite
        return super().render_mail(template_prefix, email, context, headers)

    def format_email_subject(self, subject):
        ced_app_base_url = getattr(settings, "CED_FRONTEND_APP_BASE_URL")
        if ced_app_base_url:
            return f"[{urlparse(ced_app_base_url).netloc}] {subject}"
        return super().format_email_subject(subject)


class UserPasswordResetSerializer(PasswordResetSerializer):
    """
    User password reset serializer with overrided default reset password
    confirmation email URL
    """

    def _reset_pass_url_generator(self, request, user, temp_key):
        """Override reset password confirmation email URL"""
        uid = user_pk_to_url_str(user)
        return f"{settings.ACCOUNT_RESET_PASSWORD_CONFIRMATION_URL}?uid={uid}&token={temp_key}"

    def get_email_options(self):
        return {"url_generator": self._reset_pass_url_generator}
