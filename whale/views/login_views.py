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
from ..models import AreaOfInterest, PointsOfInterest, EarthExplorer, GEOINTDiscovery, MaxarGeospatialPlatform, ExtractTransformLoad, BlindReviews
from ..forms import APIQueryForm, ProcessingForm, PointsOfInterestForm
from ..tasks import process_etl_data
from ..query import build_ee_query_payload, query_mgp
from ..download import download_imagery
from ..utils import get_entity_pairs, standardize_names, calibrate_image, import_pois, upload_to_auzre  # should be depricated: convert_to_tiles

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaia.settings')
os.environ["CPL_DEBUG"] = "ON" # Should enable GDAL debuggin
django.setup()

def login_view(request):
    """ A simple log-in page meeting NOAA OCIO's security requirement for
            a username and password protecting restricted access
            satellite imagery.
    """
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
    """ A basic landing page for the WHale Active Learning Environment (WHALE)
            Tasking, Collection, Processing, Exploitation, and Dissimination
            (TCPED) pages. Each TCPED task has its own page linked to this
            one.
    """
    return render(request, 'landing_page.html')

def check_records_view(request):
    """ Supports validating that a point of interest actually exists within the database. """
    records_exist = PointsOfInterestForm.objects.exists()
    return render(request, 'check_records.html', {'records_exist': records_exist})