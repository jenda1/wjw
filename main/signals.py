from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from .models import Parent

@receiver(user_signed_up)
def create_parent_profile(request, user, **kwargs):
    first_name = ""
    last_name = ""

    sociallogin = kwargs.get('sociallogin')
    if sociallogin:
        extra_data = sociallogin.account.extra_data
        print(extra_data)  # Debug: Print the extra data to see its structure
        first_name = extra_data.get('given_name', '') or extra_data.get('first_name', '')
        last_name = extra_data.get('family_name', '') or extra_data.get('last_name', '')

    if not first_name and not last_name:
        first_name = user.first_name
        last_name = user.last_name

    _ = Parent.objects.get_or_create(
        user=user,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
        }
    )
