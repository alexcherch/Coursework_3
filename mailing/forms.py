from django import forms

from mailing.models import Client, Mailing, Message


class StyleFormMixin:
    """Миксин для автоматического добавления стилей Bootstrap к полям формы"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Добавляем класс Bootstrap для всех полей ввода
            field.widget.attrs["class"] = "form-control"


class ClientForm(StyleFormMixin, forms.ModelForm):
    """Форма для создания и редактирования клиента"""

    class Meta:
        model = Client
        fields = ("full_name", "email", "comment")
        # Настраиваем виджет для комментария, чтобы он не занимал пол-экрана по высоте
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4}),
        }


class MessageForm(StyleFormMixin, forms.ModelForm):
    """Форма для создания и редактирования сообщения"""

    class Meta:
        model = Message
        fields = ("title", "body")
        widgets = {
            "body": forms.Textarea(attrs={"rows": 5}),  # Делаем поле текста письма удобного размера
        }


class MailingForm(StyleFormMixin, forms.ModelForm):
    """Форма для создания и редактирования рассылки."""

    class Meta:
        model = Mailing
        fields = ("start_time", "end_time", "message", "recipients")
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "recipients": forms.SelectMultiple(attrs={"style": "height: 150px;"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        """Фильтруем клиентов и сообщения по владельцу (кроме менеджера)."""
        super().__init__(*args, **kwargs)
        self.user = user

        if user and not user.is_superuser and not user.groups.filter(name="Менеджер").exists():
            self.fields["recipients"].queryset = Client.objects.filter(owner=user)
            self.fields["message"].queryset = Message.objects.filter(owner=user)

    def clean_recipients(self):
        """Проверяем, что все получатели принадлежат текущему пользователю."""
        recipients = self.cleaned_data.get("recipients")

        if not recipients:
            return recipients

        user = self.user
        if not user or user.is_superuser or user.groups.filter(name="Менеджер").exists():
            return recipients

        for recipient in recipients:
            if recipient.owner != user:
                raise forms.ValidationError(f"Клиент '{recipient.full_name}' вам не принадлежит.")

        return recipients
