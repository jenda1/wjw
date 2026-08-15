from __future__ import annotations

from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider

from .views import SeznamOAuth2Adapter


class SeznamAccount(ProviderAccount):
    def get_avatar_url(self):
        return self.account.extra_data.get("avatar_url")

    def to_str(self):
        dflt = super().to_str()
        return self.account.extra_data.get("account_name", dflt)


class SeznamProvider(OAuth2Provider):
    id = "seznam"
    name = "Seznam"
    account_class = SeznamAccount
    oauth2_adapter_class = SeznamOAuth2Adapter

    def get_default_scope(self):
        # "identity" je jediný povinný scope a už vrací email + jméno.
        # https://vyvojari.seznam.cz/oauth/scopes
        return ["identity"]

    def extract_uid(self, data):
        return str(data["oauth_user_id"])

    def extract_common_fields(self, data):
        return dict(
            email=data.get("email"),
            first_name=data.get("firstname"),
            last_name=data.get("lastname"),
        )

    def extract_email_addresses(self, data):
        email = data.get("email")
        if not email:
            return []
        return [EmailAddress(email=email, verified=True, primary=True)]


provider_classes = [SeznamProvider]
