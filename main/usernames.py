import re

from django.contrib.auth import get_user_model

from .forms import fold_name

_CYRILLIC_TO_LATIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'ґ': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'є': 'ie', 'ж': 'zh', 'з': 'z', 'и': 'i', 'і': 'i', 'ї': 'yi', 'й': 'i', 'к': 'k',
    'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
    'у': 'u', 'ў': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
}


def _transliterate_cyrillic(value: str) -> str:
    return ''.join(_CYRILLIC_TO_LATIN.get(c, c) for c in value.casefold())


def _slug(value: str) -> str:
    return re.sub(r'[^a-z0-9]', '', fold_name(_transliterate_cyrillic(value)))


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
