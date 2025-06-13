# This Dockerfile sets up a Django application with Spatialite support using Miniconda
#
# - Uses miniconda3 as the base image
# - Installs system dependencies including spatialite, sqlite3, and gdal
# - Creates a non-root user 'vmuser' for security
# - Sets up a conda environment from environment.yml
# - Configures Spatialite integration with Django
# - Sets up directories for secrets and data volume mounting
# - Uses gunicorn as the application server
# - Uses whitenoise for static file serving
#
# Environment variables:
# - SPATIALITE_LIBRARY_PATH=mod_spatialite.so
# - CONDA_DEFAULT_ENV=gaia
#
# Exposed ports:
# - 8000
#
# Volumes:
# - /mnt/secrets: For application secrets
# - /mnt/data: For SQLite database
#
# The application runs as non-root user 'vmuser' for security
# Entrypoint runs any initialization scripts
# Default CMD runs gunicorn server on port 8000

# Use an official miniconda image as a parent image
FROM continuumio/miniconda3:latest

ARG BUILD_DATE
LABEL org.opencontainers.image.created=$BUILD_DATE

# env variables
ENV SPATIALITE_LIBRARY_PATH=mod_spatialite.so

# Install dependencies
RUN apt-get update && apt-get install -y \
    openssl \
    libsqlite3-mod-spatialite \
    sqlite3  \
    gdal-bin \
    gdal-plugins \
    nano \
    faker \
    binutils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN groupadd -r vmuser && \
    useradd -r -g vmuser -m vmuser

# create conda env and install dependencies
COPY environment.yml .
RUN conda env create -f environment.yml && \
    conda clean -a

# Activate the conda environment
ENV CONDA_DEFAULT_ENV=gaia
ENV PATH=/opt/conda/envs/$CONDA_DEFAULT_ENV/bin:$PATH

# Set up Spatialite
RUN mkdir -p /etc/sqlite && \
    echo ".load /usr/lib/mod_spatialite.so" > /etc/sqlite/sqlite3.conf && \
    echo "SELECT load_extension('mod_spatialite');" > /etc/sqlite/spatialite.init

# Set application directory
WORKDIR /app
COPY . /app

RUN chmod +x entrypoint.sh

RUN mkdir -p logs

# Change ownership of the application directory to the non-root user
RUN chown -R vmuser:vmuser /app && \
    chown -R vmuser:vmuser /etc/sqlite

# Ensure Spatialite extension loads with Django's database connection
RUN sed -i 's/ENGINE": "django.db.backends.sqlite3/ENGINE": "django.contrib.gis.db.backends.spatialite/' /app/gaia/settings.py

# Install gunicorn
RUN conda install -y gunicorn

# Install whitenoise to serve static files with gunicorn (not for production)
RUN conda install -c conda-forge whitenoise

# Create directories for secrets and data volumes so Azure will mount them
RUN mkdir -p /mnt/secrets
RUN mkdir -p /mnt/data

# Add symbolic links to secrets and database file if they don't exist
RUN [ -e /app/gaia/secrets.json ] || ln -s /mnt/secrets/secrets-json /app/gaia/secrets.json
RUN [ -e /app/db.sqlite3 ] || ln -s /mnt/data/db.sqlite3 /app/db.sqlite3
# expose port 8000 for external access
EXPOSE 8000

# Switch to the non-root user
USER vmuser

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/bin/bash", "-c", "source activate gaia && gunicorn gaia.wsgi:application --bind 0.0.0.0:8000"]
