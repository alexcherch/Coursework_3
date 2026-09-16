from django import forms
from mailing.models import Client


class StyleFormMixin:
    """Миксин для автоматического добавления стилей Bootstrap к полям формы"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Добавляем класс Bootstrap для всех полей ввода
            field.widget.attrs['class'] = 'form-control'


class ClientForm(StyleFormMixin, forms.ModelForm):
    """Форма для создания и редактирования клиента"""
    class Meta:
        model = Client
        fields = ('full_name', 'email', 'comment')
        # Настраиваем виджет для комментария, чтобы он не занимал пол-экрана по высоте
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }
