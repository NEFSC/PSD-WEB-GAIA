#!/bin/bash

set -e

# Activate the conda environment
source /opt/conda/etc/profile.d/conda.sh
conda activate gaia

# Unapply all migrations for the whale app
echo "Unapplying all migrations for the whale app"
python manage.py migrate whale zero

# Create new migrations
echo "Creating new migrations"
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
