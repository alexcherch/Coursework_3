from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from mailing.models import Mailing, Client
from mailing.forms import ClientForm


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


# --- КЛИЕНТЫ (CRUD) ---

class ClientListView(ListView):
    """Просмотр списка всех клиентов"""
    model = Client
    # Шаблон по умолчанию Django ищет в: mailing/client_list.html


class ClientDetailView(DetailView):
    """Просмотр детальной информации о клиенте"""
    model = Client


class ClientCreateView(CreateView):
    """Создание нового клиента"""
    model = Client
    form_class = ClientForm
    success_url = reverse_lazy('mailing:client_list')


class ClientUpdateView(UpdateView):
    """Редактирование данных клиента"""
    model = Client
    form_class = ClientForm
    success_url = reverse_lazy('mailing:client_list')


class ClientDeleteView(DeleteView):
    """Удаление клиента"""
    model = Client
    success_url = reverse_lazy('mailing:client_list')
