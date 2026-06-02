import hashlib
import re
from typing import cast

from django.conf import settings


def rodne_cislo_hash(rc_text: str | None):
    if not rc_text:
        return None

    ciste_rc = re.sub(r'[^0-9]', '', str(rc_text))
    soleny_vstup = f"{ciste_rc}{cast(str, settings.SECRET_KEY)}"

    return hashlib.sha256(soleny_vstup.encode('utf-8')).hexdigest()
