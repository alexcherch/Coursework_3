"""Management-команда для запуска планировщика задач.

Скрипт запускается отдельным процессом:
    python manage.py runapscheduler

"""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.utils import timezone
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution

from mailing.models import Mailing
from mailing.services import send_mailing

logger = logging.getLogger(__name__)


def send_scheduled_mailings():
    """Проверяет активные рассылки и отправляет те, что ещё НЕ отправлялись.

    Логика:
        - Берём все рассылки, попадающие в окно [start_time, end_time]
        - Исключаем те, у которых уже есть успешные попытки (уже отправлялись)
        - Исключаем завершённые
        - Для оставшихся вызываем send_mailing
    """
    now = timezone.now()

    # Активные (в окне) и не завершённые
    active_mailings = Mailing.objects.filter(
        start_time__lte=now,
        end_time__gte=now,
    ).exclude(status="completed")

    if not active_mailings.exists():
        logger.info("Планировщик: нет активных рассылок.")
        return

    # Исключаем те, где уже есть хотя бы одна успешная попытка
    mailings_to_send = []
    for mailing in active_mailings:
        has_successful_attempt = mailing.mailingattempt_set.filter(status="success").exists()
        if not has_successful_attempt:
            mailings_to_send.append(mailing)
        else:
            logger.debug(f"Планировщик: рассылка #{mailing.id} уже отправлена ранее — пропускаем.")

    if not mailings_to_send:
        logger.info("Планировщик: все активные рассылки уже были отправлены.")
        return

    for mailing in mailings_to_send:
        try:
            send_mailing(mailing.id)
            logger.info(f"Планировщик: рассылка #{mailing.id} отправлена автоматически.")
        except ValidationError as exc:
            error_text = exc.messages[0] if exc.messages else str(exc)
            logger.warning(f"Планировщик: рассылка #{mailing.id} пропущена: {error_text}")
        except Exception as exc:
            logger.error(f"Планировщик: ошибка отправки рассылки #{mailing.id}: {exc}")


def delete_old_job_executions(max_age=604_800):
    """Удаляет старые записи о выполненных задачах (старше 7 дней).

    По умолчанию 604800 секунд = 7 дней.
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    """Запускает планировщик задач для автоматической отправки рассылок."""

    help = "Запускает APScheduler для автоматической отправки рассылок"

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            send_scheduled_mailings,
            trigger=CronTrigger(second="*/30"),
            id="send_scheduled_mailings",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Добавлена задача 'send_scheduled_mailings' (каждые 30 секунд).")

        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(day_of_week="mon", hour="00", minute="00"),
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Добавлена задача 'delete_old_job_executions' (по понедельникам в 00:00).")

        try:
            logger.info("Планировщик запущен. Ctrl+C для остановки.")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Планировщик остановлен.")
            scheduler.shutdown()
