# Use an official Anaconda image as a parent image
FROM continuumio/anaconda3:latest

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install OpenSSL system-wide
RUN apt-get update && apt-get install -y openssl libsqlite3-mod-spatialite libgdal-dev libgeos-dev


ENV SPATIALITE_LIBRARY_PATH=/opt/conda/envs/gaia/lib/mod_spatialite.so

# Install Django and Gunicorn in the Anaconda environment
RUN conda install -y django gunicorn

# Create the environment using the environment.yml file
COPY environment.yml .
RUN conda install -n base -c conda-forge mamba && mamba env create -f environment.yml

# Activate the environment
ENV PATH /opt/conda/envs/gaia/bin:$PATH
RUN echo "conda init && conda activate gaia" > ~/.bashrc
ENV CONDA_DEFAULT_ENV gaia

# Install Nginx
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

# Copy the Nginx configuration file to the container
COPY nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /app/logs

# Collect static files (optional, depending on Django settings)
RUN python manage.py collectstatic --noinput

# Expose port 80 for external access
EXPOSE 80

# Run Gunicorn and start Nginx
CMD ["sh", "-c", "gunicorn gaia.wsgi:application --bind 0.0.0.0:8000 --timeout 120 & nginx -g 'daemon off;'"]
