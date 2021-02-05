from django.conf import settings

from oauth2_provider.scopes import BaseScopes


class CustomApplicationScopes(BaseScopes):
    """
    Rewrite of default Scopes

    Get available scopes for current app and apply them in token
    """

    def get_available_scopes(self, application=None, request=None, *args, **kwargs):
        return settings.OAUTH2_PROVIDER["SCOPES"].keys()

    def get_default_scopes(self, application=None, request=None, *args, **kwargs):
        return application.applicationscopeselector.default_scopes.split(" ")
