# main/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Получить значение из словаря по ключу"""
    return dictionary.get(key, {})

@register.filter
def divisibleby(value, arg):
    """Деление значения на аргумент"""
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Умножение значения на аргумент"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0