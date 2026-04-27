from datetime import date
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django import utils
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField


class ClassCollective(models.Model):
    class SchoolClassType(models.IntegerChoices):
        R1 = 1, "1. ročník"
        R2 = 2, "2. ročník"
        R3 = 3, "3. ročník"

    school_class = models.IntegerField(
        choices=SchoolClassType.choices, null=True, blank=True
    )

    year = models.PositiveIntegerField(
        verbose_name="Školní rok (nástupu)",
        default=date.today().year,
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
    )
    variant = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["year", "variant"], name="unique_class_collective_name"
            )
        ]

    def __str__(self):
        return (
            f"{self.school_class} ({self.year}"
            + (f" {self.variant}" if self.variant else "")
            + ")"
        )


class Parent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    first_name = models.CharField(max_length=100, verbose_name="Jméno")
    last_name = models.CharField(max_length=100, verbose_name="Příjmení")

    phone_number = PhoneNumberField(region="CZ", blank=True, verbose_name="Telefon")
    email = models.EmailField()

    class Meta:
        verbose_name = "Zákoný zástupce"
        verbose_name_plural = "Zákonní zástupci"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Student(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Jméno")
    last_name = models.CharField(max_length=100, verbose_name="Příjmení")

    school_class = models.ManyToManyField(
        ClassCollective,
        through="CollectiveRelationship",
        related_name="students",
        verbose_name="Třída",
    )

    parents = models.ManyToManyField(
        Parent,
        through="FamilyRelationship",
        related_name="children",
        verbose_name="Rodiče",
    )

    class Meta:
        verbose_name = "Žák"
        verbose_name_plural = "Žáci"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class FamilyRelationship(models.Model):
    student = models.ForeignKey(Student, on_delete=models.PROTECT)
    parent = models.ForeignKey(Parent, on_delete=models.PROTECT)

    valid_from = models.DateField(auto_now=True, verbose_name="Platnost od")
    valid_until = models.DateField(null=True, blank=True, verbose_name="Platnost do")

    class Meta:
        # Zabráníme duplicitnímu vztahu mezi stejným rodičem a dítětem
        constraints = [
            models.UniqueConstraint(
                fields=["student", "parent"], name="student_parent_unique"
            )
        ]

    def __str__(self):
        return f"{self.parent} -> {self.student} ({self.valid_from} - {self.valid_until or 'současnost'})"


class CollectiveRelationship(models.Model):
    student = models.ForeignKey(Student, on_delete=models.PROTECT)
    school_class = models.ForeignKey(ClassCollective, on_delete=models.PROTECT)

    # Naše vlastní atributy (časový interval)
    valid_from = models.DateField(
        null=True, blank=True, auto_now=True, verbose_name="Platnost od"
    )
    valid_until = models.DateField(null=True, blank=True, verbose_name="Platnost do")

    class Meta:
        # Zabráníme duplicitnímu vztahu mezi stejným rodičem a dítětem
        constraints = [
            models.UniqueConstraint(
                fields=["student", "school_class"],
                name="student_trida_unique_relationship",
            )
        ]

    def __str__(self):
        return f"{self.student} -> {self.school_class} ({self.valid_from} - {self.valid_until or 'současnost'})"


class PaymentRule(models.Model):
    class PaymentRuleType(models.IntegerChoices):
        JEDINACEK = 1, "jedno dítě"
        SOUROZENEC = 2, "sourozenec"
        SOUROZENEC2 = 3, "druhý sourozenec"

    name = models.CharField(max_length=100, unique=True, verbose_name="Pravidlo")
    variant = models.IntegerField(
        choices=PaymentRuleType.choices, null=True, blank=True
    )

    valid_from = models.DateField(
        null=True, blank=True, auto_now=True, verbose_name="Platnost od"
    )
    valid_until = models.DateField(null=True, blank=True, verbose_name="Platnost do")
