from django.contrib import admin
from mailing.models import Client, Message, Mailing, MailingAttempt


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    # Поля, которые будут отображаться в списке клиентов
    list_display = ('id', 'full_name', 'email', 'owner')
    # Поля, по которым можно искать клиентов
    search_fields = ('full_name', 'email')
    # Фильтр справа
    list_filter = ('owner',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner')
    search_fields = ('title', 'body')


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_time', 'end_time', 'status', 'message', 'owner')
    list_filter = ('status', 'start_time', 'end_time')
    # Позволяет удобно выбирать много клиентов через горизонтальный фильтр
    filter_horizontal = ('clients',)


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'attempt_time', 'status', 'mailing')
    list_filter = ('status', 'attempt_time')
    # Запрещаем редактировать логи вручную из админки, они должны быть только для чтения
    readonly_fields = ('attempt_time', 'status', 'server_response', 'mailing')
