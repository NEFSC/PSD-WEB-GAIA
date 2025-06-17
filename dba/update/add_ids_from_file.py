# ------------------------------------------------------------------------------
#
# Adds US Goverment Catalog IDs and Entity IDs when provide with Vendor IDs as
#      file names of GeoTIFFs.
#
# Written by John Wall (john.wall@noaa.gov)
#
# ------------------------------------------------------------------------------

# Import some libraries, configure Django
import os
import django
import zipfile
import pandas as pd
import geopandas as gd
from glob import glob
from time import time
import geopandas as gpd
import subprocess
from shapely.wkt import loads
import xml.etree.ElementTree as ET

import sys; sys.path.append('../../')
os.environ['DJANGO_SETTINGS_MODULE'] = 'gaia.settings'
django.setup()

from asgiref.sync import sync_to_async
from django.core.management import call_command
from django.contrib.gis.geos import GEOSGeometry

from animal.models import PointsOfInterest as POI

# User define variables
data_dir = "../../../gis/data/"
local_geojson = "files.geojson"

# Read GeoJSON into memory
data_dir = os.path.abspath(data_dir)
filepath = os.path.join(data_dir, local_geojson)
gdf = gd.read_file(filepath)

# Keep only relevant columns, update Vendor ID for database
gdf = gdf[['Entity ID', 'Vendor ID', 'Catalog ID']]
gdf['Vendor ID'] = gdf['Vendor ID'].str.replace(r'P1BS|M1BS', 'S1BS', regex=True)
gdf = gdf.drop_duplicates(subset='Vendor ID', keep='first')

# No further work done on this as the data appears to be incomplete...