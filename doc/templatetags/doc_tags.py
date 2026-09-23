from django import template

from doc.models import person_display

register = template.Library()


@register.filter(name='person_display')
def do_person_display(person):
    return person_display(person)


@register.filter(name='get_item')
def get_item(struct_value, key):
    """Přístup do StructValue podle jména pole zjištěného za běhu (např. z query stringu) -
    `{{ item.item }}` v šabloně jde napsat jen s pevným jménem pole."""
    return struct_value.get(key)
