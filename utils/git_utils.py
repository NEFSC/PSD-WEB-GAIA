# ------------------------------------------------------------------------------
#
# Download or update, after 15 days of cloning, a copy of Polar Geospatial
#   Center's "Image Utils" repository ensuring that the most up-to-date copy
#   of the repository is present for the GAIA application.
#
# This should likely be called as part of a start-up script.
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
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# ----------------------------
# Defined variables
# ----------------------------
repo_url = "https://github.com/PolarGeospatialCenter/imagery_utils.git"
max_age_days = 15

# ----------------------------
# Key functions
# ----------------------------
def is_repo_stale(path: Path, max_age_days: int) -> bool:
    """ Checks if the local version of Polar Geospatial Center's Imagery Utils
            is stale, based on a user-defined threashold of days, or not using
            boolean logic.

        PATH - Relative path to where IMAGERY UTILS should be cloned.
        MAX AGE DAYS - Maximum number of days to be considered stale.
    """
    if not path.exists():
        return True

    try:
        # Use last modified time of the .git directory as a proxy
        git_dir = path / ".git"
        last_modified = datetime.fromtimestamp(git_dir.stat().st_mtime)
        return datetime.now() - last_modified > timedelta(days=max_age_days)
    except Exception as e:
        print(f"Warning: Could not check age of repo. Re-cloning. Reason: {e}")
        return True

def clone_imagery_utils(external_dir: Path):
    """ Clones Polar Geospatial Center's Imagery Utilitys repository or if
            the repository is availble locally, deletes it and redownloads.
            Helps to ensure that the 

        EXTERNAL DIR - Directory for scripts from external, or third, parties.
    """
    if is_repo_stale(external_dir, MAX_AGE_DAYS):
        if external_dir.exists():
            print(f"Removing stale copy of {external_dir}...")
            shutil.rmtree(external_dir)

        print(f"Cloning fresh imagery_utils into {external_dir}...")
        subprocess.run(["git", "clone", REPO_URL, str(external_dir)], check=True)
    else:
        print(f"{external_dir} is up to date (less than {max_age_days} days old). Skipping clone...")

# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    try:
        base_dir = Path(__file__).resolve().parent.parent
    except NameError:
        # For interactive environments or if __file__ is not available
        base_dir = Path(os.getenv("PROJECT_ROOT", Path.cwd()))

    external_dir = base_dir / "external" / "imagery_utils"

    clone_imagery_utils(external_dir)

    sys.path.append(str(external_dir))
    import pgc_ortho