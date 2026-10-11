import logging

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_field, user_username
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .usernames import generate_username

logger = logging.getLogger(__name__)


class AccountAdapter(DefaultAccountAdapter):
    def populate_username(self, request, user):
        first_name = user_field(user, "first_name")
        last_name = user_field(user, "last_name")

        if not user_username(user) and first_name and last_name:
            user_username(user, generate_username(first_name, last_name))
        else:
            super().populate_username(request, user)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        logger.exception(
            "Přihlášení přes externího poskytovatele %s selhalo (error=%s)", provider, error, exc_info=exception,
        )
        super().on_authentication_error(request, provider, error=error, exception=exception, extra_context=extra_context)
