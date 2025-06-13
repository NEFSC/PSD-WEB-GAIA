import os

def environment(request):
    return {
        'DJANGO_ENV': os.environ.get('DJANGO_ENV', 'unknown')
    }