import logging

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

logger = logging.getLogger(__name__)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        logger.exception(
            "Přihlášení přes externího poskytovatele %s selhalo (error=%s)", provider, error, exc_info=exception,
        )
        super().on_authentication_error(request, provider, error=error, exception=exception, extra_context=extra_context)
