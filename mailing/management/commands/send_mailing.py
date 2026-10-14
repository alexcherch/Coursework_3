from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from mailing.models import Mailing
from mailing.services import send_mailing


class Command(BaseCommand):
    """Отправляет рассылку(и) через командную строку.

    Использование:
        # Отправить конкретную рассылку по id
        python manage.py send_mailing --id 5

        # Отправить все рассылки, которые сейчас можно отправить
        python manage.py send_mailing --all
    """

    help = "Отправляет рассылку по id или все активные рассылки"

    def add_arguments(self, parser):
        parser.add_argument(
            "--id",
            type=int,
            help="ID рассылки для отправки",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Отправить все рассылки, попадающие в окно времени",
        )

    def handle(self, *args, **options):
        mailing_id = options.get("id")
        send_all = options.get("all")

        # Если не указан ни --id, ни --all — сообщаем об ошибке
        if not mailing_id and not send_all:
            raise CommandError("Укажите --id <номер> или --all.")

        # Список id рассылок для отправки
        if mailing_id:
            mailing_ids = [mailing_id]
        else:
            mailing_ids = list(Mailing.objects.values_list("id", flat=True))

        sent_count = 0
        error_count = 0

        for mid in mailing_ids:
            try:
                send_mailing(mid)
                self.stdout.write(self.style.SUCCESS(f"Рассылка #{mid}: отправлена"))
                sent_count += 1
            except ValidationError as exc:
                error_text = exc.messages[0] if exc.messages else str(exc)
                self.stdout.write(self.style.WARNING(f"Рассылка #{mid}: {error_text}"))
                error_count += 1

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING(f"Итог: отправлено {sent_count}, пропущено {error_count}"))
