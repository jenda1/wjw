from __future__ import annotations

from django.http import HttpRequest

from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client, OAuth2Error
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)


class SeznamOAuth2Client(OAuth2Client):
    """Seznam's token endpoint expects a JSON request body, not the
    application/x-www-form-urlencoded body used by most OAuth2 providers
    (and by allauth's default OAuth2Client).
    See https://vyvojari.seznam.cz/oauth/doc
    """

    def get_access_token(self, code, pkce_code_verifier=None, extra_data=None):
        data = {
            "redirect_uri": self.callback_url,
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.consumer_key,
            "client_secret": self.consumer_secret,
        }
        if extra_data:
            data.update(extra_data)
        if pkce_code_verifier:
            data["code_verifier"] = pkce_code_verifier
        with get_adapter().get_requests_session() as sess:
            resp = sess.post(
                self.access_token_url,
                json=data,
                headers={"Accept": "application/json"},
            )
            access_token = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else None
            if not access_token or "access_token" not in access_token:
                raise OAuth2Error(f"Error retrieving access token: {resp.content!r}")
            return access_token


class SeznamOAuth2Adapter(OAuth2Adapter):
    provider_id = "seznam"
    client_class = SeznamOAuth2Client
    # Seznam scope je seznam slov oddělených čárkou (ne mezerou).
    scope_delimiter = ","
    authorize_url = "https://login.seznam.cz/api/v1/oauth/auth"
    access_token_url = "https://login.seznam.cz/api/v1/oauth/token"
    profile_url = "https://login.seznam.cz/api/v1/user"

    def complete_login(self, request: HttpRequest, app, token, **kwargs):
        headers = {"Authorization": f"bearer {token.token}"}
        with get_adapter().get_requests_session() as sess:
            resp = sess.get(self.profile_url, headers=headers)
            resp.raise_for_status()
            extra_data = resp.json()
        return self.get_provider().sociallogin_from_response(request, extra_data)


oauth2_login = OAuth2LoginView.adapter_view(SeznamOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(SeznamOAuth2Adapter)
