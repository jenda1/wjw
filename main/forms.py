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


class StudentLookupMixin(forms.Form):
    """Ověří dítě podle jména, příjmení a data narození místo rodného čísla."""

    student_first_name = forms.CharField(label="Jméno dítěte", required=False)
    student_last_name = forms.CharField(label="Příjmení dítěte", required=False)
    student_birth_date = forms.DateField(
        label="Datum narození dítěte",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Slouží jen k ověření žádosti.",
    )

    def clean(self):
        cleaned_data = super().clean()

        first_name = cleaned_data.get('student_first_name')
        last_name = cleaned_data.get('student_last_name')
        birth_date = cleaned_data.get('student_birth_date')

        cleaned_data['student_by_rc'] = None
        if first_name and last_name and birth_date:
            cleaned_data['student_by_rc'] = Student.objects.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name,
                birth_date=birth_date,
            ).first()

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.student_by_rc = self.cleaned_data.get('student_by_rc')
        if commit:
            instance.save()
        return instance


@final
class ProfileStudentRequestForm(StudentLookupMixin, forms.ModelForm):
    @final
    class Meta:
        model = ProfileStudentRequest
        fields = ['student_name', 'comments']
        widgets = {
            'student_name': forms.TextInput(attrs={'placeholder': 'Tomáš Novák, 3. třída' }),
            'comments': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Poznánky...'}),
        }

ProfileStudentRequestFormSet = forms.formset_factory(ProfileStudentRequestForm, extra=1)


@final
class ProfileMergeRequestForm(StudentLookupMixin, forms.ModelForm):
    @final
    class Meta:
        model = ProfileMergeRequest

        fields = [ 'old_email', 'student_name', 'comments']

        lables = {
            'old_email': 'E-mail, který jste používali dříve (nebo stále používáte)',
            'student_name': 'Jméno a třída varšeho dítěte',
        }
        # Můžeš přidat i hezké HTML widgety (např. kalendář pro datum)
        widgets = {
            'student_name': forms.TextInput(attrs={'placeholder': 'Tomáš Novák, 3. třída' }),
            'comments': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Poznánky...'}),
        }
