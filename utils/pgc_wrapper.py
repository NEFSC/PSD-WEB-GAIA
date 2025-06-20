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
import sys
from pathlib import Path

try:
    base_dir = Path(__file__).resolve().parent.parent
except NameError:
    # For interactive environments or if __file__ is not available
    base_dir = Path(os.getenv("PROJECT_ROOT", Path.cwd()))

external_dir = base_dir / "external" / "imagery_utils"
print(external_dir)
sys.path.append(str(external_dir))


# ----------------------------
# Functions to be pulled from utils.py
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
