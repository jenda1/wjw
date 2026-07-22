from django import template
import vokativ

register = template.Library()

@register.filter(name='vokativ')
def do_pateho_pada(jmeno:str) -> str:
    if not jmeno:
        return ""
    # vokativ.vokativ() vrátí jméno v 5. pádě
    return vokativ.vokativ(str(jmeno).strip())


@register.inclusion_tag('main/tags/login_status.html', takes_context=True)
def render_login_status(context):
    user = context.get('user')

    is_logged_in = user and user.is_authenticated
    is_member = not user.is_anonymous and getattr(user, 'profile', None)

    return {
        'user': user,
        'is_logged_in': is_logged_in,
        'is_member': is_member,
    }


@register.inclusion_tag('main/tags/edit_icon.html')
def edit_icon(url, title="Upravit"):
    """
    Použití v šabloně: {% edit_icon url "Popisek" %}
    """
    return {
        'url': url,
        'title': title,
    }
