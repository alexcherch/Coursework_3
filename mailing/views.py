from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from mailing.forms import ClientForm, MailingForm, MessageForm
from mailing.models import Client, Mailing, MailingAttempt, Message
from mailing.services import send_mailing
from users.mixins import ManagerRequiredMixin, OwnerOnlyMixin, OwnerOrManagerMixin, is_manager
from users.models import User


def index(request):
    """Главная страница со статистикой.

    - Аноним — видит нули.
    - Пользователь — только свои рассылки/клиентов.
    - Менеджер — статистику по всем.
    """
    user = request.user

    if not user.is_authenticated:
        # Аноним — пустая статистика
        base_mailings = Mailing.objects.none()
        base_clients = Client.objects.none()
    elif is_manager(user):
        # Менеджер — видит всё
        base_mailings = Mailing.objects.all()
        base_clients = Client.objects.all()
    else:
        # Обычный пользователь — только своё
        base_mailings = Mailing.objects.filter(owner=user)
        base_clients = Client.objects.filter(owner=user)

    # 1. Всего рассылок (по видимым)
    total_mailings = base_mailings.count()

    # 2. Активные рассылки: started + сейчас в окне
    now = timezone.now()
    active_mailings = base_mailings.filter(
        status="started",
        start_time__lte=now,
        end_time__gte=now,
    ).count()

    # 3. Уникальные получатели
    unique_clients = base_clients.values("email").distinct().count()

    context = {
        "total_mailings": total_mailings,
        "active_mailings": active_mailings,
        "unique_clients": unique_clients,
        "title": "Главная страница",
    }

    return render(request, "mailing/index.html", context)


# --- КЛИЕНТЫ (CRUD) ---


class ClientListView(LoginRequiredMixin, ListView):
    """Список клиентов: пользователь видит только своих, менеджер — всех."""

    model = Client

    def get_queryset(self):
        user = self.request.user
        if is_manager(user):
            return Client.objects.all()
        return Client.objects.filter(owner=user)


class ClientDetailView(LoginRequiredMixin, OwnerOrManagerMixin, DetailView):
    """Просмотр детальной информации о клиенте (владелец или менеджер)."""

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


class ClientUpdateView(LoginRequiredMixin, OwnerOnlyMixin, UpdateView):
    """Редактирование данных клиента (только владелец)."""

    model = Client
    form_class = ClientForm
    success_url = reverse_lazy("mailing:client_list")


class ClientDeleteView(LoginRequiredMixin, OwnerOnlyMixin, DeleteView):
    """Удаление клиента (только владелец)."""

    model = Client
    success_url = reverse_lazy("mailing:client_list")


# --- СООБЩЕНИЯ (CRUD) ---


class MessageListView(LoginRequiredMixin, ListView):
    """Список сообщений: пользователь видит только свои, менеджер — все."""

    model = Message

    def get_queryset(self):
        user = self.request.user
        if is_manager(user):
            return Message.objects.all()
        return Message.objects.filter(owner=user)


class MessageDetailView(LoginRequiredMixin, OwnerOrManagerMixin, DetailView):
    """Просмотр детальной информации о сообщении (владелец или менеджер)."""

    model = Message


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Создание нового сообщения (только для авторизованных)"""

    model = Message
    form_class = MessageForm
    success_url = reverse_lazy("mailing:message_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, OwnerOnlyMixin, UpdateView):
    """Редактирование сообщения (только владелец)."""

    model = Message
    form_class = MessageForm
    success_url = reverse_lazy("mailing:message_list")


class MessageDeleteView(LoginRequiredMixin, OwnerOnlyMixin, DeleteView):
    """Удаление сообщения (только владелец)."""

    model = Message
    success_url = reverse_lazy("mailing:message_list")


# --- РАССЫЛКИ (CRUD) ---


class MailingListView(LoginRequiredMixin, ListView):
    """Список рассылок: пользователь видит только свои, менеджер — все."""

    model = Mailing

    def get_queryset(self):
        user = self.request.user
        if is_manager(user):
            return Mailing.objects.all()
        return Mailing.objects.filter(owner=user)


class MailingDetailView(LoginRequiredMixin, OwnerOrManagerMixin, DetailView):
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


class MailingUpdateView(LoginRequiredMixin, OwnerOnlyMixin, UpdateView):
    """Редактирование рассылки (только владелец)."""

    model = Mailing
    form_class = MailingForm
    success_url = reverse_lazy("mailing:mailing_list")


class MailingDeleteView(LoginRequiredMixin, OwnerOnlyMixin, DeleteView):
    """Удаление рассылки (только владелец)."""

    model = Mailing
    success_url = reverse_lazy("mailing:mailing_list")


def toggle_mailing_send(request, pk):
    """Ручной запуск отправки рассылки из интерфейса.

    Доступ: владелец или менеджер.
    Обрабатывает ValidationError от сервиса и показывает сообщение пользователю.
    """
    # Аноним → на логин
    if not request.user.is_authenticated:
        return redirect(f"{reverse('users:login')}?next={request.path}")

    mailing = get_object_or_404(Mailing, pk=pk)

    # Проверка прав: владелец или менеджер
    if mailing.owner != request.user and not is_manager(request.user):
        raise PermissionDenied("У вас нет прав на отправку этой рассылки.")

    try:
        send_mailing(pk)
        messages.success(request, "Рассылка успешно запущена.")
    except ValidationError as exc:
        error_text = exc.messages[0] if exc.messages else str(exc)
        messages.error(request, error_text)

    return redirect("mailing:mailing_detail", pk=pk)


# --- ДЕЙСТВИЯ МЕНЕДЖЕРА ---


class UserListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    """Список всех пользователей сервиса (только менеджер)."""

    model = User
    template_name = "mailing/user_list.html"
    context_object_name = "users"
    ordering = ("-date_joined",)


class ToggleUserActiveView(LoginRequiredMixin, ManagerRequiredMixin, View):
    """Блокировка/разблокировка пользователя (только менеджер).

    Менеджер не может блокировать суперюзера или самого себя.
    """

    def post(self, request, pk):
        target_user = get_object_or_404(User, pk=pk)

        # Защита: не блокировать суперюзера и самого себя
        if target_user.is_superuser:
            messages.error(request, "Нельзя блокировать суперпользователя.")
            return redirect("mailing:user_list")

        if target_user == request.user:
            messages.error(request, "Нельзя заблокировать самого себя.")
            return redirect("mailing:user_list")

        target_user.is_active = not target_user.is_active
        target_user.save(update_fields=["is_active"])

        action = "разблокирован" if target_user.is_active else "заблокирован"
        messages.success(request, f"Пользователь {target_user.email} {action}.")
        return redirect("mailing:user_list")


class DisableMailingView(LoginRequiredMixin, ManagerRequiredMixin, View):
    """Отключение рассылки (только менеджер) — статус → completed."""

    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)
        mailing.status = "completed"
        mailing.save(update_fields=["status"])

        messages.success(request, f"Рассылка #{mailing.id} отключена.")
        return redirect("mailing:mailing_detail", pk=mailing.pk)


# --- СТАТИСТИКА ---


class StatisticsView(LoginRequiredMixin, TemplateView):
    """Страница статистики по попыткам рассылок.

    - Пользователь: только по своим рассылкам.
    - Менеджер: по всем рассылкам.
    """

    template_name = "mailing/statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # База рассылок для статистики
        if is_manager(user):
            mailings = Mailing.objects.all().order_by("-id")
        else:
            mailings = Mailing.objects.filter(owner=user).order_by("-id")

        # Собираем статистику по каждой рассылке
        stats = []
        total_success = 0
        total_fail = 0

        for mailing in mailings:
            attempts = MailingAttempt.objects.filter(mailing=mailing)
            success = attempts.filter(status="success").count()
            fail = attempts.filter(status="fail").count()

            total_success += success
            total_fail += fail

            stats.append(
                {
                    "mailing": mailing,
                    "success": success,
                    "fail": fail,
                    "total": success + fail,
                }
            )

        context["stats"] = stats
        context["total_success"] = total_success
        context["total_fail"] = total_fail
        context["total_sent"] = total_success  # каждое успешное = отправленное письмо
        context["is_manager_view"] = is_manager(user)

        return context
