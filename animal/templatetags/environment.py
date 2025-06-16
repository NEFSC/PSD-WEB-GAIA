from django import template
import os

register = template.Library()

@register.simple_tag
def django_env():
    return os.environ.get('DJANGO_ENV', 'Unknown')