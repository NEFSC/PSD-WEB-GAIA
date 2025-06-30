# Basic stack
import os
import django
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from animal.models import Project

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaia.settings')
os.environ["CPL_DEBUG"] = "ON" # Should enable GDAL debuggin
django.setup()

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('landing_page')
    else:
        form = AuthenticationForm()
        
    return render(request, 'login.html', {'form': form})

def landing_page(request):
    projects = Project.objects.all()
    return render(request, 'landing_page.html', {'projects': projects})

def project_page(request, project_id=None):
    if project_id is None:
        return redirect('landing_page')  # Redirect to landing page if no project_id is provided
    project = Project.objects.filter(id=project_id)
    return render(request, 'project_page.html', {'project': project})