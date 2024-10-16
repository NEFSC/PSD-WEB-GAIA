import os
import time
import subprocess
from django.conf import settings
from django.core.management.base import BaseCommand

REPO_URL = "https://github.com/PolarGeospatialCenter/imagery_utils.git"
REPO_DIR = os.path.join(settings.BASE_DIR, 'imagery_utils')
CHECK_INTERVAL = 2_624_016 # One month in seconds

class Command(BaseCommand):
    help = "Clone the Polar Geospatial Center's repository on first server run and periodically check for updates"

    def handle(self, *args, **kwargs):
        if not os.path.exists(REPO_DIR):
            self.clone_repo()
        else:
            self.pull_repo()

        while True:
            time.sleep(CHECK_INTERVAL)
            self.pull_repo()

    def clone_repo(self):
        """ Close the PGC repository from GitHub if it is not already downloaded."""
        try:
            self.stdout.write(f"Cloning repository {REPO_URL} into {REPO_DIR}...")
            subprocess.check_call(['git', 'clone', REPO_URL, REPO_DIR])
            self.stdout.write(self.style.SUCCESS('Repository cloned successfully.'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"Error cloning repository: {e}"))

    def pull_repo(self):
        """ Pull the latest changes from the repository."""
        try:
            self.stdout.write(f"Checking for updates in {REPO_DIR}...")
            result = subprocess.check_output(['git', '-C', REPO_DIR, 'pull'], stderr=subprocess.STDOUT)
            if "Already up to date" in result.decode('utf-8'):
                self.stdout.write(self.style.SUCCESS('No updates available.'))
            else:
                self.stdout.write(self.style.SUCCESS('Repository updated.'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"Error pulling updates: {e}"))