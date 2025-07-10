"""
Django admin configuration module

Note: AreaOfInterest admin configuration is currently commented out.  It needs a way for user to upload .geojson or .kml/.kmz
"""

from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import AreaOfInterest, Target, Classification, Confidence, Project, PointsOfInterest, Category
from adminsortable2.admin import SortableInlineAdminMixin, SortableAdminBase

# @admin.register(AreaOfInterest)
# class AreaOfInterestAdmin(admin.ModelAdmin):
#     list_display = ('name',)
#     search_fields = ['name']

@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    list_display = ('value',)
    search_fields = ['value', 'scientific_name']

@admin.register(Classification)
class ClassificationAdmin(admin.ModelAdmin):
    list_display = ('value', 'category')
    search_fields = ['value', 'label']

class ClassificationInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Classification
    extra = 1
    ordering = ('order',)

@admin.register(Category)
class CategoryAdmin(SortableAdminBase, admin.ModelAdmin):
    inlines = [ClassificationInline]

@admin.register(Confidence)
class ConfidenceAdmin(admin.ModelAdmin):
    list_display = ('value',)
    search_fields = ['value', 'label']
    list_filter = ['value', 'label']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('value',)
    search_fields = ['value', 'label']
    list_filter = ['value', 'label']

@admin.register(PointsOfInterest)
class PointsOfInterestAdmin(GISModelAdmin):
    list_display = ('id', 'vendor_id')