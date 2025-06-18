import os

# Add a context processor function
def build_date(request):
    return {'BUILD_DATE': os.environ.get('BUILD_DATE', 'Unknown')}