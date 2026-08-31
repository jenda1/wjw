from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import pre_social_login
from django.contrib import messages
from django.dispatch import receiver


@receiver(pre_social_login)
def load_social_data(sender, request, sociallogin, **kwargs):
    user = sociallogin.user

    provider = sociallogin.account.provider
    extra_data = sociallogin.account.extra_data

    # Příklad pro GOOGLE
    if provider == 'google':
        user.email = extra_data.get('email', '')
        user.first_name = extra_data.get('given_name', '')
        user.last_name = extra_data.get('family_name', '')

    # Příklad pro GITHUB (GitHub často nevrací rozdělené jméno)
    elif provider == 'github':
        user.email = extra_data.get('email', '')
        celé_jméno = extra_data.get('name', '')  # Vrací např. "Jan Novák"
        if celé_jméno and ' ' in celé_jméno:
            user.first_name, user.last_name = celé_jméno.split(' ', 1)
        else:
            user.first_name = celé_jméno


#@receiver(pre_social_login)
@receiver(user_signed_up)
def new_user(sender, request, sociallogin, **kwargs):
    messages.add_message(request, messages.INFO, "prvni_login")

    # DEBUG
    import pprint
    print(f"--- DATA PRO POSKYTOVATELE: {sociallogin.account.provider} ---")
    pprint.pprint(sociallogin.account.extra_data)
