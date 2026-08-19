from django import template

from doc.models import person_display

register = template.Library()


@register.filter(name='person_display')
def do_person_display(person):
    return person_display(person)
