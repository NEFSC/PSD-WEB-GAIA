from django.urls import path
from django.contrib.auth.decorators import login_required, user_passes_test
from . import views
from .views.annotation_views import proxy_openlayers_js, proxy_webgls_js

def is_superuser(user):
    return user.is_superuser

urlpatterns = [
    path('', login_required(views.landing_page), name='landing_page'),
    path('project', login_required(views.project_page), name='project_list'),
    path('project/<int:project_id>/tasking/', login_required(views.tasking_page), name='tasking_page'),
    path('project/<int:project_id>/collection/', login_required(views.collection_page), name='collection_page'),
    path('project/<int:project_id>/processing/', login_required(views.processing_page), name='processing_page'),
    path('project/<int:project_id>/', login_required(views.project_page), name='project_detail'),
    path('project/<int:project_id>/annotation/', login_required(views.annotation_page), name='annotation_page'),
    path('project/<int:project_id>/annotation/<int:item_id>/', login_required(views.annotation_page), 
         name='annotation_item_page'),
    path('project/<int:project_id>/poi/create', login_required(views.create_point), 
         name='create_point'),
    path('project/<int:project_id>/detect/', login_required(views.detect_page), name='detect_page'),
    path('project/<int:project_id>/detect/<int:id>/', login_required(views.detect_page), name='detect_item_page'),
    path('cogs/<str:vendor_id>/', views.cog_view, name='cog_view'),
    path('project/<int:project_id>/dissemination/', login_required(views.dissemination_page), name='dissemination_page'),
    path('project/<int:project_id>/validation/', user_passes_test(is_superuser, login_url='/access-denied/')(views.validation), name='validation'),
    path('proxy/openlayers.js', proxy_openlayers_js, name='proxy_openlayers_js'),
    path('proxy/ol-webgl.js', proxy_webgls_js, name='proxy_webgls_js'),
    path('access-denied/', views.access_denied, name='access_denied'),
]