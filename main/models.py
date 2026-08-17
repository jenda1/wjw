from datetime import date
from typing import final, override, cast

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from simple_history.models import HistoricalRecords

import requests

def validuj_datum_narozeni(value):
    """Bariéra, která nepustí datum z budoucnosti a příliš staré lidi."""
    if not value:
        return

    today = date.today()

    if value > today:
        raise ValidationError("Datum narození nemůže být v budoucnosti.")

    age: int = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if age < 18:
        raise ValidationError("Datum narození je špatně (a nebo nejste plnoletý(á)?!?).")

    if age > 90:
        raise ValidationError("Datum narození je špatně (a nebo jste otec Járy Cimrmana?).")


def validuj_adresu(street_and_number:str, city:str, zip_code:str):
    full_address = f"{street_and_number}, {city}, {zip_code}"

    # Mapy.cz Geocoding API setup
    url = cast(str, settings.MAPY_CZ_API_URL)
    api_key = cast(str, settings.MAPY_CZ_API_KEY)

    params = {"query": full_address, "apikey": api_key, "lang": cast(str, settings.LANGUAGE_CODE), "locality": "cz"}
    try:
        response = requests.get(url, params=params, timeout=5)
        if not response:
            reason = response.reason if response.reason else "Neznámá chyba"
            raise ValidationError({"street_and_number": "Interní chyba při ověřování adresy: " + reason})

        data = response.json()
        if not data.get("items"):
            raise ValidationError({
                'street_and_number': (
                    "Adresu se nepodařilo zkontrolovat - zdá se, že neexistuje (podle mapy.cz). "
                    "Zkontrolujte prosím překlepy."
                )
            })

        best_match = data["items"][0]
        if best_match.get("type") not in ["regional.address"]:
            raise ValidationError({
                'street_and_number': (
                    "Adresa možná existuje, ale není jednoznačná - číslo popisné buď chybí a nebo neexistuje."
                )
            })

    except requests.exceptions.RequestException:
        raise ValidationError({"street_and_number": "chyba ... zkuste to pozdeji"})

psc_validator = RegexValidator(
    regex=r'^\d{3}\s?\d{2}$',
    message="Zadejte platné PSČ ve formátu 123 45 nebo 12345."
)

@final
class ClassCollective(models.Model):
    class SchoolClassType(models.IntegerChoices):
        R1 = 1, "1. ročník"
        R2 = 2, "2. ročník"
        R3 = 3, "3. ročník"
        R4 = 4, "4. ročník"
        R5 = 5, "5. ročník"
        R6 = 6, "6. ročník"
        R7 = 7, "7. ročník"
        R8 = 8, "8. ročník"
        R9 = 9, "9. ročník"

    year = models.PositiveIntegerField(
        verbose_name="Rok nástupu",
        default=date.today().year,
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
    )

    school_class = models.IntegerField(
        choices=SchoolClassType.choices, null=True, blank=True
    )

    variant = models.CharField(max_length=20, null=True, blank=True)

    representatives = models.ManyToManyField(
        'Profile',
        through="ClassRepresentative",
        related_name="represented_classes",
        verbose_name="Zástupci třídy",
    )

    history = HistoricalRecords()

    @final
    class Meta:
        verbose_name = "Třídna"
        verbose_name_plural = "Třídy"
        ordering = ["year", "variant"]
        constraints = [
            models.UniqueConstraint(
                fields=["year", "variant"], name="unique_class_collective_name"
            )
        ]

    @override
    def __str__(self):
        return (
            f"{self.get_school_class_display()}{', ' + self.variant if self.variant else ''} ({self.year})"
        )


@final
class Profile(models.Model):
    class ProfileStatus(models.TextChoices):
        PENDING = 'PE', 'čeká na schválení'
        ACTIVE = 'AC', 'člen'
        CANCELLED = 'CA', 'zrušený'

    class MembershipType(models.TextChoices):
        ACTIVE = 'A', 'aktivní'
        PASSIVE = 'P', 'přispívající'

    user = models.OneToOneField(
        cast(str, settings.AUTH_USER_MODEL),
        on_delete=models.PROTECT,
        related_name='profile',
        verbose_name="Uživatelský účet",
    )

    birth_date = models.DateField(
        blank=False, null=False, validators=[validuj_datum_narozeni], verbose_name="Datum narození"
    )

    street_and_number = models.CharField("Ulice a číslo popisné", blank=False, max_length=150)
    city = models.CharField("Město", blank=False, max_length=100)
    zip_code = models.CharField("PSČ", validators=[psc_validator], max_length=10)

    phone_number = PhoneNumberField(blank=True, verbose_name="Telefonní číslo")

    membership = models.CharField(max_length=2, choices=MembershipType.choices, default=MembershipType.ACTIVE)

    status = models.CharField(max_length=2, choices=ProfileStatus.choices, default=ProfileStatus.PENDING)
    comments = models.TextField(blank=True, verbose_name="Poznámky")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Datum podání žádosti")

    history = HistoricalRecords()

    @final
    class Meta:
        verbose_name = "Člen spolku"
        verbose_name_plural = "Členové spolku"

    @override
    def clean(self):
        super().clean()

        if self.street_and_number and self.city and self.zip_code:
            validuj_adresu(self.street_and_number, self.city, self.zip_code)

    @override
    def __str__(self):
        stav = self.status if self.status == self.ProfileStatus.PENDING[0] else self.membership
        return f"{self.user.first_name} {self.user.last_name} ({stav})"

    def get_status_full(self):
        return f"{self.get_status_display()} - {self.get_membership_display()}"



@final
class Student(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Jméno")
    last_name = models.CharField(max_length=100, verbose_name="Příjmení")

    birth_date = models.DateField(verbose_name="Datum narození")

    school_class = models.ForeignKey(
        ClassCollective,
        on_delete=models.PROTECT,
        related_name="students",
        verbose_name="Třída",
    )

    parents = models.ManyToManyField(
        Profile,
        through="ParentRelationship",
        related_name="children",
        verbose_name="Zákonní zástupci",
    )

    history = HistoricalRecords()

    @final
    class Meta:
        verbose_name = "Žák"
        verbose_name_plural = "Žáci"

    @override
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.school_class})"


@final
class ParentRelationship(models.Model):
    parent = models.ForeignKey(Profile, blank=False, null=False, on_delete=models.PROTECT)
    student = models.ForeignKey(Student, null=True, on_delete=models.PROTECT)

    valid_from = models.DateField(auto_now=True, verbose_name="Platnost od")
    valid_until = models.DateField(null=True, blank=True, verbose_name="Platnost do")

    paring_info = models.CharField(max_length=200, blank=True, null=True, verbose_name="Infromace o žákovi")

    @final
    class Meta:
        # Zabráníme duplicitnímu vztahu mezi stejným rodičem a dítětem
        constraints = [
            models.UniqueConstraint(
                fields=["student", "parent"], name="student_parent_unique"
            )
        ]
        verbose_name = "Vztah rodič-žák"
        verbose_name_plural = "Vztahy rodič-žák"

    @override
    def __str__(self):
        return f"{self.parent} -> {self.student} ({self.valid_from} - {self.valid_until or 'současnost'})"


@final
class ClassRepresentative(models.Model):
    class RepresentantType(models.TextChoices):
        VR = 'VR', "zástupce ve VR"
        TREASURER = 'P', "pokladník"

    school_class = models.ForeignKey(ClassCollective, blank=False, null=False, on_delete=models.PROTECT)
    representative = models.ForeignKey(Profile, blank=False, null=False, on_delete=models.PROTECT)

    representant_type = models.CharField(
        max_length=20, choices=RepresentantType.choices, verbose_name="Typ zástupce"
    )

    valid_from = models.DateField(default=date.today, verbose_name="Platnost od")
    valid_until = models.DateField(null=True, blank=True, verbose_name="Platnost do")

    @final
    class Meta:
        # Zabráníme duplicitnímu vztahu mezi stejným zástupcem, třídou, typem zastoupení
        # a obdobím platnosti (stejná osoba tak může tutéž roli ve třídě zastávat
        # opakovaně v různých, na sebe nenavazujících obdobích - viz clean()).
        constraints = [
            models.UniqueConstraint(
                fields=["school_class", "representative", "representant_type", "valid_until"],
                name="class_representative_unique",
            )
        ]
        verbose_name = "Zástupce třídy"
        verbose_name_plural = "Zástupci tříd"

    @override
    def clean(self):
        super().clean()

        # Uniqueness na úrovni DB nestačí - stejnou roli ve stejné třídě nesmí mít ve
        # stejném období dva různí zástupci, i když jde o odlišné záznamy.
        if self.school_class_id and self.representant_type and self.valid_from:
            overlapping = ClassRepresentative.objects.filter(
                school_class_id=self.school_class_id, representant_type=self.representant_type,
            ).exclude(pk=self.pk)
            overlapping = overlapping.filter(
                models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=self.valid_from)
            )
            if self.valid_until is not None:
                overlapping = overlapping.filter(valid_from__lte=self.valid_until)

            if overlapping.exists():
                raise ValidationError(
                    "Pro tuto třídu a roli už existuje jiný zástupce v překrývajícím se období."
                )

    @override
    def __str__(self):
        return (
            f"{self.representative} -> {self.school_class} "
            f"({self.valid_from} - {self.valid_until or 'současnost'})"
        )


@final
class ProfileMergeRequest(models.Model):
    class RequestStatus(models.TextChoices):
        PENDING = 'PE', 'čeká na schválení'
        APPROVED = 'AP', 'schváleno'
        REJECTED = 'RE', 'zamítnuto'

    # SET_NULL (ne CASCADE): po schválení se uživatelský účet žadatele smaže
    # (jeho SocialAccount se přesune na cílový účet), ale žádost zůstává jako záznam.
    user = models.OneToOneField(
        cast(str, settings.AUTH_USER_MODEL),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='merge_request',
    )

    status = models.CharField(max_length=2, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Datum podání")

    old_email = models.EmailField(verbose_name="Stávající email")

    first_name = models.CharField(max_length=100, verbose_name="Jméno dítěte")
    last_name = models.CharField(max_length=100, verbose_name="Příjmení dítěte")

    student_by_name = models.ForeignKey(
        Student, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Přiřazený žák"
    )

    comments = models.TextField(blank=True, verbose_name="Poznámky")

    @final
    class Meta:
        verbose_name = "Žádost o sloučení účtů"
        verbose_name_plural = "Žádosti o sloučení účtů"


@final
class ProfileStudentRequest(models.Model):
    class ActionType(models.TextChoices):
        ADD = 'A', 'přidat dítě'

    class RequestStatus(models.TextChoices):
        PENDING = 'PE', 'čeká na schválení'
        APPROVED = 'AP', 'schváleno'
        REJECTED = 'RE', 'zamítnuto'

    profile = models.ForeignKey(Profile, blank=False, null=False, on_delete=models.CASCADE)
    action = models.CharField(max_length=2, choices=ActionType.choices, default=ActionType.ADD)
    status = models.CharField(max_length=2, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Datum podání")

    first_name = models.CharField(max_length=100, verbose_name="Jméno dítěte")
    last_name = models.CharField(max_length=100, verbose_name="Příjmení dítěte")
    birth_date = models.DateField(verbose_name="Datum narození dítěte")

    student_by_name = models.ForeignKey(
        Student, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Žák (ověřeno jménem a datem narození)"
    )

    comments = models.TextField(blank=True, verbose_name="Poznámky")

    @final
    class Meta:
        verbose_name = "Žádost o přidání žáka"
        verbose_name_plural = "Žádosti o přidání žáka"
