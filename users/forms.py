"""Формы приложения users."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from users.models import User


class UserRegisterForm(UserCreationForm):
    """Форма регистрации: email + пароль и подтверждение."""

    email = forms.EmailField(
        label="Электронная почта",
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control py-2"}),
    )

    class Meta:
        model = User
        fields = ("email", "avatar", "phone", "country")
        widgets = {
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control py-2"}),
            "phone": forms.TextInput(attrs={"class": "form-control py-2"}),
            "country": forms.TextInput(attrs={"class": "form-control py-2"}),
        }
        labels = {
            "avatar": "Аватар",
            "phone": "Номер телефона",
            "country": "Страна",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ("password1", "password2"):
            if field_name in self.fields:
                self.fields[field_name].widget.attrs["class"] = "form-control py-2"
        self.fields["password1"].label = "Пароль"
        self.fields["password2"].label = "Подтверждение пароля"

    def clean_email(self):
        """Проверяем, что email ещё не занят."""
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email


class UserLoginForm(AuthenticationForm):
    """Форма входа по email и паролю."""

    username = forms.EmailField(
        label="Электронная почта",
        widget=forms.EmailInput(attrs={"class": "form-control py-2", "autofocus": True}),
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control py-2"}),
    )
