from django.db import models
from django.conf import settings

# Константы для статусов рассылки
MAILING_STATUS_CHOICES = [
    ('created', 'Создана'),
    ('started', 'Запущена'),
    ('completed', 'Завершена'),
]

# Константы для статусов попыток
ATTEMPT_STATUS_CHOICES = [
    ('success', 'Успешно'),
    ('fail', 'Не успешно'),
]


class Client(models.Model):
    """Модель Получателя рассылки (Клиента)"""
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=150, verbose_name="Ф. И. О.")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")

    # Задел на Часть 2: привязка к пользователю, который создал клиента
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Владелец"
    )

    class Meta:
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылок"

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class Message(models.Model):
    """Модель Сообщения для рассылки"""
    title = models.CharField(max_length=255, verbose_name="Тема письма")
    body = models.TextField(verbose_name="Тело письма")

    # Задел на Часть 2
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Владелец"
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"

    def __str__(self):
        return self.title


class Mailing(models.Model):
    """Модель Рассылки"""
    start_time = models.DateTimeField(verbose_name="Дата и время первой отправки")
    end_time = models.DateTimeField(verbose_name="Дата и время окончания отправки")
    status = models.CharField(
        max_length=10,
        choices=MAILING_STATUS_CHOICES,
        default='created',
        verbose_name="Статус"
    )

    # Связи
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        verbose_name="Сообщение"
    )
    clients = models.ManyToManyField(
        Client,
        verbose_name="Получатели"
    )

    # Задел на Часть 2
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Владелец"
    )

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"

    def __str__(self):
        return f"Рассылка {self.id} (Статус: {self.get_status_display()})"


class MailingAttempt(models.Model):
    """Модель Попытки рассылки (Логи отправки)"""
    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время попытки")
    status = models.CharField(
        max_length=10,
        choices=ATTEMPT_STATUS_CHOICES,
        verbose_name="Статус"
    )
    server_response = models.TextField(blank=True, null=True, verbose_name="Ответ почтового сервера")

    # Связь с рассылкой
    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        verbose_name="Рассылка"
    )

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылок"

    def __str__(self):
        return f"Попытка {self.id} для Рассылки {self.mailing_id} ({self.get_status_display()})"
