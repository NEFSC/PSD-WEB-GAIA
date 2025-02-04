# Basic stack
import os
import sys
import json
import shutil
import requests
import datetime
from datetime import datetime, timedelta
import subprocess
from time import time
from glob import glob
from wsgiref.util import FileWrapper

# Geospatial Stack
from pyproj import CRS, Transformer
from osgeo import gdal
from osgeo_utils.gdal_pansharpen import gdal_pansharpen
from shapely import to_geojson
from shapely.geometry import box, Point, Polygon
from fiona.drvsupport import supported_drivers
import pandas as pd
import geopandas as gpd

# Azure stack
from azure.core.credentials import AzureNamedKeyCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_blob_sas, BlobSasPermissions

# Django stack
import django
from django.core.cache import cache
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.db.models.functions import Transform
from django.contrib.sessions.models import Session
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.shortcuts import render, redirect, get_object_or_404
from django_q.tasks import async_task
from django.views import View

# GAIA stack
from ..security import ee_login, mgp_login
from ..models import AreaOfInterest, PointsOfInterest, EarthExplorer, GEOINTDiscovery, MaxarGeospatialPlatform, ExtractTransformLoad
from ..forms import APIQueryForm, ProcessingForm, PointsOfInterestForm
from ..tasks import process_etl_data
from ..query import build_ee_query_payload, query_mgp
from ..download import download_imagery
from ..utils import get_entity_pairs, standardize_names, calibrate_image, import_pois, upload_to_auzre  # should be depricated: convert_to_tiles

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaia.settings')
os.environ["CPL_DEBUG"] = "ON" # Should enable GDAL debuggin
django.setup()

def tasking_page(request):
    """ A simple page to show where Areas of Interest (AOIs) currently loaded
            in the SpatiaLite database are within the world.
    """
    aoi_objects = AreaOfInterest.objects.all()
    aoi_data = serialize('geojson', aoi_objects)
    aoi_data = json.loads(aoi_data)

    flattended_aoi_data = []
    for feature in aoi_data['features']:
        flattended_aoi_data.append({
            'id': feature['id'],
            'name': feature['properties']['name'],
            'requestor': feature['properties']['requestor'],
            'sqkm': feature['properties']['sqkm'],
            'geometry': feature['geometry'],
        })
    
    return render(request, 'tasking_page.html', {
        'aoi_data': flattended_aoi_data,
        'geojson_aoi_data': aoi_data
    })