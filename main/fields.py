from django import forms
from django.core.exceptions import ValidationError

from main import utils
from main.models import Student

class StudentByRodneCisloField(forms.CharField):
    def __init__(self, *args, **kwargs):
        attrs={'placeholder': 'YYMMDD/XXXX'}

        kwargs.setdefault('max_length', 11)
        kwargs.setdefault('label', "Rodné číslo")
        kwargs.setdefault('widget', forms.TextInput(attrs=attrs))
        kwargs.setdefault('help_text', "Rodné číslo neukládáme, slouží jen k ověření žádosti.")

        super().__init__(*args, **kwargs)

    def clean(self, value):
        value = super().clean(value)
        if not value:
            return value

        utils.rodne_cislo_validate_format(value)
        rc_hash = utils.rodne_cislo_hash(value)
        student =  Student.objects.filter(rc_hash=rc_hash).first()

        return student
