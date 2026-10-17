"""Management-команда для создания групп пользователей."""

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from users.mixins import MANAGER_GROUP_NAME


class Command(BaseCommand):
    """Создаёт группы пользователей с нужными правами.

    Использование:
        python manage.py create_groups
    """

    help = "Создаёт группу 'Менеджер' для сервиса рассылок"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Создание групп..."))

        manager_group, created = Group.objects.get_or_create(name=MANAGER_GROUP_NAME)

        if created:
            self.stdout.write(self.style.SUCCESS(f"  [+] Создана группа '{MANAGER_GROUP_NAME}'"))
        else:
            self.stdout.write(f"  [=] Группа '{MANAGER_GROUP_NAME}' уже существует")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Готово!"))
