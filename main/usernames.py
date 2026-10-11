import re

from django.contrib.auth import get_user_model

from .forms import fold_name


def _slug(value: str) -> str:
    return re.sub(r'[^a-z0-9]', '', fold_name(value))


def generate_username(first_name: str, last_name: str, *, exclude_pk: int | None = None) -> str:
    """Vygeneruje unikátní uživatelské jméno ve formátu prijmeni.jmeno (prijmeni.jmenoX při kolizi)."""
    base = f"{_slug(last_name) or 'uzivatel'}.{_slug(first_name) or 'uzivatel'}"

    User = get_user_model()
    qs = User.objects.all()
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)

    username = base
    suffix = 2
    while qs.filter(username=username).exists():
        username = f"{base}{suffix}"
        suffix += 1
    return username
