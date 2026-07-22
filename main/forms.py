from typing import final

from django import forms

from .models import Profile, ProfileMergeRequest, ProfileStudentRequest, Student

@final
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile

        fields = [
            'birth_date',
            'street_and_number', 'city', 'zip_code',
            'phone_number',
            'membership', 'comments'
        ]

        # Můžeš přidat i hezké HTML widgety (např. kalendář pro datum)
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': '+420 123 456 789'}),
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Poznánky...'}),
        }


class StudentLookupMixin:
    """Doplní žáka podle jména, příjmení a data narození vyplněných ve formuláři."""

    def clean(self):
        cleaned_data = super().clean()

        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        birth_date = cleaned_data.get('birth_date')

        cleaned_data['student_by_name'] = None
        if first_name and last_name and birth_date:
            cleaned_data['student_by_name'] = Student.objects.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name,
                birth_date=birth_date,
            ).first()

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.student_by_name = self.cleaned_data.get('student_by_name')
        if commit:
            instance.save()
        return instance


@final
class ProfileStudentRequestForm(StudentLookupMixin, forms.ModelForm):
    @final
    class Meta:
        model = ProfileStudentRequest
        fields = ['first_name', 'last_name', 'birth_date', 'comments']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Poznánky...'}),
        }
        help_texts = {
            'birth_date': "Slouží jen k ověření žádosti.",
        }

ProfileStudentRequestFormSet = forms.formset_factory(ProfileStudentRequestForm, extra=1)


@final
class ProfileMergeRequestForm(StudentLookupMixin, forms.ModelForm):
    @final
    class Meta:
        model = ProfileMergeRequest

        fields = [ 'old_email', 'first_name', 'last_name', 'birth_date', 'comments']

        lables = {
            'old_email': 'E-mail, který jste používali dříve (nebo stále používáte)',
        }
        # Můžeš přidat i hezké HTML widgety (např. kalendář pro datum)
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Poznánky...'}),
        }
        help_texts = {
            'birth_date': "Slouží jen k ověření žádosti.",
        }
