from django import template
import os

register = template.Library()

@register.simple_tag
def DJANGO_ENV():
    """
    Returns the current Django environment, e.g., 'development', 'production', etc.
    """
    return os.environ.get('djangoenv', 'Unknown')