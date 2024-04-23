from django.db import models
from users.models import CustomUser

class Allegro(models.Model):
    name=models.CharField(
        max_length=125,
        null=True
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
    )

    def __str__(self):
        return self.name

class Secret(models.Model):
    CLIENT_ID = models.CharField(
        null=True,
        max_length=255,
        )
    CLIENT_SECRET = models.CharField(
        null=True,
        max_length=999,
        )
    access_token = models.CharField(
        null=True,
        max_length=2000,
        )
    refresh_token = models.CharField(
        null=True,
        max_length=2000,
        )
    account = models.ForeignKey(
        Allegro,
        on_delete=models.CASCADE
    )
    dpd_access_token = models.CharField(
        null=True,
        max_length=2000,
        )

    def __str__(self):
        return self.account.name