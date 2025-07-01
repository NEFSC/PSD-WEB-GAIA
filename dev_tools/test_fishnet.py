# ------------------------------------------------------------------------------
# ----- test_fishnet.py --------------------------------------------------------
# ------------------------------------------------------------------------------
#
#    authors:  John Wall (john.wall@noaa.gov)
#              
#    purpose:  Test evaluation of the fishnet method
#
# ------------------------------------------------------------------------------



# ------------------------------------------------------------------------------
# Import libraries, configure environment
# ------------------------------------------------------------------------------
import os
import sys
import django
import asyncio
import importlib
from time import time
from glob import glob
from pathlib import Path
from asgiref.sync import sync_to_async

# Set PROJ_LIB environment variable to fix projection issues
os.environ['PROJ_LIB'] = '/opt/conda/envs/gaia/share/proj'

project_dir = "../"
project_dir = os.path.abspath(project_dir)
sys.path.append(str(project_dir))

import utils.spatial_ops
importlib.reload(utils.spatial_ops)

os.environ['DJANGO_SETTINGS_MODULE'] = 'gaia.settings'
django.setup()

from animal.models import Fishnet as FN


# ------------------------------------------------------------------------------
# Basic test for fishnet method
# ------------------------------------------------------------------------------
data_dir = ""
sub_dir = ""

data_dir = os.path.abspath(data_dir)
cogs = glob(os.path.join(data_dir, sub_dir, '**', "*.tif"), recursive=True)

test_cog = [cogs[0]]
print(f"\nRunning test on {test_cog[0]}!\n")
fishnet_gdf = utils.spatial_ops.create_fishnet(test_cog)


# ------------------------------------------------------------------------------
# Import fishnet into the SpatiaLite database
# ------------------------------------------------------------------------------
def import_fishnet(gdf):
    """Synchronous import fishnet cells."""
    for index, row in gdf.iterrows():
        FN.objects.update_or_create(
            vendor_id=row['vendor_id'],
            defaults={'cell': row['geometry'].wkt}
        )

async def import_fishnet_async(gdf):
    await sync_to_async(import_fishnet, thread_sensitive=True)(gdf)

start = time()

async def run_all():
    await import_fishnet_async(fishnet_gdf)

asyncio.run(run_all())

end = time()
print(f"\n Loaded in {round(end - start, 2)} seconds.")
