from django import template

register = template.Library()


@register.filter
def percentage(value, total):
    """Calculate percentage: {{ value|percentage:total }}"""
    try:
        return int(float(value) / float(total) * 100)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
