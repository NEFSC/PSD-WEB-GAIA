from django import template
import os

register = template.Library()

@register.simple_tag
def build_date():
    return os.environ.get('BUILD_DATE', 'Unknown')