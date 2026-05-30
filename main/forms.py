from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        # Vybereme pole, která má uživatel možnost sám upravovat
        fields = ['first_name', 'last_name', 'birth_date', 'phone_number', 'email']

        # Můžeš přidat i hezké HTML widgety (např. kalendář pro datum)
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Napište něco o sobě...'}),
        }
