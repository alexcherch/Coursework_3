from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from mailing.models import Mailing, MailingAttempt


def send_mailing(mailing_id):
    """Функция отправки писем для конкретной рассылки и записи логов"""
    # Получаем рассылку из базы данных
    try:
        mailing = Mailing.objects.get(id=mailing_id)
    except Mailing.DoesNotExist:
        return

    # Получаем сообщение и список клиентов, привязанных к этой рассылке
    message = mailing.message
    clients = mailing.clients.all()

    # Обновляем статус рассылки на 'Запущена', если она была 'Создана'
    if mailing.status == 'created':
        mailing.status = 'started'
        mailing.save()

    # Перебираем каждого клиента и отправляем ему индивидуальное письмо
    for client in clients:
        try:
            # Отправка через встроенную функцию Django
            send_mail(
                subject=message.title,
                message=message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[client.email],
                fail_silently=False,  # Выбрасывать исключение в случае ошибки
            )

            # Если улетело без ошибок — пишем успешный лог
            MailingAttempt.objects.create(
                status='success',
                server_response='Письмо успешно отправлено.',
                mailing=mailing
            )

        except Exception as e:
            # Если сервер вернул ошибку или нет сети — пишем неуспешный лог с текстом ошибки
            MailingAttempt.objects.create(
                status='fail',
                server_response=str(e),
                mailing=mailing
            )
