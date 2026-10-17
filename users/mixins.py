"""Миксины для проверки прав доступа."""

from django.contrib.auth.mixins import UserPassesTestMixin

# Имя группы менеджеров в системе.
MANAGER_GROUP_NAME = "Менеджер"


def is_manager(user) -> bool:
    """Проверяет, является ли пользователь менеджером или суперюзером.

    Args:
        user: объект User.

    Returns:
        True, если пользователь в группе «Менеджер» или суперюзер.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=MANAGER_GROUP_NAME).exists()


class OwnerOrManagerMixin(UserPassesTestMixin):
    """Разрешает доступ владельцу объекта или менеджеру.

    Используется в UpdateView/DeleteView/DetailView, где у объекта есть поле `owner`.
    Ожидается, что view имеет метод `get_object()`, возвращающий объект с атрибутом `.owner`.
    """

    def test_func(self):
        obj = self.get_object()
        user = self.request.user
        if not user.is_authenticated:
            return False
        return obj.owner == user or is_manager(user)


class OwnerOnlyMixin(UserPassesTestMixin):
    """Разрешает доступ ТОЛЬКО владельцу объекта (менеджер не проходит).

    Нужен для UpdateView/DeleteView, где менеджер НЕ должен редактировать чужое.
    """

    def test_func(self):
        obj = self.get_object()
        user = self.request.user
        if not user.is_authenticated:
            return False
        return obj.owner == user


class ManagerRequiredMixin(UserPassesTestMixin):
    """Разрешает доступ только менеджеру или суперюзеру.

    Для views, специфичных для менеджера (список пользователей, блокировка и т.д.).
    """

    def test_func(self):
        return is_manager(self.request.user)
