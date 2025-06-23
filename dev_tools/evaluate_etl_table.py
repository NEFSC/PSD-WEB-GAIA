# ------------------------------------------------------------------------------
#
# This notebook is intended to validate information in the ExtractTransformLoad
#      table as modeled in Django.
#
# Written by John Wall (john.wall@noaa.gov)
#
# N.B.: Orignially written as a Jupyter Notebook, limited validation has been done.
#
# ------------------------------------------------------------------------------


# Import some libraries, configure Django
import os

import sqlite3

import shapely
from shapely.geometry import Polygon
import pandas as pd
import geopandas as gpd

import django

import sys; sys.path.append('../../')
os.environ['DJANGO_SETTINGS_MODULE'] = 'gaia.settings'
django.setup()

from asgiref.sync import sync_to_async
from django.core.management import call_command
from django.contrib.gis.geos import GEOSGeometry

from animal.models import EarthExplorer as EE

imgs = await sync_to_async(list)(EE.objects.all())

for img in imgs[0:5]:
    geom = GEOSGeometry(img.bounds).wkt
    print(f"EE - X: {img.pixel_size_x} | Y: {img.pixel_size_y} | Geom: {geom}")

    db = "../../db.sqlite3"

animal_earthexplorer_columns = ['entity_id', 'catalog_id', 'acquisition_date', 'vendor',
                               'vendor_id', 'cloud_cover', 'satellite', 'sensor',
                               'number_of_bands', 'map_projection', 'datum',
                               'processing_level', 'file_format', 'license_id',
                               'sun_azimuth', 'sun_elevation', 'pixel_size_x',
                               'pixel_size_y', 'license_uplift_update', 'event',
                               'date_entered', 'center_latitude_dec',
                               'center_longitude_dec', 'thumbnail', 'publish_date',
                               'aoi_id_id', 'event_date']

conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

columns_list = list(animal_earthexplorer_columns)
columns_str = ', '.join(columns_list)
sql_string = "SELECT {}, AsText(bounds) FROM animal_earthexplorer WHERE vendor IS NOT NULL AND aoi_id_id = {}".format(columns_str, 1)

df = pd.read_sql_query(sql_string, conn)
df = df.rename(columns={'AsText(bounds)': 'geometry'}, errors='raise')
df['geometry'] = shapely.wkt.loads(df['geometry'])
gdf = gpd.GeoDataFrame(df, geometry='geometry')

conn.commit()
conn.close()

gdf.head()

set(gdf['pixel_size_y'])

set(gdf['pixel_size_x'])

set(gdf['aoi_id_id'])

type(gdf['aoi_id_id'][0])