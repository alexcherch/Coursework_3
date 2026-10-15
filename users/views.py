"""Views приложения users."""

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

        # Отправляем письмо подтверждения
        send_confirmation_email(self.request, self.object)

        return response


class ConfirmEmailView(View):
    """Подтверждение email по токену из письма."""

    def get(self, request, token):
        user_id = verify_email_confirmation_token(token)

        if user_id is None:
            return render(request, "users/email_confirm_invalid.html", status=400)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return render(request, "users/email_confirm_invalid.html", status=404)

        # Если email уже подтверждён — показываем сообщение об успехе (не ругаемся)
        if not user.email_confirmed:
            user.email_confirmed = True
            user.save(update_fields=["email_confirmed"])

        # Автоматически логиним после подтверждения
        login(request, user)
        messages.success(request, "Email успешно подтверждён!")
        return redirect("mailing:index")


class LoginView(BaseLoginView):
    """Вход по email и паролю."""

    form_class = UserLoginForm
    template_name = "users/login.html"
    redirect_authenticated_user = True


class LogoutView(BaseLogoutView):
    """Выход из системы."""

    next_page = reverse_lazy("mailing:index")


class EmailSentView(TemplateView):
    """Страница «Проверьте почту» после регистрации."""

    template_name = "users/email_sent.html"
