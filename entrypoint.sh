#!/bin/bash

set -e

# Activate the conda environment
source /opt/conda/etc/profile.d/conda.sh
conda activate gaia

# Function to delete migration files
delete_migrations() {
    # Delete all .py files in migrations directories except __init__.py
    find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
    # Delete all .pyc files in migrations directories
    find . -path "*/migrations/*.pyc" -delete
}

# Function to reset the database
reset_database() {
    # Remove the SQLite database file
    rm -f db.sqlite3
}

# Delete migration files
#echo "Deleting migration files"
#delete_migrations

# Reset the database
#echo "Resetting the database"
#reset_database

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
