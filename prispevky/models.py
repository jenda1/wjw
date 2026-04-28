from typing import final
from django.db import models

@final
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
