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
# Import libraries
# ------------------------------------------------------------------------------
import os
import sys
import importlib
from glob import glob
from pathlib import Path

project_dir = "../../../gis/PSD-WEB-GAIA"
project_dir = os.path.abspath(project_dir)
sys.path.append(str(project_dir))

import utils.spatial_ops
importlib.reload(utils.spatial_ops)

# ------------------------------------------------------------------------------
# Basic test for fishnet method
# ------------------------------------------------------------------------------
data_dir = "../../../gis/data/"
sub_dir = "cogs/"

data_dir = os.path.abspath(data_dir)
cogs = glob(os.path.join(data_dir, sub_dir, '**', "*.tif"), recursive=True)

test_cog = [cogs[0]]
print(f"\nRunning test on {test_cog[0]}!\n")
fishnet_gdf = utils.spatial_ops.create_fishnet(test_cog)