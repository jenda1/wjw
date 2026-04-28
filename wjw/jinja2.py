from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment, pass_context
from django_bootstrap5.templatetags.django_bootstrap5 import (
    bootstrap_javascript,
    bootstrap_messages,
    bootstrap_pagination,
    render_form,
    render_field,
    render_button,
    bootstrap_css,
)


# This wrapper fixes the AttributeError
@pass_context
def bootstrap_messages_wrapper(context, **kwargs):
    return bootstrap_messages(dict(context), **kwargs)


def environment(**options):
    env = Environment(**options)
    env.globals.update(
        {
            "static": static,
            "url": reverse,
            # Registrace Bootstrap funkcí pro Jinja2
            "bootstrap_css": bootstrap_css,
            "bootstrap_form": render_form,
            "bootstrap_field": render_field,
            "bootstrap_button": render_button,
            "bootstrap_messages": bootstrap_messages_wrapper,  # Use the wrapper here
            "bootstrap_pagination": bootstrap_pagination,
            "bootstrap_javascript": bootstrap_javascript,
        }
    )
    return env
