from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext as _

from .manager import CustomUserManager

class CustomUser(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(
        null=True,
        max_length=125,
        )
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
        max_length=999,
        )
    refresh_token = models.CharField(
        null=True,
        max_length=999,
        )
    next_access_token = models.CharField(
        null=True,
        max_length=999,
        )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username',)

    objects = CustomUserManager()

    def __str__(self):
        return self.email