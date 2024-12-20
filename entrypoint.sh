#!/bin/bash

set -e

# Activate the conda environment
source /opt/conda/etc/profile.d/conda.sh
conda activate gaia

python manage.py makemigrations

# Apply database migrations
echo "Applying database migrations"
python manage.py migrate

# Collect static files
echo "Collecting static files"
python manage.py collectstatic --noinput

# Start server
echo "Starting server"
exec "$@"
