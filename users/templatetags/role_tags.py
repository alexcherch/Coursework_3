"""Template-теги для проверки ролей."""

from django import template

from users.mixins import is_manager

register = template.Library()


@register.filter(name="is_manager")
def is_manager_filter(user):
    """Фильтр для шаблонов: {{ user|is_manager }}."""
    return is_manager(user)
