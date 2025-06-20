# ------------------------------------------------------------------------------
#
# Adds interesting points, as GeoJSONs, to the SpatiaLite database.
#
# Written by John Wall (john.wall@noaa.gov)
#
# ------------------------------------------------------------------------------

# ----------------------------
# Import some libraries, configure Django
# ----------------------------
import os
import django
import asyncio
import pandas as pd
from glob import glob
from time import time
import geopandas as gpd
import subprocess
from shapely.wkt import loads

import sys; sys.path.append('../../')
os.environ['DJANGO_SETTINGS_MODULE'] = 'gaia.settings'
django.setup()

from asgiref.sync import sync_to_async
from django.core.management import call_command
from django.contrib.gis.geos import GEOSGeometry

from animal.models import ExtractTransformLoad as ETL
from animal.models import PointsOfInterest as POI

# ----------------------------
# User defined variables
# ----------------------------
interesting_points_dir = '../../gis/data/geojson/interesting_points_5-2-2025'

# ----------------------------
# Locally defined functions
# ----------------------------
def import_poi(geojson_path):
    """ Synchronous Import Points of Interest function.

        Takes the GeoJSON filepath and converts the file path to Vendor ID
            using the panchromatic image as the basis for this (opposed to
            the multispectral). Queries the ExtractTransformLoad (ETL) table
            in SpatiaLite for the relevant Vendor ID object. Reads the GeoJSON
            file to a GeoDataFrame. Updates or creates the Interesting Points
            records from a combination of the ETL and GeoJSON information.

        Print statements support troubleshooting.
    """
    cid = geojson_path.split('/')[-2]
    
    vid = '_'.join(geojson_path.split('/')[-1:][0].split('.')[0].split('_')[:-2])
    cog_root = '_'.join(geojson_path.split('/')[-1:][0].split('.')[0].split('_')[:-1])
    print(f"Adding points for {vid}")

    epsg_code = geojson_path.split('/')[-1:][0].split('.')[0].split('_')[-2].split('mr')[-1]
    gdf = gpd.read_file(geojson_path)

    for index, row in gdf.iterrows():
        poi, created = POI.objects.update_or_create(
            defaults={
                'area': row['area'],
                'deviation': row['deviation'],
                'epsg_code': epsg_code,
                'point': row['geometry'].wkt
            },
            sample_idx = row['id'],
            vendor_id = vid,
        )

# ----------------------------
# Identify all GeoJSONs
# ----------------------------
interesting_points_dir = os.path.abspath(interesting_points_dir)
geojsons = glob(interesting_points_dir + '/**/*.geojson', recursive=True)
geojsons = [geojson.replace('\\', '/') for geojson in geojsons]
print(f"\nFound {len(geojsons)} GeoJSON files to load into the database!\n")
print(geojsons[0])

# ----------------------------
# Load points
# ----------------------------
async def import_poi_async(file_path):
    await sync_to_async(import_poi, thread_sensitive=True)(file_path)

start = time()

async def run_all():
    for geojson in geojsons:
        await import_poi_async(geojson)

asyncio.run(run_all())

end = time()
print(f"\n Loaded {len(geojsons)} GeoJSONs in {round(end - start, 2)} seconds.")

# ----------------------------
# Confirm points were loaded
# ----------------------------
poi_columns = ['id', 'vendor_id', 'sample_idx', 'area', 'deviation', 'epsg_code']

sample_vid = '_'.join(geojsons[0].split('/')[-1].split('.')[0].split('_')[:-2])
objs = list(POI.objects.filter(vendor_id=sample_vid))
print(f"Found {len(objs)} POI records for vendor_id: {sample_vid}")

geoms = []
attributes = []
for obj in objs:
    attr_dict = {col: getattr(obj, col) for col in poi_columns}
    attributes.append(attr_dict)
    geoms.append(GEOSGeometry(obj.point))

gdf = gpd.GeoDataFrame(attributes, geometry=[loads(g.wkt) for g in geoms])
print(gdf.head())
print(gdf.shape)

# ----------------------------
# Confirm unique Vendor IDs
# ----------------------------
vendor_ids = []
for geojson in geojsons:
    vendor_id = '_'.join(geojson.split('/')[-1].split('.')[0].split('_')[:-2])
    vendor_ids.append(vendor_id)

print(f"Unique vendor_ids: {len(set(vendor_ids))}")
print(sorted(set(vendor_ids)))

# ----------------------------
# Provide some addtional details about points in the database
# ----------------------------
objs = list(POI.objects.all())

vendor_ids = [obj.vendor_id for obj in objs]

vendor_counts = pd.Series(vendor_ids).value_counts().reset_index()
vendor_counts.columns = ['vendor_id', 'point_count']

print(vendor_counts)