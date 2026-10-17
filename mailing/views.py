import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
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

logger = logging.getLogger("mailing")


def index(request):
    """Главная страница со статистикой (с кешированием агрегатов).

    Кеш-ключ учитывает роль пользователя:
    - manager → общий кеш (все данные)
    - user → персональный кеш (по user.id)
    - anonymous → пустые данные (не кешируем)

    Кеш живёт 5 минут.
    """
    user = request.user

    # Аноним — не кешируем, просто 0/0/0
    if not user.is_authenticated:
        context = {
            "total_mailings": 0,
            "active_mailings": 0,
            "unique_clients": 0,
            "title": "Главная страница",
        }
        return render(request, "mailing/index.html", context)

    # Ключ кеша зависит от роли: менеджер — общий, юзер — свой
    if is_manager(user):
        cache_key = "index_stats_manager"
    else:
        cache_key = f"index_stats_user_{user.id}"

    def compute_stats():
        """Тяжёлые запросы, которые надо кешировать."""
        if is_manager(user):
            base_mailings = Mailing.objects.all()
            base_clients = Client.objects.all()
        else:
            base_mailings = Mailing.objects.filter(owner=user)
            base_clients = Client.objects.filter(owner=user)

        now = timezone.now()
        return {
            "total_mailings": base_mailings.count(),
            "active_mailings": base_mailings.filter(
                status="started",
                start_time__lte=now,
                end_time__gte=now,
            ).count(),
            "unique_clients": base_clients.values("email").distinct().count(),
        }

    stats = cache.get_or_set(cache_key, compute_stats, timeout=300)

    context = {**stats, "title": "Главная страница"}
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
        """Автоматически назначаем владельцем + сбрасываем кеш."""
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        invalidate_stats_cache(self.request.user)
        return response


class ClientUpdateView(LoginRequiredMixin, OwnerOnlyMixin, UpdateView):
    """Редактирование данных клиента (только владелец)."""

    model = Client
    form_class = ClientForm
    success_url = reverse_lazy("mailing:client_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        invalidate_stats_cache(self.request.user)
        return response


class ClientDeleteView(LoginRequiredMixin, OwnerOnlyMixin, DeleteView):
    """Удаление клиента (только владелец)."""

    model = Client
    success_url = reverse_lazy("mailing:client_list")

    def form_valid(self, form):
        """Сбрасываем кеш перед удалением."""
        invalidate_stats_cache(self.request.user)
        return super().form_valid(form)


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
        response = super().form_valid(form)
        invalidate_stats_cache(self.request.user)
        return response


class MessageUpdateView(LoginRequiredMixin, OwnerOnlyMixin, UpdateView):
    """Редактирование сообщения (только владелец)."""

    model = Message
    form_class = MessageForm
    success_url = reverse_lazy("mailing:message_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        invalidate_stats_cache(self.request.user)
        return response


class MessageDeleteView(LoginRequiredMixin, OwnerOnlyMixin, DeleteView):
    """Удаление сообщения (только владелец)."""

    model = Message
    success_url = reverse_lazy("mailing:message_list")

    def form_valid(self, form):
        invalidate_stats_cache(self.request.user)
        return super().form_valid(form)


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
    """Создание новой рассылки (только для авторизованных)."""

    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def get_form_kwargs(self):
        """Передаём текущего пользователя в форму (для фильтрации)."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        invalidate_stats_cache(self.request.user)
        return response


class MailingUpdateView(LoginRequiredMixin, OwnerOnlyMixin, UpdateView):
    """Редактирование рассылки (только владелец)."""

    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def get_form_kwargs(self):
        """Передаём текущего пользователя в форму (для фильтрации)."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        invalidate_stats_cache(self.request.user)
        return response


class MailingDeleteView(LoginRequiredMixin, OwnerOnlyMixin, DeleteView):
    """Удаление рассылки (только владелец)."""

    model = Mailing
    success_url = reverse_lazy("mailing:mailing_list")

    def form_valid(self, form):
        invalidate_stats_cache(self.request.user)
        return super().form_valid(form)


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
        logger.info(f"Рассылка #{pk} запущена (пользователь: {request.user.email})")
        messages.success(request, "Рассылка успешно запущена.")
        invalidate_stats_cache(request.user, mailing.owner)
    except ValidationError as exc:
        error_text = exc.messages[0] if exc.messages else str(exc)
        logger.warning(f"Отказ в отправке рассылки #{pk}: {error_text}")
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
        logger.info(f"Пользователь {target_user.email} {action} менеджером {request.user.email}")
        messages.success(request, f"Пользователь {target_user.email} {action}.")
        return redirect("mailing:user_list")


class DisableMailingView(LoginRequiredMixin, ManagerRequiredMixin, View):
    """Отключение рассылки (только менеджер) — статус → completed."""

    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)
        mailing.status = "completed"
        mailing.save(update_fields=["status"])

        logger.info(f"Рассылка #{mailing.id} отключена менеджером {request.user.email}")
        messages.success(request, f"Рассылка #{mailing.id} отключена.")
        invalidate_stats_cache(request.user, mailing.owner)
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

        # Ключ кеша: у менеджера — общий, у юзера — свой
        if is_manager(user):
            cache_key = "statistics_manager"
        else:
            cache_key = f"statistics_user_{user.id}"

        def compute_statistics():
            """Тяжёлый расчёт статистики."""
            if is_manager(user):
                mailings = Mailing.objects.all().order_by("-id")
            else:
                mailings = Mailing.objects.filter(owner=user).order_by("-id")

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

            return {
                "stats": stats,
                "total_success": total_success,
                "total_fail": total_fail,
                "total_sent": total_success,
                "is_manager_view": is_manager(user),
            }

        cached = cache.get_or_set(cache_key, compute_statistics, timeout=300)
        context.update(cached)
        return context


# --- ИНВАЛИДАЦИЯ КЕША ---


def invalidate_stats_cache(*users):
    """Сбрасывает кеш счётчиков и статистики.

    Принимает произвольное число пользователей, чьи кеши надо сбросить.
    Всегда сбрасывает общий кеш менеджера.
    """
    for user in users:
        if user and user.is_authenticated:
            cache.delete(f"index_stats_user_{user.id}")
            cache.delete(f"statistics_user_{user.id}")

    cache.delete("index_stats_manager")
    cache.delete("statistics_manager")
