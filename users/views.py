"""Views приложения users."""

import logging

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import LogoutView as BaseLogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView

from users.forms import UserLoginForm, UserRegisterForm
from users.models import User
from users.utils import send_confirmation_email, verify_email_confirmation_token

logger = logging.getLogger("users")


class RegisterView(CreateView):
    """Регистрация нового пользователя.

    После успешного создания:
        - username заполняется email'ом;
        - отправляется письмо с ссылкой подтверждения;
        - редирект на страницу «проверьте почту».
    """

    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:email_sent")

    def form_valid(self, form):
        # username = email (в форме username нет)
        form.instance.username = form.cleaned_data["email"]
        response = super().form_valid(form)

        # Логируем регистрацию
        logger.info(f"Регистрация нового пользователя: {self.object.email}")

        # Отправляем письмо подтверждения
        send_confirmation_email(self.request, self.object)

        return response


class ConfirmEmailView(View):
    """Подтверждение email по токену из письма."""

    def get(self, request, token):
        user_id = verify_email_confirmation_token(token)

        if user_id is None:
            logger.warning("Попытка подтверждения email с невалидным токеном")
            return render(request, "users/email_confirm_invalid.html", status=400)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            logger.warning(f"Подтверждение email: пользователь id={user_id} не найден")
            return render(request, "users/email_confirm_invalid.html", status=404)

        if not user.email_confirmed:
            user.email_confirmed = True
            user.save(update_fields=["email_confirmed"])
            logger.info(f"Email подтверждён: {user.email}")

        login(request, user)
        messages.success(request, "Email успешно подтверждён!")
        return redirect("mailing:index")


class LoginView(BaseLoginView):
    """Вход по email и паролю."""

    form_class = UserLoginForm
    template_name = "users/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        logger.info(f"Успешный вход: {form.get_user().email}")
        return super().form_valid(form)

    def form_invalid(self, form):
        email = form.cleaned_data.get("username", "unknown")
        logger.warning(f"Неудачная попытка входа: {email}")
        return super().form_invalid(form)


class LogoutView(BaseLogoutView):
    """Выход из системы."""

    next_page = reverse_lazy("mailing:index")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logger.info(f"Выход: {request.user.email}")
        return super().dispatch(request, *args, **kwargs)


class EmailSentView(TemplateView):
    """Страница «Проверьте почту» после регистрации."""

    template_name = "users/email_sent.html"
