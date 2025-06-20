# ------------------------------------------------------------------------------
#
# Quality Assurance and Control of GeoDjango Objects.
#      Helps assure that the SQLite tables are spatially enabled, i.e. SpatiaLite,
#      and are properly modeled by GeoDjango. This notebook also documents a lot
#      of the validation needed to configure GeoDjango components.
#
# Configuring SpatiaLite and enabling GeoDjango
#      Within `settings.py` the following need to be configured:
#      - "GDAL_LIBRARY_PATH"
#      - "SPATIALITE_LIBRARY_PATH"
#      Also within `settings.py` "INSTALLED_APPS" needs to be amended to include
#           `'django.contrib.gis'` and the "DATABASES" 'ENGINE' needs to be
#           amended to be `'django.contrib.gis.db.backends.spatialite'`.
#
#       At `[PROJECT]/` you need to download and unzip SpatiaLite from
#       https://www.gaia-gis.it/gaia-sins/) as well as make the amendments to your
#       `libgdal.py` recommended in
#       https://stackoverflow.com/questions/46313119/geodjango-could-not-find-gdal-library-in-windows-10
#       StackOverflow post.
#
# Spatially Enabling Django Database
#       Use the following code as a template to spatially enable your Django SQLite
#       database turning it into a SpatiaLite database and therefore making your
#       application a GeoDjango application. This code builds the metadata tables
#       for spatial data.

'''
import sqlite3

db = "path/to/django/database/db.sqlite3"

conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

c = conn.cursor()
c.execute('''SELECT InitSpatialMetaData();''')
conn.commit()
conn.close()
'''

# Validating SpatiaLite and GeoDjango
#     From an Anaconda prompt window, activate your environment of choice and
#     nagivate to your GeoDjango database. Here issue a command something
#     like `sqlite3 db.sqlite3` which will turn your Anaconda prompt into a
#     sqlite terminal. From here issue the command `.tables` you should see
#     a bunch of geometry tables among others. Quit this termainl with `.quit`.
#
#     From the Anaconda prompt, activate a GeoDjango Database Shell terminal
#     with `python manage.py dbshell` this should launch you into a spatialite
#     terminal. Quit out of this termainl with `.quit`.
#
#     From the Anaconda prompt, activate a GeoDjango Shell terminal with
#     `python manage.py shell`. At this point, we just want to make sure this
#     starts up and will validate what should come out of here below since we
#     are doing commands here, in the Jupyter Notebook, that could otherwise
#     be implimented within the Shell terminal.
#
# Written by John Wall (john.wall@noaa.gov)
#
# N.B.: Orignially written as a Jupyter Notebook, limited validation has been done.
#
# ------------------------------------------------------------------------------


# Basic stack
import os

# Database stack
import sqlite3

# Geospatial stack
import shapely
from shapely.wkt import loads
from shapely.geometry import Polygon
import pandas as pd
import geopandas as gpd
import folium

# GeoDjango stack
import django

import sys; sys.path.append('../../')
os.environ['DJANGO_SETTINGS_MODULE'] = 'gaia.settings'
django.setup()

from django.db import connection
from django.contrib.gis.geos import GEOSGeometry
from asgiref.sync import sync_to_async

from animal.models import AreaOfInterest as AOI
from animal.models import ExtractTransformLoad as ETL

# User defined variables
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
animal_areaofinterest_columns = ['id', 'name', 'requestor', 'sqkm']
etl_columns = ['table_name', 'aoi_id', 'id', 'vendor_id', 'entity_id', 'vendor',
               'platform', 'pixel_size_x', 'pixel_size_y', 'date', 'publish_date',
               'sea_state_qual', 'sea_state_quant', 'shareable']

# Validate geospatial data within the SpatiaLite database
## Connect to database, load SpatiaLite exntention
conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

## Using the column names within Animal's EarthExplorer table, select first ten records
columns_str = ', '.join(animal_earthexplorer_columns)
sql_string = "SELECT {}, AsText(bounds) FROM animal_earthexplorer LIMIT 10".format(columns_str)
df = pd.read_sql_query(sql_string, conn)

## Build GeoDataFrame from results
df = df.rename(columns={'AsText(bounds)': 'geometry'}, errors='raise')
df['geometry'] = shapely.wkt.loads(df['geometry'])
gdf = gpd.GeoDataFrame(df, geometry='geometry')

## Close your database connection
conn.commit()
conn.close()

## Show records
gdf.head()

# Plot GeoDataFrame on an interactive map
def style_function(hex_value):
    return {'color': hex_value, 'fillOpacity': 0}

## Add OpenStreetMap as a basemap
map = folium.Map()
folium.TileLayer('openstreetmap').add_to(map)

## Create a GeoJson layer from the response_geojson and add it to the map
folium.GeoJson(
    gdf['geometry'].to_json(),
    style_function = lambda x: style_function('#0000FF')
).add_to(map)

## Zoom to collected images
map.fit_bounds(map.get_bounds(), padding=(100, 100))

## Display the map
map

# Leverage GeoDjango's models to retrieve database objects
#      GeoDjango's `models.py` file provides GeoDjango with a blueprint for how
#      the application should interact with the database returning objects.
#      This means datatypes, constraints, etc. need to match between the models
#      and the database. If not, there is no guarantee the application will
#      retrieve the information we desire if any information at all.
#
#      Above, note that we used the table "whale_earthexplorer" where the
#      application name is appended as a prefix to the model class. To
#      validate that we can also retrieve the same information as objects
#      let's import EarthExplorer from the Whale models and retrieve as well
#      as plot this information.

from animal.models import EarthExplorer as EE

## Retrieve the first ten EarthExplorer objects from GeoDjango
imgs = await sync_to_async(list)(EE.objects.all()[:10])

## Create a GeoDataFrame
geoms = []
attributes = []
for img in imgs:
    attr_dict = {col: getattr(img, col) for col in animal_earthexplorer_columns}
    attributes.append(attr_dict)

    geoms.append(GEOSGeometry(img.bounds))

gdf = gpd.GeoDataFrame(attributes, geometry = [loads(g.wkt) for g in geoms])
gdf.head()

# Plot the results
def style_function(hex_value):
    return {'color': hex_value, 'fillOpacity': 0}

## Add OpenStreetMap as a basemap
map = folium.Map()
folium.TileLayer('openstreetmap').add_to(map)

## Create a GeoJson layer from the response_geojson and add it to the map
folium.GeoJson(
    gdf['geometry'].to_json(),
    style_function = lambda x: style_function('#0000FF')
).add_to(map)

## Zoom to collected images
map.fit_bounds(map.get_bounds(), padding=(100, 100))

## Display the map
map

# Let's confirm the above code works for other models like AOI
## Retrieve the first ten EarthExplorer objects from GeoDjango
imgs = await sync_to_async(list)(AOI.objects.all()[:10])

## Create a GeoDataFrame
geoms = []
attributes = []
for img in imgs:
    attr_dict = {col: getattr(img, col) for col in animal_areaofinterest_columns}
    attributes.append(attr_dict)

    geoms.append(GEOSGeometry(img.geometry))

gdf = gpd.GeoDataFrame(attributes, geometry = [loads(g.wkt) for g in geoms])
gdf.head()

# Plot the results
def style_function(hex_value):
    return {'color': hex_value, 'fillOpacity': 0}

## Add OpenStreetMap as a basemap
map = folium.Map()
folium.TileLayer('openstreetmap').add_to(map)

## Create a GeoJson layer from the response_geojson and add it to the map
folium.GeoJson(
    gdf['geometry'].to_json(),
    style_function = lambda x: style_function('#0000FF')
).add_to(map)

## Zoom to collected images
map.fit_bounds(map.get_bounds(), padding=(100, 100))

## Display the map
map

# Now, let's repeat this for the ExtractTransformLoad (ETL) Table
#      Note that the ETL table is a table created from other table. I've seen
#      this described as a junction or denormalized table amongst others. The
#      key point is that this table integrates imagery across our three data
#      sources (USGS EarthExplorer, GEGD, and Maxar Geospatial Platform) into
#      a uniform table. As such, you'll notice there is no "whale_" prefix.
#      Records are added to the table from triggers. This is the table we
#      want to ensure always passes QA/QC.

## Retrieve the first 25 EarthExplorer objects from GeoDjango
imgs = await sync_to_async(list)(ETL.objects.all()[:25])

## Create a GeoDataFrame
geoms = []
attributes = []
for img in imgs:
    attr_dict = {col: getattr(img, col) for col in etl_columns}
    attributes.append(attr_dict)

    geoms.append(GEOSGeometry(img.geometry))

gdf = gpd.GeoDataFrame(attributes, geometry = [loads(g.wkt) for g in geoms])
gdf.head(25)

# Plot the results
def style_function(hex_value):
    return {'color': hex_value, 'fillOpacity': 0}

## Add OpenStreetMap as a basemap
map = folium.Map()
folium.TileLayer('openstreetmap').add_to(map)

## Create a GeoJson layer from the response_geojson and add it to the map
folium.GeoJson(
    gdf['geometry'].to_json(),
    style_function = lambda x: style_function('#0000FF')
).add_to(map)

## Zoom to collected images
map.fit_bounds(map.get_bounds(), padding=(100, 100))

## Display the map
map