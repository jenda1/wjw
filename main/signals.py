from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import pre_social_login
from django.shortcuts import redirect
from django.contrib import messages

# from .models import Parent
# @receiver(user_signed_up)
# def create_parent_profile(request, user, **kwargs):
#     first_name = ""
#     last_name = ""
#
#     sociallogin = kwargs.get('sociallogin')
#     if sociallogin:
#         extra_data = sociallogin.account.extra_data
#         print(extra_data)  # Debug: Print the extra data to see its structure
#         first_name = extra_data.get('given_name', '') or extra_data.get('first_name', '')
#         last_name = extra_data.get('family_name', '') or extra_data.get('last_name', '')
#
#     if not first_name and not last_name:
#         first_name = user.first_name
#         last_name = user.last_name
#
#     _ = Parent.objects.get_or_create(
#         user=user,
#         defaults={
#             'first_name': first_name,
#             'last_name': last_name,
#         }
#     )
#

@receiver(pre_social_login)
def load_social_data(sender, request, sociallogin, **kwargs):
    # 1. Získat instanci uživatele, která se právě vytváří/přihlašuje
    user = sociallogin.user

    # 2. Získat syrová data (extra_data), která poslala sociální síť
    provider = sociallogin.account.provider
    extra_data = sociallogin.account.extra_data

    # Příklad pro GOOGLE
    if provider == 'google':
        user.email = extra_data.get('email', '')
        user.first_name = extra_data.get('given_name', '')
        user.last_name = extra_data.get('family_name', '')

    # Příklad pro FACEBOOK
    elif provider == 'facebook':
        user.email = extra_data.get('email', '')
        user.first_name = extra_data.get('first_name', '')
        user.last_name = extra_data.get('last_name', '')

    # Příklad pro GITHUB (GitHub často nevrací rozdělené jméno)
    elif provider == 'github':
        user.email = extra_data.get('email', '')
        celé_jméno = extra_data.get('name', '')  # Vrací např. "Jan Novák"
        if celé_jméno and ' ' in celé_jméno:
            user.first_name, user.last_name = celé_jméno.split(' ', 1)
        else:
            user.first_name = celé_jméno


@receiver(pre_social_login)
def debug_social_data(sender, request, sociallogin, **kwargs):
    import pprint
    print(f"--- DATA PRO POSKYTOVATELE: {sociallogin.account.provider} ---")
    pprint.pprint(sociallogin.account.extra_data)


@receiver(user_signed_up)
def presmeruj_noveho_uzivatele(request, user, **kwargs):
    request.session['new_user_redirect'] = True
