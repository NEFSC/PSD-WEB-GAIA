# ------------------------------------------------------------------------------
#
# Adds interesting points, as GeoJSONs, to the SpatiaLite database.
#
# Written by John Wall (john.wall@noaa.gov)
#
# N.B.: Orignially written as a Jupyter Notebook, limited validation has been done.
#
# ------------------------------------------------------------------------------

# Import some libraries, configure Django
import os
import django
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

# User defined variables
interesting_points_dir = '../../data/geojson/interesting_points_5-2-2025'

poi_columns = ['id', 'vendor_id', 'sample_idx', 'area', 'deviation', 'epsg_code', 'cog_url']

# Identify all GeoJSONs
geojsons = glob(interesting_points_dir + '/**/*.geojson', recursive=True)
geojsons = [geojson.replace('\\', '/') for geojson in geojsons]
geojsons[0]

# Review Interesting Points GeoJSON
gdf = gpd.read_file(geojsons[0])
print(f"The shape of your Geodataframe is: {gdf.shape}\n")
gdf.head()

# Add Interesting Points to SpatiaLite Database
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
    cog_root = '_'.join(geojsons[0].split('/')[-1:][0].split('.')[0].split('_')[:-1])
    cog_url = f"https://gaianoaastorage.blob.core.windows.net/data/cogs/{cog_root}_cog.tif"
    print(f"Adding points for {vid}")
    # obj = ETL.objects.get(vendor_id=vid)

    epsg_code = geojson_path.split('/')[-1:][0].split('.')[0].split('_')[-2].split('mr')[-1]
    gdf = gpd.read_file(geojson_path)

    for index, row in gdf.iterrows():
        # print(f"Processing row: {row['id']}")
        poi, created = POI.objects.update_or_create(
            sample_idx = row['id'],
            defaults={
                # 'catalog_id': obj.id,
                # 'vendor_id': obj.vendor_id,
                'vendor_id': vid,
                # 'entity_id': obj.entity_id,
                'area': row['area'],
                'deviation': row['deviation'],
                'epsg_code': epsg_code,
                'cog_url': cog_url,
                'point': row['geometry'].wkt
            }
        )
        # print(f"\t{'Created' if created else 'Updated'} POI with id: {poi.sample_idx}\n")

    # print('Data imported successfully!')

start = time()

async def import_poi_async(file_path):
    await sync_to_async(import_poi, thread_sensitive=True)(file_path)

import asyncio

if asyncio.get_event_loop().is_running():
    for geojson in geojsons[0:5]:
        await import_poi_async(geojson)
else:
    asyncio.run(import_poi_async(geojson))

end = round(time() - start, 2)
print("It took {} seconds to load {} GeoJSONs".format(end, len(geojsons))) 

# Confirm that the points were added
objs = await sync_to_async(list)(POI.objects.all())
print(f"Number of POI records in database: {len(objs)}\n")

vid = '_'.join(geojsons[0].split('/')[-1:][0].split('.')[0].split('_')[:-2])

geoms = []
attributes = []
for obj in objs:
    if obj.vendor_id == vid:
        attr_dict = {col: getattr(obj, col) for col in poi_columns}
        attributes.append(attr_dict)
    
        geoms.append(GEOSGeometry(obj.point))

gdf = gpd.GeoDataFrame(attributes, geometry = [loads(g.wkt) for g in geoms])
gdf.head()

# Identify unique Vendor IDs
objs = await sync_to_async(list)(POI.objects.all())
print(f"Number of POI records in database: {len(objs)}\n")

vendor_ids = list(set([obj.vendor_id for obj in objs]))
print(f"Your unique vendor ids are: {vendor_ids}")

vendor_ids_list = [obj.vendor_id for obj in objs]
vendor_dict = {}
for vendor_id in vendor_ids:
    vendor_dict.update({
        vendor_id: vendor_ids_list.count(vendor_id)
    })

pd.DataFrame.from_dict(vendor_dict, orient='index', columns=['poi'])