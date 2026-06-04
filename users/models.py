from typing import final, override

from django.contrib.auth.models import AbstractUser
from django.db import models
from main.models import Profile


@final
class MyUser(AbstractUser):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    # Řekneme Djangu, že hlavním přihlašovacím údajem je email
    #USERNAME_FIELD = 'email'
    #REQUIRED_FIELDS = []

    @override
    def __str__(self):
        return self.email
