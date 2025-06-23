# ------------------------------------------------------------------------------
#
# Functions for interacting with USGS's EarthExplorer platform via its
#   REST API endpoint.
#
# Written by John Wall (john.wall@noaa.gov)
#
# ------------------------------------------------------------------------------

# ----------------------------
# Import some libraries, configure Django
# ----------------------------
import os
import sys
import shutil
import zipfile
from glob import glob
from time import time
from pathlib import Path
import multiprocessing as mp
from functools import partial

sys.path.append("../"); import whale_detector

# ----------------------------
# Set environmental variables
# ----------------------------
os.environ["GDAL_VRT_ENABLE_PYTHON"] = "YES"

# ----------------------------
# Set environmental variables
# ----------------------------
img_dir = "../data/imagery/"
pgc_ortho = 'C:/gis/imagery_utils/pgc_ortho.py'
dem = "../data/rasters/output_hh.tif"