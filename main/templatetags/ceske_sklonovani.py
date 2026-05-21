from django import template
import vokativ

register = template.Library()

@register.filter(name='vokativ')
def do_pateho_pada(jmeno):
    if not jmeno:
        return ""
    # vokativ.vokativ() vrátí jméno v 5. pádě
    return vokativ.vokativ(str(jmeno).strip())
