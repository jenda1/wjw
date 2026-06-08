import hashlib
import re
from typing import cast

from django.conf import settings
from django.forms import ValidationError


def rodne_cislo_hash(rc_text: str | None):
    if not rc_text:
        return None

    ciste_rc = re.sub(r'[^0-9]', '', str(rc_text))
    soleny_vstup = f"{ciste_rc}{cast(str, settings.SECRET_KEY)}"

    return hashlib.sha256(soleny_vstup.encode('utf-8')).hexdigest()


def rodne_cislo_validate_format(value: str):
    match = re.match(r'^(\d{6})\/?(\d{3,4})$', value)
    if not match:
        raise ValidationError('Rodné číslo nemá správný formát.')
    cislo_text = match.group(1) + match.group(2)
    if len(cislo_text) == 10 and int(cislo_text) % 11 != 0:
        if not (int(cislo_text[:-1]) % 11 == 10 and cislo_text[-1] == '0'):
            raise ValidationError('Rodné číslo není platné.')
