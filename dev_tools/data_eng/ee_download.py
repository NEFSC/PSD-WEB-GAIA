# ------------------------------------------------------------------------------
#
# When provided with a directory of imagery, create panshapered web-entabled COGs
#
# Written by John Wall (john.wall@noaa.gov)
#
# ------------------------------------------------------------------------------

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