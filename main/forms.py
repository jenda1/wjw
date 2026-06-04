from typing import final

from django import forms

from .models import Profile, ProfileMergeRequest
from . import utils


@final
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile

        fields = [
            'first_name', 'last_name',
            'birth_date',
            'street_and_number', 'city', 'zip_code',
            'phone_number', 'email',
            'membership', 'comments'
        ]

        # Můžeš přidat i hezké HTML widgety (např. kalendář pro datum)
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': '+420 123 456 789'}),
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Poznánky...'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if user:
            # Předvyplnění hodnot
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name

            if user.email:
                self.fields['email'].initial = user.email
                self.fields['email'].widget.attrs['readonly'] = True
                self.fields['email'].widget.attrs['class'] = 'form-control bg-light text-muted'


@final
class RequestMergeUserForm(forms.ModelForm):
    rodne_cislo = forms.CharField(
        label="Rodné číslo dítěte (pro jednoznačné ověření)",
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'YYMMDD/XXXX'
        }),
        help_text="Rodné číslo v databázi neukládáme, slouží jen k ověření žádosti."
    )

    @final
    class Meta:
        model = ProfileMergeRequest

        fields = [ 'old_email', 'student_name', 'rodne_cislo', 'comments']

        lables = {
            'old_email': 'E-mail, který jste používali dříve (nebo stále používáte)',
            'student_name': 'Jméno a třída varšeho dítěte',
        }
        # Můžeš přidat i hezké HTML widgety (např. kalendář pro datum)
        widgets = {
            'student_name': forms.TextInput(attrs={'placeholder': 'Tomáš Novák, 3. třída' }),
            'comments': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Poznánky...'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)

        rc_hash = utils.rodne_cislo_hash(self.cleaned_data['rodne_cislo'])

        if commit:
            instance.save()
        return instance
