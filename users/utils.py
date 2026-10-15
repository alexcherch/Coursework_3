"""Утилиты для приложения users: токены и отправка писем."""

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner

# Максимальное время жизни токена подтверждения email (в секундах).
# 86400 секунд = 24 часа.
EMAIL_CONFIRMATION_MAX_AGE = 60 * 60 * 24


def _get_signer() -> TimestampSigner:
    """Возвращает TimestampSigner на основе SECRET_KEY проекта."""
    return TimestampSigner(settings.SECRET_KEY)


def generate_email_confirmation_token(user_id: int) -> str:
    """Генерирует подписанный токен для подтверждения email.

    Args:
        user_id: ID пользователя.

    Returns:
        Строка-токен, которую можно использовать в URL.
    """
    signer = _get_signer()
    token = signer.sign(str(user_id)).decode("utf-8")
    return token


def verify_email_confirmation_token(token: str):
    """Проверяет токен и возвращает user_id.

    Args:
        token: Строка-токен из URL.

    Returns:
        user_id (int) — если токен валиден и не истёк.
        None — если токен подделан или просрочен.
    """
    signer = _get_signer()
    try:
        user_id = signer.unsign(token, max_age=EMAIL_CONFIRMATION_MAX_AGE).decode("utf-8")
        return int(user_id)
    except (BadSignature, SignatureExpired):
        return None


def send_confirmation_email(request, user) -> None:
    """Отправляет письмо со ссылкой подтверждения email.

    Args:
        request: HttpRequest — нужен для построения абсолютного URL.
        user: объект User.
    """
    token = generate_email_confirmation_token(user.pk)
    confirm_path = reverse("users:confirm_email", kwargs={"token": token})
    confirm_url = request.build_absolute_uri(confirm_path)

    subject = "Подтвердите ваш email"
    message = (
        f"Здравствуйте!\n\n"
        f"Спасибо за регистрацию в сервисе рассылок.\n"
        f"Чтобы подтвердить ваш email, перейдите по ссылке:\n\n"
        f"{confirm_url}\n\n"
        f"Ссылка действительна 24 часа.\n\n"
        f"Если вы не регистрировались — просто проигнорируйте это письмо."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
