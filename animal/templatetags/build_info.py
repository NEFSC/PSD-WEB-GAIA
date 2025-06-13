from django import template
import os

register = template.Library()

@register.simple_tag
def build_date():
    # You could read from a file, environment variable, or hardcode
    return os.environ.get('BUILD_DATE', 'Unknown')