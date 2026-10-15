from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from mailing.forms import ClientForm, MailingForm, MessageForm
from mailing.models import Client, Mailing, Message
from mailing.services import send_mailing


def index(request):
    """Контроллер главной страницы со статистикой"""
    # 1. Всего рассылок
    total_mailings = Mailing.objects.count()

    # 2. Количество активных рассылок:
    #    - статус 'started' (Запущена)
    #    - текущее время между start_time и end_time
    now = timezone.now()
    active_mailings = Mailing.objects.filter(
        status="started",
        start_time__lte=now,
        end_time__gte=now,
    ).count()

    # 3. Количество уникальных получателей
    # .distinct() гарантирует, что email-адреса не будут дублироваться в подсчете
    unique_clients = Client.objects.values("email").distinct().count()

    context = {
        "total_mailings": total_mailings,
        "active_mailings": active_mailings,
        "unique_clients": unique_clients,
        "title": "Главная страница",
    }

    return render(request, "mailing/index.html", context)


# --- КЛИЕНТЫ (CRUD) ---


class ClientListView(ListView):
    """Просмотр списка всех клиентов"""

    model = Client
    # Шаблон по умолчанию Django ищет в: mailing/client_list.html


class ClientDetailView(DetailView):
    """Просмотр детальной информации о клиенте"""

    model = Client


class ClientCreateView(LoginRequiredMixin, CreateView):
    """Создание нового клиента (только для авторизованных)"""

    model = Client
    form_class = ClientForm
    success_url = reverse_lazy("mailing:client_list")

    def form_valid(self, form):
        """Автоматически назначаем владельцем текущего пользователя."""
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ClientUpdateView(UpdateView):
    """Редактирование данных клиента"""

    model = Client
    form_class = ClientForm
    success_url = reverse_lazy("mailing:client_list")


class ClientDeleteView(DeleteView):
    """Удаление клиента"""

    model = Client
    success_url = reverse_lazy("mailing:client_list")


# --- СООБЩЕНИЯ (CRUD) ---


class MessageListView(ListView):
    """Просмотр списка всех сообщений"""

    model = Message


class MessageDetailView(DetailView):
    """Просмотр детальной информации о сообщении"""

    model = Message


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Создание нового сообщения (только для авторизованных)"""

    model = Message
    form_class = MessageForm
    success_url = reverse_lazy("mailing:message_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(UpdateView):
    """Редактирование сообщения"""

    model = Message
    form_class = MessageForm
    success_url = reverse_lazy("mailing:message_list")


class MessageDeleteView(DeleteView):
    """Удаление сообщения"""

    model = Message
    success_url = reverse_lazy("mailing:message_list")


# --- РАССЫЛКИ (CRUD) ---


class MailingListView(ListView):
    """Просмотр списка всех рассылок"""

    model = Mailing


class MailingDetailView(DetailView):
    """Просмотр детальной информации о рассылке (с автообновлением статуса)."""

    model = Mailing

    def get_object(self, queryset=None):
        """Перед отображением пересчитываем статус рассылки по времени."""
        obj = super().get_object(queryset)
        obj.update_status()
        return obj


class MailingCreateView(LoginRequiredMixin, CreateView):
    """Создание новой рассылки (только для авторизованных)"""

    model = Mailing
    form_class = MailingForm
    success_url = reverse_lazy("mailing:mailing_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MailingUpdateView(UpdateView):
    """Редактирование рассылки"""

    model = Mailing
    form_class = MailingForm
    success_url = reverse_lazy("mailing:mailing_list")


class MailingDeleteView(DeleteView):
    """Удаление рассылки"""

    model = Mailing
    success_url = reverse_lazy("mailing:mailing_list")


def toggle_mailing_send(request, pk):
    """Ручной запуск отправки рассылки из интерфейса.

    Обрабатывает ValidationError от сервиса и показывает сообщение пользователю.
    """
    try:
        send_mailing(pk)
        messages.success(request, "Рассылка успешно запущена.")
    except ValidationError as exc:
        # exc.message может быть как строкой, так и списком
        error_text = exc.messages[0] if exc.messages else str(exc)
        messages.error(request, error_text)

    return redirect("mailing:mailing_detail", pk=pk)
