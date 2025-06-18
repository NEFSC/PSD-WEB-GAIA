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
import django
import pandas as pd

import sys; sys.path.append('../../')
os.environ['DJANGO_SETTINGS_MODULE'] = 'gaia.settings'
django.setup()

from asgiref.sync import sync_to_async
from django.core.management import call_command
from django.contrib.gis.geos import GEOSGeometry

from animal.models import ExtractTransformLoad as ETL

imgs = await sync_to_async(list)(ETL.objects.all())

for img in imgs[0:5]:
    geom = GEOSGeometry(img.geometry).wkt
    print(f"ETL Table Name: {img.table_name} | ID: {img.aoi_id} | Vendor ID: {img.vendor_id} | Geom: {geom}")

for img in imgs:
    if img.table_name == "EE":
        if img.aoi_id == 1:
            print(img.entity_id)

imgs = await sync_to_async(list)(ETL.objects.all().values())
df = pd.DataFrame(imgs)
df.to_csv('etl_output.csv', index=False)