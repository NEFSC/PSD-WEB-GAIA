# ------------------------------------------------------------------------------
#
# Standardizes functions from the Polar Geospatial Center's "Image Utils"
#   repository for use within this application as well as enabling
#   troubleshooting locally.
#
# Written by John Wall (john.wall@noaa.gov)
#
# N.B. this might be better named pgc_utils.py, but could become confusing
#   when talking to others. Therefore, wrapper was chosen.
#
# ------------------------------------------------------------------------------



# ----------------------------
# Import libraries, find third-party exript
# ----------------------------
import os
import sys
import subprocess
from glob import glob
from pathlib import Path

try:
    base_dir = Path(__file__).resolve().parent.parent
except NameError:
    # For interactive environments or if __file__ is not available
    base_dir = Path(os.getenv("PROJECT_ROOT", Path.cwd()))

external_dir = base_dir / "external" / "imagery_utils"
print(f"The imagery utilities directory is: {external_dir}")
sys.path.append(str(external_dir))


# ----------------------------
# Example function
# ----------------------------
def run_orthorectification(input_dem: str, output_dir: str, other_args: list = None):
    """
    Wrapper for PGC's pgc_ortho.py to orthorectify imagery with your parameters.
    """
    if other_args is None:
        other_args = []

    # Mimic CLI call to pgc_ortho
    args = [
        "pgc_ortho.py",
        "--dem", input_dem,
        "--outdir", output_dir,
        *other_args,
    ]

    print(f"Running pgc_ortho with: {' '.join(args)}")
    pgc_ortho.main(args)  # Use pgc_ortho's main function directly if callable


# ----------------------------
# Real functions
# ----------------------------
def calibrate_image(tiff, dem):
    """ Calibrates a given Maxar 1B image using the Polar Geospatial Center (PGC) method
             (see references). Georeferences the images to the nearest UTM zone, applies
             no stretch to the image, outputs to GeoTIFF format, the image will be
             16-bit Unsigned Integer, and resampled using cubic convolution.
    
        Ref: https://www.pgc.umn.edu/guides/pgc-coding-and-utilities/using-pgc-github-orthorectification/
        Ref: https://github.com/PolarGeospatialCenter/imagery_utils/blob/main/doc/pgc_ortho.txt
    """
    dir_path = os.path.dirname(os.path.realpath(tiff))
    print(f"Your dir_path is: {dir_path}")
    dir_path_new = "\\".join(os.path.dirname(tiff).split('\\')[:-1] + ["calibrated"]) 
    # dir_path_new = os.path.join(dir_path, 'calibrated/') # Make LInux style
    print(f"Your new dir_ath is: {dir_path_new}")
    if not os.path.exists(dir_path_new):
        os.makedirs(dir_path_new)

    subprocess.run([sys.executable,
                    f'{external_dir}/pgc_ortho.py',
                    '-p', 'utm',
                    '-c', 'mr',
                    '-f', 'GTiff',
                    '-t', 'Byte',
                    '-d', dem,
                    '--resample=cubic',
                    dir_path,
                    dir_path_new])
    try:
        img_out = glob(dir_path_new + "/*.tif")[0]
        print(f"Your image is: {img_out}")
        return img_out
    except:
        print("Failed on: {}".format(tiff))
        pass