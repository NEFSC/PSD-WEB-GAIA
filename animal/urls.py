"""
URL configuration for GAIA project's animal application.

This module contains URL patterns for various views within the animal application.
Each path maps a URL pattern to a specific view function, with most routes requiring user authentication.

URL Patterns:
    - '': Landing page (requires login)
    - 'tasking/': Task management page (requires login)
    - 'collection/': Data collection page (requires login)
    - 'processing/': Data processing page (requires login)
    - 'annotation/': Data annotation page (requires login)
    - 'annotation/<int:item_id>': Specific item annotation page (requires login)
    - 'annotation/cogs/<str:vendor_id>/': COG (Cloud Optimized GeoTIFF) view
    - 'dissemination/': Data dissemination page (requires login)
    - 'proxy/openlayers.js': Proxy for OpenLayers JavaScript
    - 'proxy/ol-webgl.js': Proxy for WebGL JavaScript
    - 'validation/': Validation page
"""

from django.urls import path
from django.contrib.auth.decorators import login_required, user_passes_test
from . import views
from .views.annotation_views import proxy_openlayers_js, proxy_webgls_js

def is_superuser(user):
    return user.is_superuser

urlpatterns = [
    path('', login_required(views.landing_page), name='landing_page'),
    path('tasking/', login_required(views.tasking_page), name='tasking_page'),
    path('collection/', login_required(views.collection_page), name='collection_page'),
    path('processing/', login_required(views.processing_page), name='processing_page'),
    path('project/', login_required(views.project_page), name='project_page'),
    path('annotation/', login_required(views.annotation_page), name='annotation_page'),
    path('annotation/<int:item_id>', login_required(views.annotation_page), name='annotation_page'),
    path('annotation/cogs/<str:vendor_id>/', views.cog_view, name='cog_view'),
    path('dissemination/', login_required(views.dissemination_page), name='dissemination_page'),
    path('proxy/openlayers.js', proxy_openlayers_js, name='proxy_openlayers_js'),
    path('proxy/ol-webgl.js', proxy_webgls_js, name='proxy_webgls_js'),
    path('validation/', user_passes_test(is_superuser, login_url='/access-denied/')(views.validation), name='validation'),
    path('access-denied/', views.access_denied, name='access_denied'),
]