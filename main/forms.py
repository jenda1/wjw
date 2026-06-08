from typing import final

from django import forms

from main.fields import StudentByRodneCisloField

from . import utils
from .models import Profile, ProfileMergeRequest, ProfileStudentRequest, Student

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
class ProfileStudentRequestForm(forms.ModelForm):
    student_by_rc = StudentByRodneCisloField()

    @final
    class Meta:
        model = ProfileStudentRequest
        fields = ['student_name', 'student_by_rc', 'comments']
        widgets = {
            'student_name': forms.TextInput(attrs={'placeholder': 'Tomáš Novák, 3. třída' }),
            'comments': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Poznánky...'}),
        }

ProfileStudentRequestFormSet = forms.formset_factory(ProfileStudentRequestForm, extra=1)


@final
class ProfileMergeRequestForm(forms.ModelForm):
    student_by_rc = StudentByRodneCisloField()

    @final
    class Meta:
        model = ProfileMergeRequest

        fields = [ 'old_email', 'student_name', 'student_by_rc', 'comments']

        lables = {
            'old_email': 'E-mail, který jste používali dříve (nebo stále používáte)',
            'student_name': 'Jméno a třída varšeho dítěte',
        }
        # Můžeš přidat i hezké HTML widgety (např. kalendář pro datum)
        widgets = {
            'student_name': forms.TextInput(attrs={'placeholder': 'Tomáš Novák, 3. třída' }),
            'comments': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Poznánky...'}),
        }
