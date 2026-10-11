import re
import unicodedata

from django.db import migrations


def _slug(value: str) -> str:
    decomposed = unicodedata.normalize('NFKD', value or '')
    folded = ''.join(c for c in decomposed if not unicodedata.combining(c)).casefold()
    return re.sub(r'[^a-z0-9]', '', folded)


def set_username_format(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    taken_lower = set()

    users_with_social_account = User.objects.filter(socialaccount__isnull=False).distinct()

    for user in users_with_social_account.order_by('id'):
        base = f"{_slug(user.last_name) or 'uzivatel'}.{_slug(user.first_name) or 'uzivatel'}"

        username = base
        suffix = 2
        while (
            username.lower() in taken_lower
            or User.objects.filter(username=username).exclude(pk=user.pk).exists()
        ):
            username = f"{base}{suffix}"
            suffix += 1

        taken_lower.add(username.lower())

        if user.username != username:
            user.username = username
            user.save(update_fields=['username'])


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_mailinglist_views'),
        ('auth', '0001_initial'),
        ('socialaccount', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(set_username_format, migrations.RunPython.noop),
    ]
