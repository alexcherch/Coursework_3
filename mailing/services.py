from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone

from mailing.models import Mailing, MailingAttempt


def send_mailing(mailing_id):
    """Отправляет рассылку по её ID.

    Логика:
        1. Получаем рассылку из БД. Если не найдена — ValidationError.
        2. Проверяем, разрешена ли отправка по времени:
           - now < start_time → рано, ошибка
           - now > end_time → поздно, ошибка, статус 'completed'
           - start_time <= now <= end_time → разрешено
        3. Обновляем статус на актуальный.
        4. Для каждого получателя отправляем письмо.
        5. Все попытки (успех/ошибка) собираем в список и создаём
           одним запросом через bulk_create.
    """
    try:
        mailing = Mailing.objects.get(pk=mailing_id)
    except Mailing.DoesNotExist:
        raise ValidationError(f"Рассылка с id={mailing_id} не найдена.")

    now = timezone.now()

    # Проверка времени отправки
    if now < mailing.start_time:
        raise ValidationError(f"Рассылка ещё не активна. Начало: {mailing.start_time:%d.%m.%Y %H:%M}.")
    if now > mailing.end_time:
        # Автоматически помечаем как завершённую
        mailing.status = "completed"
        mailing.save(update_fields=["status"])
        raise ValidationError(f"Рассылка уже завершена. Окончание: {mailing.end_time:%d.%m.%Y %H:%M}.")

    # Обновляем статус динамически
    mailing.update_status()

    message = mailing.message
    recipients = mailing.recipients.all()

    attempts_to_create = []

    for recipient in recipients:
        try:
            send_mail(
                subject=message.title,
                message=message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            attempts_to_create.append(
                MailingAttempt(
                    status="success",
                    server_response="Письмо успешно отправлено.",
                    mailing=mailing,
                )
            )
        except Exception as exc:
            attempts_to_create.append(
                MailingAttempt(
                    status="fail",
                    server_response=str(exc),
                    mailing=mailing,
                )
            )

    # Batch-создание всех попыток одним запросом
    if attempts_to_create:
        MailingAttempt.objects.bulk_create(attempts_to_create)
