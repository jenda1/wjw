from datetime import date
from typing import final, override

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

import hashlib
import re


def hash_rodne_cislo(rc_text: str | None):
    if not rc_text:
        return None

    ciste_rc = re.sub(r'[^0-9]', '', str(rc_text))
    soleny_vstup = f"{ciste_rc}{settings.SECRET_KEY}"

    return hashlib.sha256(soleny_vstup.encode('utf-8')).hexdigest()


def validate_rodne_cislo_format(value: str):
    match = re.match(r'^(\d{6})\/?(\d{3,4})$', value)
    if not match:
        raise ValidationError('Rodné číslo nemá správný formát.')
    cislo_text = match.group(1) + match.group(2)
    if len(cislo_text) == 10 and int(cislo_text) % 11 != 0:
        if not (int(cislo_text[:-1]) % 11 == 10 and cislo_text[-1] == '0'):
            raise ValidationError('Rodné číslo není platné.')


def validuj_datum_narozeni(value):
    """Bariéra, která nepustí datum z budoucnosti a příliš staré lidi."""
    if value > date.today():
        raise ValidationError("Datum narození nemůže být v budoucnosti.")
    if value.year < 1900:
        raise ValidationError("Neplatné datum narození (příliš hluboko v minulosti).")


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

    @final
    class Meta:
        verbose_name = "Třídna"
        verbose_name_plural = "Třídy"
        constraints = [
            models.UniqueConstraint(
                fields=["year", "variant"], name="unique_class_collective_name"
            )
        ]

    @override
    def __str__(self):
        return (
            f"{self.school_class}{self.variant if self.variant else ""} ({self.year})"
        )



@final
class Profile(models.Model):
    first_name = models.CharField(max_length=100, blank=False, verbose_name="Jméno")
    last_name = models.CharField(max_length=100, blank=False, verbose_name="Příjmení")

    date_of_birth = models.DateField(blank=True, validators=[validuj_datum_narozeni], verbose_name="Datum narození")
    rc_hash = models.CharField(
        max_length=64,
        editable=False,
        verbose_name="Otisk rodného čísla"
    )

    phone_number = PhoneNumberField(region="CZ", blank=True, verbose_name="Telefon")
    email = models.EmailField()

    @property
    def vek(self):
        """Pomocná vlastnost (property), která automaticky spočítá aktuální věk."""
        if not self.date_of_birth:
            return None

        dnes = date.today()
        return dnes.year - self.date_of_birth.year - (
            (dnes.month, dnes.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


    @final
    class Meta:
        verbose_name = "Člen spolku"
        verbose_name_plural = "Členové spolku"

    @override
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


@final
class Student(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Jméno")
    last_name = models.CharField(max_length=100, verbose_name="Příjmení")

    rc_hash = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        verbose_name="Otisk rodného čísla"
    )

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

    @final
    class Meta:
        verbose_name = "Žák"
        verbose_name_plural = "Žáci"

    @override
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


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

    @override
    def __str__(self):
        return f"{self.parent} -> {self.student} ({self.valid_from} - {self.valid_until or 'současnost'})"
