# Basic stack
import os
import django
from django.shortcuts import render

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaia.settings')
os.environ["CPL_DEBUG"] = "ON" # Should enable GDAL debuggin
django.setup()

def dissemination_page(request):
    """ This page is to inform the scientific investigators as to what is currently within
            the data so that they can make decisions based on it (e.g., task for additional
            satellite imagery) (GAIFAGP-46).
    """
    return render(request, 'dissemination_page.html')