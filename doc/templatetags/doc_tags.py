from django import template
from wagtail.models import BaseViewRestriction

from doc.models import person_display
from main.permissions import VR_MEMBER_GROUP_NAME

register = template.Library()

# Lidsky čitelné názvy skupin pro tooltip u ikony soukromí stránky - skupiny bez
# záznamu zde se zobrazí pod svým technickým jménem (viz main/permissions.py).
GROUP_DISPLAY_NAMES = {
    VR_MEMBER_GROUP_NAME: "Výkonná rada",
}


@register.filter(name='person_display')
def do_person_display(person):
    return person_display(person)


@register.filter(name='display_title')
def do_display_title(page):
    """Titulek stránky pro výpis odkazů (viz SubpagesBlock) - u typů stránek s vlastním
    `display_title` (např. AgendaPage dopočítává datum jednání) použije ten, jinak holý title."""
    return getattr(page, 'display_title', page.title)


@register.inclusion_tag('doc/privacy_badge.html')
def privacy_badge(page):
    """Ikonka u nadpisu stránky, pokud na ní (nebo některém z jejích předků) leží
    Wagtail view restriction - aby bylo na první pohled vidět, že stránka nevidí
    úplně každý. Stránky viditelné jen pro Výkonnou radu mají vlastní odlišnou ikonu."""
    restrictions = list(page.get_view_restrictions())
    if not restrictions:
        return {}

    restriction_types = {r.restriction_type for r in restrictions}
    group_names = set()
    for restriction in restrictions:
        if restriction.restriction_type == BaseViewRestriction.GROUPS:
            group_names.update(restriction.groups.values_list('name', flat=True))

    if restriction_types == {BaseViewRestriction.GROUPS} and group_names == {VR_MEMBER_GROUP_NAME}:
        return {
            'icon': 'bi-shield-lock-fill',
            'tooltip': "Stránka je viditelná jen pro Výkonnou radu.",
        }

    duvody = []
    if BaseViewRestriction.PASSWORD in restriction_types:
        duvody.append("je přístupná se sdíleným heslem")
    if BaseViewRestriction.LOGIN in restriction_types:
        duvody.append("je přístupná jen přihlášeným uživatelům")
    if group_names:
        jmena = ', '.join(sorted(GROUP_DISPLAY_NAMES.get(name, name) for name in group_names))
        duvody.append(f"je přístupná jen skupinám: {jmena}")

    return {
        'icon': 'bi-lock-fill',
        'tooltip': "Stránka není viditelná pro všechny - " + '; '.join(duvody) + '.',
    }


@register.filter(name='get_item')
def get_item(struct_value, key):
    """Přístup do StructValue podle jména pole zjištěného za běhu (např. z query stringu) -
    `{{ item.item }}` v šabloně jde napsat jen s pevným jménem pole."""
    return struct_value.get(key)
