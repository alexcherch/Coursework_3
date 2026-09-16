from django.shortcuts import render
from mailing.models import Mailing, Client


def index(request):
    """Контроллер главной страницы со статистикой"""
    # 1. Всего рассылок
    total_mailings = Mailing.objects.count()

    # 2. Количество активных рассылок (статус 'Запущена')
    # Используем 'started', так как именно это значение мы указали в choices модели
    active_mailings = Mailing.objects.filter(status='started').count()

    # 3. Количество уникальных получателей
    # .distinct() гарантирует, что email-адреса не будут дублироваться в подсчете
    unique_clients = Client.objects.values('email').distinct().count()

    context = {
        'total_mailings': total_mailings,
        'active_mailings': active_mailings,
        'unique_clients': unique_clients,
        'title': 'Главная страница'
    }

    return render(request, 'mailing/index.html', context)
