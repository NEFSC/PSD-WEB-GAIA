"""
Django admin configuration module

Note: AreaOfInterest admin configuration is currently commented out.  It needs a way for user to upload .geojson or .kml/.kmz
"""

from django.contrib import admin
from .models import AreaOfInterest, Targets, Classification, Confidence

# @admin.register(AreaOfInterest)
# class AreaOfInterestAdmin(admin.ModelAdmin):
#     list_display = ('name',)
#     search_fields = ['name']

@admin.register(Targets)
class TargetsAdmin(admin.ModelAdmin):
    list_display = ('value',)
    search_fields = ['value', 'scientific_name']

@admin.register(Classification)
class TaskingAdmin(admin.ModelAdmin):
    list_display = ('value',)
    search_fields = ['value', 'label']
    list_filter = ['value', 'label']

@admin.register(Confidence)
class ConfidenceAdmin(admin.ModelAdmin):
    list_display = ('value',)
    search_fields = ['value', 'label']
    list_filter = ['value', 'label']