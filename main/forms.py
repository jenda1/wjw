from typing import final, override

from django import forms
from django.contrib.auth import get_user_model

from .models import Profile, ProfileMergeRequest, ProfileStudentRequest, Student

@final
class ProfileForm(forms.ModelForm):
    # Jméno a příjmení se ukládají do User (allauth je při registraci předvyplní,
    # ale uživatel je zde může opravit).
    first_name = forms.CharField(label="Jméno", required=True)
    last_name = forms.CharField(label="Příjmení", required=True)

    email = forms.EmailField(
        label="E-mail",
        required=False,
        disabled=True,
        help_text="E-mail nelze změnit, je součástí vašeho přihlašovacího účtu.",
    )

    class Meta:
        model = Profile

        fields = [
            'first_name', 'last_name', 'email',
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

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        profile = super().save(commit=False)

        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            if commit:
                self.user.save(update_fields=['first_name', 'last_name'])

        if commit:
            profile.save()

        return profile


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
class StudentRequestApprovalForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.all().order_by('last_name', 'first_name'),
        label="Žák",
        help_text="Žák musí být v systému už založený (administrátorem) - zde ho jen připojíte k rodiči.",
    )


class UserChoiceField(forms.ModelChoiceField):
    @override
    def label_from_instance(self, obj):
        return f"{obj.first_name} {obj.last_name} ({obj.email})"


@final
class MergeRequestApprovalForm(forms.Form):
    target_user = UserChoiceField(
        queryset=get_user_model().objects.all().order_by('last_name', 'first_name'),
        label="Sloučit s existujícím účtem",
        help_text="Vyberte účet, ke kterému se má tato žádost připojit.",
    )


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
