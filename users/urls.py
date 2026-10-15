"""URLs приложения users."""

from django.urls import path

from users.apps import UsersConfig
from users.views import ConfirmEmailView, EmailSentView, LoginView, LogoutView, RegisterView

app_name = UsersConfig.name

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("confirm-email/<str:token>/", ConfirmEmailView.as_view(), name="confirm_email"),
    path("email-sent/", EmailSentView.as_view(), name="email_sent"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
