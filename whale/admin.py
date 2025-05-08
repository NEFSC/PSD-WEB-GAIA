"""
Django admin configuration module for the whale application.

Models registered:
    - Targets: Configures display and search fields for Target instances
        - list_display shows the target name
        - search_fields allows searching by target name and scientific name

Note: AreaOfInterest admin configuration is currently commented out.  It needs a way for user to upload .geojson or .kml/.kmz
"""

from django.contrib import admin
from .models import AreaOfInterest, Targets, Tasking

# @admin.register(AreaOfInterest)
# class AreaOfInterestAdmin(admin.ModelAdmin):
#     list_display = ('name',)
#     search_fields = ['name']

@admin.register(Targets)
class TargetsAdmin(admin.ModelAdmin):
    list_display = ('target',)
    search_fields = ['target', 'scientific_name']

