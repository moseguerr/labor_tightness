import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def percentage(value, total):
    """Calculate percentage: {{ value|percentage:total }}"""
    try:
        return int(float(value) / float(total) * 100)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def rank_badges(text):
    """Replace (N) in prompt text with styled circle badges."""
    def _badge(match):
        num = match.group(1)
        return (
            f'<span class="inline-flex items-center justify-center w-5 h-5 rounded-full '
            f'bg-primary-500 text-white text-xs font-bold align-middle">{num}</span>'
        )
    return mark_safe(re.sub(r'\((\d+)\)', _badge, str(text)))
