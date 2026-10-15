from django.urls import path

from mailing.apps import MailingConfig
from mailing.views import (
    ClientCreateView,
    ClientDeleteView,
    ClientDetailView,
    ClientListView,
    ClientUpdateView,
    DisableMailingView,
    MailingCreateView,
    MailingDeleteView,
    MailingDetailView,
    MailingListView,
    MailingUpdateView,
    MessageCreateView,
    MessageDeleteView,
    MessageDetailView,
    MessageListView,
    MessageUpdateView,
    ToggleUserActiveView,
    UserListView,
    index,
    toggle_mailing_send,
)

app_name = MailingConfig.name

urlpatterns = [
    # Главная страница
    path("", index, name="index"),
    # Маршруты для CRUD Клиентов
    path("clients/", ClientListView.as_view(), name="client_list"),
    path("clients/<int:pk>/", ClientDetailView.as_view(), name="client_detail"),
    path("clients/create/", ClientCreateView.as_view(), name="client_create"),
    path("clients/<int:pk>/update/", ClientUpdateView.as_view(), name="client_update"),
    path("clients/<int:pk>/delete/", ClientDeleteView.as_view(), name="client_delete"),
    # Маршруты для CRUD Сообщений
    path("messages/", MessageListView.as_view(), name="message_list"),
    path("messages/<int:pk>/", MessageDetailView.as_view(), name="message_detail"),
    path("messages/create/", MessageCreateView.as_view(), name="message_create"),
    path("messages/<int:pk>/update/", MessageUpdateView.as_view(), name="message_update"),
    path("messages/<int:pk>/delete/", MessageDeleteView.as_view(), name="message_delete"),
    # Маршруты для CRUD Рассылок
    path("mailings/", MailingListView.as_view(), name="mailing_list"),
    path("mailings/<int:pk>/", MailingDetailView.as_view(), name="mailing_detail"),
    path("mailings/create/", MailingCreateView.as_view(), name="mailing_create"),
    path("mailings/<int:pk>/update/", MailingUpdateView.as_view(), name="mailing_update"),
    path("mailings/<int:pk>/delete/", MailingDeleteView.as_view(), name="mailing_delete"),
    # Маршрут для ручного запуска отправки рассылки
    path("mailings/<int:pk>/send/", toggle_mailing_send, name="mailing_toggle_send"),
    # Действия менеджера
    path("manage/users/", UserListView.as_view(), name="user_list"),
    path("manage/users/<int:pk>/toggle-active/", ToggleUserActiveView.as_view(), name="user_toggle_active"),
    path("mailings/<int:pk>/disable/", DisableMailingView.as_view(), name="mailing_disable"),
]
