from django.urls import path
from mailing.apps import MailingConfig
from mailing.views import index

# Задаем имя приложения для использования object_list и reverse URL-шаблонов
app_name = MailingConfig.name

urlpatterns = [
    path('', index, name='index'),  # Главная страница: http://127.0.0
]
