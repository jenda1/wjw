from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment
from django_bootstrap5.templatetags.django_bootstrap5 import bootstrap_messages, bootstrap_pagination, render_form, render_field, render_button

def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': static,
        'url': reverse,
        # Registrace Bootstrap funkcí pro Jinja2
        'bootstrap_form': render_form,
        'bootstrap_field': render_field,
        'bootstrap_button': render_button,
        'bootstrap_messages': bootstrap_messages,
        'bootstrap_pagination': bootstrap_pagination,
    })
    return env
