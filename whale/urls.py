from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views
from .views.exploitation_views import proxy_openlayers_js, proxy_webgls_js
from .views.reset_pw_view import MyResetPasswordView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', login_required(views.landing_page), name='landing_page'),
    path('tasking/', login_required(views.tasking_page), name='tasking_page'),
    path('collection/', login_required(views.collection_page), name='collection_page'),
    path('processing/', login_required(views.processing_page), name='processing_page'),
    path('exploitation/', login_required(views.exploitation_page), name='exploitation_page'),
    path('exploitation/<int:item_id>', login_required(views.exploitation_page), name='exploitation_page'),
    path('exploitation/check-records/', login_required(views.check_records_view), name='check_records'),
    path('exploitation/cogs/<str:vendor_id>/', views.cog_view, name='cog_view'),
    path('dissemination/', login_required(views.dissemination_page), name='dissemination_page'),
    path('proxy/openlayers.js', proxy_openlayers_js, name='proxy_openlayers_js'),
    path('proxy/ol-webgl.js', proxy_webgls_js, name='proxy_webgls_js'),
    path('blind-reviews/', views.blind_reviews, name='blind_reviews'),
]
