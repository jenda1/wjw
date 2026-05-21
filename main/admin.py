from django import forms
from django.contrib import admin
from .models import ClassCollective, Parent, Student, ParentRelationship
from .models import validate_rodne_cislo_format, hash_rodne_cislo

class StudentInline(admin.TabularInline):
    model = Student
    extra = 1
    fields = ("first_name", "last_name", "school_class")

class ParentRelationshipInline(admin.TabularInline):
    model = ParentRelationship


class StudentAdminForm(forms.ModelForm):
    # Přidáme do formuláře virtuální textové pole, které v modelu neexistuje
    rc_number = forms.CharField(
        max_length=11,
        required=True,
        label="Rodné číslo",
        help_text="Zadejte ve formátu RRMMDD/XXXX. Číslo se ihned zahashuje a neuloží se v čitelné podobě.",
        validators=[validate_rodne_cislo_format]  # Použijeme náš validátor
    )

    class Meta:
        model = Student
        fields = '__all__'  # Načte ostatní pole (např. jméno)

    def save(self, commit=True):
        # Než se model uloží, vytáhneme rodné číslo z formuláře a zahashujeme ho
        instance = super().save(commit=False)
        rc_number = self.cleaned_data.get('rc_number')
        
        if rc_number:
            instance.rc_hash = hash_rodne_cislo(rc_number)

        if commit:
            instance.save()

        return instance

@admin.register(ClassCollective)
class ClassCollectiveAdmin(admin.ModelAdmin):
    list_display = ("school_class", "year", "variant")
    list_filter = ("school_class",)
    search_fields = ("school_class", "year", "variant")
    inlines = [StudentInline]


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "phone_number")
    inlines = [ParentRelationshipInline]

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    form = StudentAdminForm
    list_display = ("first_name", "last_name", "rc_hash", "school_class")
    inlines = [ParentRelationshipInline]
    search_fields = ("first_name",
                     "last_name", "rc_hash", "school_class")


