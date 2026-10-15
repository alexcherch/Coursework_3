from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Кастомная модель пользователя с авторизацией по email."""

    email = models.EmailField(
        "Электронная почта",
        unique=True,
    )
    avatar = models.ImageField(
        "Аватар",
        upload_to="avatars/",
        blank=True,
        null=True,
    )
    phone = models.CharField(
        "Номер телефона",
        max_length=20,
        blank=True,
    )
    country = models.CharField(
        "Страна",
        max_length=100,
        blank=True,
    )
    email_confirmed = models.BooleanField(
        "Email подтверждён",
        default=False,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email
