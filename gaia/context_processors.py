import os

def environment(request):
    return {
        'DJANGO_ENV': os.environ.get('DJANGO_ENV', 'Unknown')
    }

def build_date(request):
    return {'BUILD_DATE': os.environ.get('BUILD_DATE', 'Unknown')}