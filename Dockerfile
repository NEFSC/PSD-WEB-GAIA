# Use an official Anaconda image as a parent image
FROM continuumio/miniconda3:latest

# env variables
ENV SPATIALITE_LIBRARY_PATH=mod_spatialite.so

# Install dependencies
RUN apt-get update && apt-get install -y openssl libsqlite3-mod-spatialite sqlite3 gdal-bin binutils nginx binutils

# create conda env and install dependencies
COPY environment.yml .
RUN conda env create -f environment.yml && \
    conda clean -a

# Activate the conda environment
ENV CONDA_DEFAULT_ENV gaia
ENV PATH /opt/conda/envs/$CONDA_DEFAULT_ENV/bin:$PATH

# Set up Spatialite
RUN mkdir -p /etc/sqlite && \
    echo ".load /usr/lib/mod_spatialite.so" > /etc/sqlite/sqlite3.conf && \
    echo "SELECT load_extension('mod_spatialite');" > /etc/sqlite/spatialite.init

# Set application directory
WORKDIR /app
COPY . /app

# Copy the Nginx configuration file to the container
COPY nginx.conf /etc/nginx/nginx.conf

# Ensure Spatialite extension loads with Django's database connection
RUN sed -i 's/ENGINE": "django.db.backends.sqlite3/ENGINE": "django.contrib.gis.db.backends.spatialite/' /app/gaia/settings.py

# expose port 8000 for Gunicorn
EXPOSE 8000

# Run migrations and collect static files
#RUN conda run -n gaia python manage.py migrate
RUN conda run -n gaia python manage.py

# Start Gunicorn and Nginx
CMD ["bash", "-c", "source activate gaia && (gunicorn myproject.wsgi:application --bind 0.0.0.0:8000 &) && nginx -g 'daemon off;'"]
#CMD ["conda", "run", "-n", "myenv", "bash", "-c", "(gunicorn myproject.wsgi:application --bind 0.0.0.0:8000 &) && nginx -g 'daemon off;'"]
