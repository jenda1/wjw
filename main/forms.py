from typing import final

from django import forms

from .models import Profile, RequestMergeUser
from . import utils


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
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Poznánky...'}),
        }


@final
class RequestMergeUserForm(forms.ModelForm):
    rodne_cislo = forms.CharField(
        label="Rodné číslo dítěte (pro jednoznačné ověření)",
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'YYMMDD/XXXX'
        }),
        help_text="Rodné číslo v databázi neukládáme, slouží jen k ověření!"
    )

    @final
    class Meta:
        model = RequestMergeUser

        fields = [ 'old_email', 'student_name', 'rodne_cislo', 'comments']

        # Můžeš přidat i hezké HTML widgety (např. kalendář pro datum)
        widgets = {
            'old_email': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'student_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tomáš Novák, 3. třída'
            }),
            'comments': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Poznánky...'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)

        rc_hash = utils.rodne_cislo_hash(self.cleaned_data['rodne_cislo'])

        if commit:
            instance.save()
        return instance
