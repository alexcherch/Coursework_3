from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from mailing.models import Mailing, Client, Message
from mailing.forms import ClientForm, MessageForm, MailingForm
from mailing.services import send_mailing


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


# --- СООБЩЕНИЯ (CRUD) ---

class MessageListView(ListView):
    """Просмотр списка всех сообщений"""
    model = Message


class MessageDetailView(DetailView):
    """Просмотр детальной информации о сообщении"""
    model = Message


class MessageCreateView(CreateView):
    """Создание нового сообщения"""
    model = Message
    form_class = MessageForm
    success_url = reverse_lazy('mailing:message_list')


class MessageUpdateView(UpdateView):
    """Редактирование сообщения"""
    model = Message
    form_class = MessageForm
    success_url = reverse_lazy('mailing:message_list')


class MessageDeleteView(DeleteView):
    """Удаление сообщения"""
    model = Message
    success_url = reverse_lazy('mailing:message_list')


# --- РАССЫЛКИ (CRUD) ---

class MailingListView(ListView):
    """Просмотр списка всех рассылок"""
    model = Mailing


class MailingDetailView(DetailView):
    """Просмотр детальной информации о рассылке"""
    model = Mailing


class MailingCreateView(CreateView):
    """Создание новой рассылки"""
    model = Mailing
    form_class = MailingForm
    success_url = reverse_lazy('mailing:mailing_list')


class MailingUpdateView(UpdateView):
    """Редактирование рассылки"""
    model = Mailing
    form_class = MailingForm
    success_url = reverse_lazy('mailing:mailing_list')


class MailingDeleteView(DeleteView):
    """Удаление рассылки"""
    model = Mailing
    success_url = reverse_lazy('mailing:mailing_list')


def toggle_mailing_send(request, pk):
    """Контроллер для ручного запуска отправки рассылки из интерфейса"""
    send_mailing(pk)
    return redirect('mailing:mailing_detail', pk=pk)
