import unicodedata
from typing import final, override

from django import forms
from django.contrib.auth import get_user_model
from django.utils.html import format_html

from .models import Profile, ProfileMergeRequest, ProfileStudentRequest, Student

STANOVY_URL = "https://www.waldorfjinonice.cz/wp-content/uploads/2018/01/SpolekWS-stanovy-zapsano-03.03.2017.pdf"

EXISTING_MEMBER_NOTE = "STÁVAJÍCÍ ČLEN – přihlášku podal(a) dříve papírově."


def fold_name(value: str) -> str:
    """Sjednotí jméno pro porovnání bez ohledu na velikost písmen a diakritiku."""
    decomposed = unicodedata.normalize('NFKD', value)
    return ''.join(c for c in decomposed if not unicodedata.combining(c)).casefold()

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
        help_text=(
            "E-mail nelze změnit, je součástí vašeho přihlašovacího účtu. "
            "Je viditelný ostatním členům spolku."
        ),
    )

    existing_member = forms.BooleanField(required=False, widget=forms.HiddenInput())

    address_help_text = "Adresu potřebujeme pouze pro účely evidence spolku, ostatním členům spolku se nezobrazuje."

    class Meta:
        model = Profile

        fields = [
            'first_name', 'last_name', 'email',
            'birth_date',
            'street_and_number', 'city', 'zip_code',
            'phone_number', 'phone_visible',
            'membership', 'comments'
        ]

        help_texts = {
            'birth_date': (
                "Datum narození potřebujeme pouze pro účely evidence spolku, ostatním členům spolku se nezobrazuje."
            ),
            'phone_visible': (
                "Pokud zaškrtnete, telefon bude viditelný i ostatním rodičům z vaší třídy "
                "a ostatním členům, pokud jste členem výkonné rady či mluvčím kruhu "
                "(nikdo další ho nevidí, ať zaškrtnete, nebo ne)."
            ),
        }

        # Můžeš přidat i hezké HTML widgety (např. kalendář pro datum)
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': '+420 123 456 789'}),
            'birth_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'comments': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Poznánky...'}),
        }

    def __init__(self, user, *args, allow_membership_change=True, allow_email_change=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

        if allow_email_change:
            self.fields['email'].disabled = False
            self.fields['email'].required = True
            self.fields['email'].help_text = (
                "Používá se pro přihlášení do systému. Je viditelný ostatním členům spolku."
            )

        if allow_membership_change:
            self.fields['membership'].help_text = format_html(
                'více informací o typu členství najdete ve <a href="{}" target="_blank" rel="noopener">stanovách spolku</a>',
                STANOVY_URL,
            )
        else:
            self.fields['membership'].disabled = True
            self.fields['membership'].help_text = (
                "Typ členství nelze měnit svépomocí, kontaktujte prosím výkonnou radu spolku."
            )

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('existing_member'):
            comments = cleaned_data.get('comments') or ''
            cleaned_data['comments'] = f"{EXISTING_MEMBER_NOTE}\n{comments}".strip()

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data['email']

        others = get_user_model().objects.filter(email__iexact=email)
        if self.user:
            others = others.exclude(pk=self.user.pk)
        if others.exists():
            raise forms.ValidationError("Tento e-mail už používá jiný účet.")

        return email

    def save(self, commit=True):
        profile = super().save(commit=False)

        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save(update_fields=['first_name', 'last_name', 'email'])

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
            folded_first_name = fold_name(first_name)
            folded_last_name = fold_name(last_name)
            for student in Student.objects.filter(birth_date=birth_date):
                if fold_name(student.first_name) == folded_first_name and fold_name(student.last_name) == folded_last_name:
                    cleaned_data['student_by_name'] = student
                    break

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
            'birth_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'comments': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Poznánky...'}),
        }
        help_texts = {
            'birth_date': "Slouží jen k ověření žádosti.",
        }

ProfileStudentRequestFormSet = forms.formset_factory(ProfileStudentRequestForm, extra=1)


@final
class StudentRequestApprovalForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.all().select_related('school_class').order_by('last_name', 'first_name'),
        label="Žák",
        help_text="Žák musí být v systému už založený (administrátorem) - zde ho jen připojíte k rodiči.",
    )


class UserChoiceField(forms.ModelChoiceField):
    @override
    def label_from_instance(self, obj):
        return f"{obj.last_name} {obj.first_name} ({obj.email})"


@final
class MergeRequestApprovalForm(forms.Form):
    target_user = UserChoiceField(
        queryset=get_user_model().objects.all().order_by('last_name', 'first_name'),
        label="Sloučit s existujícím účtem",
        help_text="Vyberte účet, ke kterému se má tato žádost připojit.",
    )

    def __init__(self, *args, candidate_users=(), **kwargs):
        super().__init__(*args, **kwargs)

        if candidate_users and not self.is_bound:
            self.fields['target_user'].initial = candidate_users[0].pk


@final
class ProfileMergeRequestForm(StudentLookupMixin, forms.ModelForm):
    @final
    class Meta:
        model = ProfileMergeRequest

        fields = [ 'old_email', 'first_name', 'last_name', 'comments']

        labels = {
            'old_email': 'E-mail, který jste na těchto stránkách používali dříve',
        }
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Poznánky...'}),
        }
