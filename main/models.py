from datetime import date
from typing import final, override

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


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
            f"{self.school_class} ({self.year}"
            + (f" {self.variant}" if self.variant else "")
            + ")"
        )


@final
class Parent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )

    first_name = models.CharField(max_length=100, verbose_name="Jméno")
    last_name = models.CharField(max_length=100, verbose_name="Příjmení")

    phone_number = PhoneNumberField(region="CZ", blank=True, verbose_name="Telefon")
    email = models.EmailField()

    @final
    class Meta:
        verbose_name = "Zákoný zástupce"
        verbose_name_plural = "Zákonní zástupci"

    @override
    def __str__(self):
        return f"{self.first_name} {self.last_name.rsplit}"


@final
class Student(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Jméno")
    last_name = models.CharField(max_length=100, verbose_name="Příjmení")

    school_class = models.ForeignKey(
        ClassCollective,
        on_delete=models.PROTECT,
        related_name="students",
        verbose_name="Třída",
    )

    parents = models.ManyToManyField(
        Parent,
        through="ParentRelationship",
        related_name="children",
        verbose_name="Rodiče",
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
    student = models.ForeignKey(Student, on_delete=models.PROTECT)
    parent = models.ForeignKey(Parent, on_delete=models.PROTECT)

    valid_from = models.DateField(auto_now=True, verbose_name="Platnost od")
    valid_until = models.DateField(null=True, blank=True, verbose_name="Platnost do")

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
