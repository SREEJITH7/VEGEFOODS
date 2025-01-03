from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    return value - arg

@register.filter
def multiply(value, arg):
    return value * arg

@register.filter
def divide(value, arg):
    return value / arg if arg != 0 else 0