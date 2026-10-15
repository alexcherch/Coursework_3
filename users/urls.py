"""URLs приложения users."""

from django.contrib.auth import views as auth_views
from django.urls import path

from users.apps import UsersConfig
from users.views import ConfirmEmailView, EmailSentView, LoginView, LogoutView, RegisterView

app_name = UsersConfig.name

urlpatterns = [
    # Регистрация и вход
    path("register/", RegisterView.as_view(), name="register"),
    path("confirm-email/<str:token>/", ConfirmEmailView.as_view(), name="confirm_email"),
    path("email-sent/", EmailSentView.as_view(), name="email_sent"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # Восстановление пароля (встроенные views Django)
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="users/password_reset.html",
            email_template_name="users/password_reset_email.html",
            subject_template_name="users/password_reset_subject.txt",
            success_url="/users/password-reset/done/",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html",
            success_url="/users/reset/done/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]
