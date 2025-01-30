# Basic stack
import os
import sys
import json
import shutil
import requests
import datetime
from datetime import datetime, timedelta
import subprocess
from time import time
from glob import glob
from wsgiref.util import FileWrapper

# Geospatial Stack
from pyproj import CRS, Transformer
from osgeo import gdal
from osgeo_utils.gdal_pansharpen import gdal_pansharpen
from shapely import to_geojson
from shapely.geometry import box, Point, Polygon
from fiona.drvsupport import supported_drivers
import pandas as pd
import geopandas as gpd

# Azure stack
from azure.core.credentials import AzureNamedKeyCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_blob_sas, BlobSasPermissions

# Django stack
import django
from django.core.cache import cache
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.db.models.functions import Transform
from django.contrib.sessions.models import Session
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.shortcuts import render, redirect, get_object_or_404
from django_q.tasks import async_task
from django.views import View

# GAIA stack
from ..security import ee_login, mgp_login
from ..models import AreaOfInterest, PointsOfInterest, EarthExplorer, GEOINTDiscovery, MaxarGeospatialPlatform, ExtractTransformLoad, BlindReviews
from ..forms import APIQueryForm, ProcessingForm, PointsOfInterestForm
from ..tasks import process_etl_data
from ..query import build_ee_query_payload, query_mgp
from ..download import download_imagery
from ..utils import get_entity_pairs, standardize_names, calibrate_image, import_pois, upload_to_auzre  # should be depricated: convert_to_tiles

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaia.settings')
os.environ["CPL_DEBUG"] = "ON" # Should enable GDAL debuggin
django.setup()

def processing_page(request):
    """ A page for preprocessing satellite imagery. Data are selected from records within
            the database by an end-user to preprocess. Preprocessing steps include
            orthorectification, calibration, super-sampling, converted to
            Cloud Optimized GeoTIFFs (COGs), and uploaded to Azure.

        TODO: Support preprocessing for more than just USGS's EarthExplorer 'crssp_orderable_w3'
            data repository (GAIFAGP-56)
        TODO: Remove GDAL2Tiles implimentation for RIOCOGEO COG creation (GAIFAGP-57)
        TODO: Execute these steps asynchronously (GAIFAGP-58, GAIFAGP-59)
        TODO: Properly integrate generate_interesting_points.py to include not only point
            generation, but their registration within the database (GAIFAGP-60)
        TODO:
            Add newly downloaded file to the ETL table.
            Add newly calibrated file to the ETL table.
            Superceed "geotiffs = glob("../data/**/*.tif", recursive=True)" section after adding above.
                 This would replace the need for identifying calibrated pansharpened and multispectral
                 imagery.
            Add newly pansharpened file to the ETL table.
            Add newly identified points files (GeoJSON, SHP) to the ETL table.
            Support moving files off virtual machine to Azure with file management.
    """
    form = ProcessingForm()
    filtered_data = None

    print("\nREQUEST API: ", request.POST, '\n\n')        
    
    if request.method == 'POST':
        if 'username' in request.POST and 'password' in request.POST:
            # Handle credentials
            username = request.POST['username']
            password = request.POST['password']
            entity_ids = request.POST.getlist('entity_ids')

            print("\n\nYour USERNAME is: ", username,)
            print("Your PASSWORD is: ", password,)
            print("Entity IDs: ", entity_ids, '\n\n')

            # Check Entity IDs have their PAN, MSI pairs
            if entity_ids:
                session = requests.Session()
                session = ee_login(session, username, password)

                list_of_pairs = [get_entity_pairs(entity_id) for entity_id in entity_ids]
                print(f"Your list of pairs: {list_of_pairs}")

                for pair in list_of_pairs:
                    try:
                        unzipped_dirs = []
                        print(f"Your pair looks like: {pair}")
                        for pan_entity_id, msi_entity_id in pair.items():
                            print(f"Your PAN entity id is: {pan_entity_id}, your MSI entity id is: {msi_entity_id}")
                            
                            start = time()
                            unzipped_dirs.append(download_imagery(session, 'crssp_orderable_w3', pan_entity_id))
                            print(f"\n It took: {round(time() - start,2)} seconds to download and unzip {pan_entity_id}, your panchromatic image \n")
    
                            start = time()
                            unzipped_dirs.append(download_imagery(session, 'crssp_orderable_w3', msi_entity_id))
                            print(f"\n It took: {round(time() - start,2)} seconds to download and unzip {msi_entity_id}, your multispectral image \n")
    
                        # BLOCK THIS OUT WHEN DEBUGGING
                        # Upload these retrieved files to Azure
                        # for unzipped_dir in unzipped_dirs:
                        #     start = time()
                        #     # Get all files from within the unzipped directory, less the license files
                        #     unzipped_files = glob(unzipped_dir + '/**/*.*', recursive=True)
                        #     filtered_files = [file for file in unzipped_files if 'license' not in file]
                            
                        #     # Determine the image directory name
                        #     dir_name = filtered_files[0].replace('\\', '/').split('/')[-2].split('.')[0]
                        #     # Upload files to Azure
                        #     for file in filtered_files:
                        #         print(f"Uploading: {file}")
                        #         upload_to_auzre(file, f'data/imagery/ee/{dir_name}', '')
                        #     print(f"\n It took: {round(time() - start,2)} seconds to upload {dir_name}, a full directory, to Azure \n\n")
    
                        # Standarize file names and calibrate images
                        print(f"Your unzipped directories looks like: {unzipped_dirs}")
                        for unzipped_dir in unzipped_dirs:
                            print(f"Your unzipped dir looks like: {unzipped_dir}")
                            
                            start = time()
                            # Only use this to get the dir name again
                            unzipped_files = glob(unzipped_dir + '/**/*.*', recursive=True)
                            print(f"Successfully executed glob: {unzipped_files}")
                            filtered_files = [file for file in unzipped_files if 'license' not in file]
                            print("Successfully removed license related files")
                            dir_name = filtered_files[0].replace('\\', '/').split('/')[-2].split('.')[0]
                            print(f"Successfully found dir name: {dir_name}")

                            try:
                                standard_name_geotiff = standardize_names(unzipped_dir)
                            except Exception as e:
                                standard_name_geotiff = unzipped_dir
                                print(f"Failed standardizing names with Exception: {e}.\n\tTrying to move along...")
                            print("Begining to calibrate the image...")
                            calibrated_image = calibrate_image(standard_name_geotiff)
                            print(f"\n It took: {round(time() - start,2)} seconds to calibrate {dir_name} \n")
    
                        # Upload these calibrated files to Azure
                        calibrated_images = []
                        for unzipped_dir in unzipped_dirs:
                            start = time()
                            unzipped_files = glob(unzipped_dir + '/**/*.*', recursive=True)
                            calibrated_files = [file for file in unzipped_files if 'calibrated' in file]
                            
                            for file in calibrated_files:
                                if 'tif' in file:
                                    calibrated_images.append(file)
                                dir_name = file.replace('\\', '/').split('/')[-1].split('.')[0]
                                upload_to_auzre(file, f'data/imagery/calibrated/{dir_name}', '')
    
                            print(f"\n Your calibrated image name is: {calibrated_image} \n")
                            print(f"\n It took: {round(time() - start,2)} seconds to upload your calibrated image to Azure \n")
    
                        # Create a pansharpened image
                        start = time()
                        for calibrated_image in calibrated_images:
                            if 'P1BS' in calibrated_image:
                                pan_image = calibrated_image
                            elif 'M1BS' in calibrated_image:
                                msi_image = calibrated_image
                            else:
                                print("\n\nYOUR IMAGE DOES NOT FOLLOW THE STANDARD NAMING CONVENTION FOR MAXAR\n\n")
    
                        shrp_image = pan_image.split('/')[-1].replace('P1BS', 'S1BS')
                        print(f"YOUR SHARP IMAGE IS: {shrp_image}")
                        gdal_pansharpen(['' ,'-b', '5', '-b', '3', '-b', '2', '-r', 'cubic', '-threads', 'ALL_CPUS', pan_image, msi_image, shrp_image])
                        print(f"\n It took: {round(time() - start,2)} seconds to create a pansharpened image \n")
    
                        # Upload this panchromatic file to Azure
                        start = time()
                        upload_to_auzre(shrp_image, f'data/imagery/panchromatic/{dir_name}', '')
                        print(f"\n It took: {round(time() - start,2)} seconds to upload your panchromatic image to Azure \n")
    
                        # Generate interesting point catalog
                        start = time()
                        try:
                            out_geojson = shrp_image.replace('tif', 'geojson')
                            subprocess.run(['python', 'manage.py', 'generate_points', '--input-file', shrp_image, '--output-file', out_geojson, '--method', 'big_window', '--difference', '20'], check=True, capture_output=True, text=True)
                            print("Subprocess output:", result.stdout)
                        except subprocess.CalledProcessError as e:
                            print("Subprocess failed with return code:", e.returncode)
                            print("Error output:", e.stderr)
                        print(f"\n It took: {round(time() - start,2)} seconds to generate interesting points: {out_geojson} \n")
    
                        # Upload the interesting point catalog to Azure
                        upload_to_auzre(out_geojson, 'json', 'application/geo+json')
    
                        # Add interesting points to database
                        start = time()
                        import_pois(out_geojson)
                        print(f"\n It took: {round(time() - start,2)} seconds to register your interesting point catalog in the database \n")
    
                        # # DON'T INCLUDE THIS FOR QA/QC
                        # # Oversample pansharpened images
                        # start = time()
                        # ultratiff = '.'.join(shrp_image.split('.')[:-1]) + "_ultra.tif"
                        # options = "-overwrite -multi -wm 80% -tr 0.13 0.13 -r cubic -co BIGTIFF=IF_SAFER -co NUM_THREADS=ALL_CPUS -co compress=lzw"
                        # output_dataset = gdal.Warp(ultratiff, shrp_image, format="COG", options=options)
                        # output_dataset = None
                        # print(f"\n It took: {round(time() - start,2)} seconds to oversampled your image: {ultratiff} \n")
    
                        # # Upload the oversampled image to Azure
                        # start = time()
                        # upload_to_auzre(ultratiff, 'json', '')
                        # print(f"\n It took: {round(time() - start,2)} seconds to upload your oversampled image to Azure \n")
    
                        # Generate Cloud Optimized GeoTIFF
                        start = time()
                        cogtiff = shrp_image.replace('.tif', '_cog.tif')
                        subprocess.run(['rio', 'cogeo', 'create', '--zoom-level', '20', '--overview-resampling', 'cubic', '-w', shrp_image, cogtiff])
                        print(f"\n It took: {round(time() - start,2)} seconds to create your COG: {cogtiff} \n")
    
                        # Upload the COG image to Azure
                        start = time()
                        upload_to_auzre(cogtiff, 'data/cog', '')
                        print(f"\n It took: {round(time() - start,2)} seconds to upload your COG image to Azure \n")
    
                        try:
                            for unzipped_dir in unzipped_dirs:
                                shutil.rmtree(unzipped_dir)
                        except:
                            print("Unable to detele unzipped directories")
                        try:
                            os.remove(shrp_image)
                        except:
                            print("Unable to remove sharpened image")
                        try:
                            os.remove(out_geojson)
                        except:
                            print("Unable to remove GeoJSON file")
                        try:
                            os.remove(cogtiff)
                        except:
                            print("Unable to remove cog")
                        print("Done carrying out garbage collection.")
                        
                    except Exception as e:
                        print(f"Failed on {pair} with Exception: {e}")
                        
                # entities = [entity for record_list in entities for entity in record_list]
                # print(f"2. Your entities are: {entities}")
                # if len(entities) > len(entity_ids):
                #     print(f"Your list of entity ids has increased from {len(entity_ids)}! It is now {len(entities)} records in size. This will increase the processing time")
                #     entity_ids = entities
                # else:
                #     print("No additional entity ids were identified for your list. Proceeding as expected...")

            # Download and unzip imagery
            # unzipped_dirs = []
            # for entity_id in entity_ids:
            #     try:
            #         start = time()
                    
            #         unzipped_dirs.append(download_imagery(session, 'crssp_orderable_w3', entity_id))
            #         messages.success(request, f'Done downloading {entity_id}')
                    
            #         print(f"\n\n IT TOOK: {round(time() - start,2)} SECONDS TO DOWNLOAD {entity_id} \n\n")
            #     except Exception as e:
            #         print(f"FAILED DOWNLOADING {entity_id} WITH EXCEPTION {e}")

            # Upload files to Azure, standarize names
            # standard_name_geotiffs = []
            # for unzipped_dir in unzipped_dirs:
            #     try:
            #         start = time()
                    
            #         unzipped_files = glob(unzipped_dir + '/**/*.*', recursive=True)
            #         filtered_files = [file for file in unzipped_files if 'license' not in file]
            #         print(f"YOUR FILTERED FILES: {filtered_files}")
                    
            #         dir_name = filtered_files[0].replace('\\', '/').split('/')[-2].split('.')[0]
            #         for file in filtered_files:
            #             print(f"Uploading: {file}")
            #             upload_to_auzre(file, f'data/imagery/ee/{dir_name}', '')
                        
            #         print(f"\n\n IT TOOK: {round(time() - start,2)} SECONDS TO UPLOAD {entity_id} TO AZURE \n\n")
                    
            #         standard_name_geotiffs.append(standardize_names(unzipped_dirs))
            #     except Exception as e:
            #         print(f"FAILED UPLOADING {unzipped_dir} WITH EXCEPTION {e}")

            # Calibrate images and upload them to Azure
            #      Only upload the GeoTIFF opposed to it and many other supporting files
            #      like Log, Prj, and XML.
            # for standard_name_geotiff in standard_name_geotiffs:
            #     try:
            #         start = time()
            #         calibrated_image = calibrate_image(standard_name_geotiff)
            #         print(f"\n\n IT TOOK: {round(time() - start,2)} SECONDS TO CALIBRATE {entity_id} \n\n")

            #         start = time()
            #         #unzipped_files = glob(unzipped_dirs + '/**/*.*', recursive=True)
            #         #calibration_files = [file for file in unzipped_files if 'calibrated' in file]
            #         # print(f"YOUR FILTERED FILES: {filtered_files}")
            #         # for file in calibration_files:
            #         #     print(f"Uploading: {file}")
            #         #     upload_to_auzre(file, f'data/imagery/calibrated/{dir_name}', '')
            #         print(f"YOUR CALIBRATED FILE IS: {calibrated_image}")
            #         upload_to_auzre(standard_name_geotiff, f'data/imagery/calibrated/{dir_name}', '') # dir_name = variable abuse
                        
            #         print(f"\n\n IT TOOK: {round(time() - start,2)} SECONDS TO UPLOAD CALIBRATED DATA TO AZURE \n\n")
            #     except Exception as e:
            #         print(f"FAILED UPLOADING {standard_name_geotiff} WITH EXCEPTION {e}")


                # If we use a database, this section wont be needed.
                #      There would need to be support for the virtual
                #      machine determining which images haven't gone
                #      through the following step.
                # geotiffs = glob("../data/**/*.tif", recursive=True)
                # print(f"Your geotiff list is: {geotiffs}")
                # calibrated_geotiffs = [geotiff for geotiff in geotiffs if 'calibrated' in geotiff]
                # calibrated_panchromatic_images = [calibrated_geotiff for calibrated_geotiff in calibrated_geotiffs if 'P1BS' in calibrated_geotiff]
                # print(f"Your {len(calibrated_panchromatic_images)} calibrated panchromatic image(s) are: {calibrated_panchromatic_images}")                    

                # Continue preprocessing pipeline
                # for pantiff in calibrated_panchromatic_images:
                #     try:
                #         panfile = pantiff.split('\\')[-1]
                #         print(f"Your pan file name is {panfile}")
                #         msifile = panfile.replace('P1BS', 'M1BS')
                #         print(f"Your msi file name is {msifile}")
                        
                #         msitiff = [geotiff for geotiff in geotiffs if msifile in geotiff][0]

                #         # Pansharpen calibrated images
                #         start = time()
                #         shrptiff = '../data/' + pantiff.split('\\')[-1].replace('P1BS', 'S1BS')
                #         gdal_pansharpen(['' ,'-b', '5', '-b', '3', '-b', '2', '-r', 'cubic', '-threads', 'ALL_CPUS', pantiff, msitiff, shrptiff])
                #         print(f"\n\n IT TOOK: {round(time() - start,2)} SECONDS TO PANSHARPEN {shrptiff} \n\n")
                        
                        # start = time()
                        # upload_to_auzre(shrptiff, 'cogs', 'image/tiff')
                        # print(f"\n\n IT TOOK: {round(time() - start,2)} SECONDS TO UPLOAD YOUR PANSHARPEN IMAGE TO AZURE \n\n")

                        # Generate interesting point catalog
                        # start = time()
                        # out_geojson = shrptiff.replace('tif', 'geojson')
                        # subprocess.run(['python', 'manage.py', 'generate_points', '--input-file', shrptiff, '--output-file', out_geojson, '--method', 'big_window', '--difference', '20'])
                        # print(f"\n\n IT TOOK: {round(time() - start,2)} SECONDS TO GENERATE INTERESTING POINTS {out_geojson} \n\n")
                        
                        # upload_to_auzre(out_geojson, 'json', 'application/geo+json')
                        
                        # Generate Shapefile for secondary validation - Probably don't need this
                        # gdf = gpd.read_file(out_geojson)
                        # output_shp = out_geojson.replace('geojson', 'shp')
                        # gdf.to_file(output_shp)

                        # Add interesting points to database
                        # start = time()
                        # import_pois(out_geojson)
                        # print(f"\n\n IT TOOK: {round(time() - start,2)} SECONDS TO REGISTER INTERESTING POINTS IN YOUR DATABASE \n\n")

                        # # Oversample pansharpened images
                        # start = time()
                        # ultratiff = '.'.join(shrptiff.split('.')[:-1]) + "_ultra.tif"
                        # options = "-overwrite -multi -wm 80% -tr 0.13 0.13 -r cubic -co BIGTIFF=IF_SAFER -co NUM_THREADS=ALL_CPUS"
                        # output_dataset = gdal.Warp(ultratiff, shrptiff, format="COG", options=options)
                        # output_dataset = None
                        # print(f"\n\n IT TOOK: {round(time() - start,2)} SECONDS TO PROCESS FROM DOWNLOAD TO {ultratiff} \n\n")
    
                        # # Generate Cloud Optimized GeoTIFF
                        # cogtiff = ultratiff.replace('_ultra.tif', '_cog.tif')
                        # subprocess.run(['rio', 'cogeo', 'create', '--zoom-level', '20', '--overview-resampling', 'cubic', '-w', ultratiff, cogtiff])

                        # QA/QC Test
                        # start = time()
                        # cogtiff = shrptiff.replace('.tif', '_cog.tif')
                        # subprocess.run(['rio', 'cogeo', 'create', '--zoom-level', '20', '--overview-resampling', 'cubic', '-w', shrptiff, cogtiff])
                        # print(f"\n\n IT TOOK: {round(time() - start,2)} SECONDS TO GENERATE COG {cogtiff} \n\n")

                        # Upload to Azure
                        # start = time()
                        # upload_to_auzre(cogtiff, 'cogs', 'image/tiff')
                        # print(f"\n\n IT TOOK: {round(time() - start,2)} SECONDS TO UPLOAD YOUR PANSHARPEN IMAGE TO AZURE \n\n")

                        # Garbage collection
                        #      Leaves the original, uncalibrated and calibrated images locally
                        # if os.path.exists(shrptiff):
                        #     os.remove(shrptiff)
                        #     print(f"Successfully deleted {shrptiff} from local machine.")
                        # else:
                        #     print(f"The file {shrptiff} does not exist.")
                        
                        # if os.path.exists(out_geojson):
                        #     os.remove(out_geojson)
                        #     print(f"Successfully deleted {out_geojson} from local machine.")
                        # else:
                        #     print(f"The file {out_geojson} does not exist.")

                        # # Comment this out when troubleshooting
                        # if os.path.exists(ultratiff):
                        #     os.remove(ultratiff)
                        #     print(f"Successfully deleted {ultratiff} from local machine.")
                        # else:
                        #     print(f"The file {ultratiff} does not exist.")
                            
                #     except Exception as e:
                #         print(f"FAILED WITH EXCEPTION {e}. Moving along?!...")

                # files = glob('../data/**/*.*', recursive=True)
                # for file in files:
                #     os.remove(file)
                #     print(f"Successfully deleted {ultratiff} from local machine.")

                # for root, dirs, files in os.walk('../data/', topdown = False):
                #     for dir_name in dirs:
                #         dir_path = os.path.join(root, dir_name)
                #         print(f"Removing directory: {dir_path}")
                #         shutil.rmtree(dir_path)
                
                messages.success(request, 'Completed imagery retrieval and pre-processing')

            else:
                messages.error(request, 'No data selected for download.')

            return render(request, 'processing_page.html', {'form': form})       
        
        elif 'filter' in request.POST:
            form = ProcessingForm(request.POST)
            if form.is_valid():
                filtered_data = ExtractTransformLoad.objects.all()
                # print("\n\nUnfiltered data: ", filtered_data, '\n\n')
                if form.cleaned_data['table_name']:
                    filtered_data = filtered_data.filter(table_name = form.cleaned_data['table_name'])
                if form.cleaned_data['id']:
                    filtered_data = filtered_data.filter(id = form.cleaned_data['id'])
                if form.cleaned_data['vendor_id']:
                    filtered_data = filtered_data.filter(vendor_id = form.cleaned_data['vendor_id'])
                if form.cleaned_data['entity_id']:
                    filtered_data = filtered_data.filter(entity_id = form.cleaned_data['entity_id'])
                if form.cleaned_data['vendor']:
                    filtered_data = filtered_data.filter(vendor = form.cleaned_data['vendor'])
                if form.cleaned_data['platform']:
                    filtered_data = filtered_data.filter(platform = form.cleaned_data['platform'])
                if form.cleaned_data['pixel_x_min']:
                    filtered_data = filtered_data.filter(pixel_x_min = form.cleaned_data['pixel_x_min'])
                if form.cleaned_data['pixel_x_max']:
                    filtered_data = filtered_data.filter(pixel_x_max = form.cleaned_data['pixel_x_max'])
                if form.cleaned_data['pixel_y_min']:
                    filtered_data = filtered_data.filter(pixel_y_min = form.cleaned_data['pixel_y_min'])
                if form.cleaned_data['pixel_y_max']:
                    filtered_data = filtered_data.filter(pixel_y_max = form.cleaned_data['pixel_y_max'])
                if form.cleaned_data['date_min']:
                    filtered_data = filtered_data.filter(date__gte = form.cleaned_data['date_min'])
                if form.cleaned_data['date_max']:
                    filtered_data = filtered_data.filter(date__lte = form.cleaned_data['date_max'])
                if form.cleaned_data['publish_date_min']:
                    filtered_data = filtered_data.filter(publish_date__gte = form.cleaned_data['publish_date_min'])
                if form.cleaned_data['publish_date_max']:
                    filtered_data = filtered_data.filter(publish_date__lte = form.cleaned_data['publish_date_max'])
                if form.cleaned_data['aoi']:
                    try:
                        aoi_geom =  GEOSGeometry(form.cleaned_data['aoi'].geometry)
                    except (ValueError, TypeError) as e:
                        aoi_geom = None
                        #print(f"Error loading AOI geometry: {e}")

                    intersecting_data = []

                    for etl in filtered_data:
                        #print(etl.geometry)
                        try:
                            geom = GEOSGeometry(etl.geometry)
                            if geom.intersects(aoi_geom):
                                intersecting_data.append(etl)
                        except (ValueError, TypeError) as e:
                            print(f"Error loading geometry for ETL ID {etl.id}: {e}")

                    filtered_data = intersecting_data
                    #print("\n\nFiltered data: ", filtered_data, '\n\n')

                geojson_data = [
                {
                    'id': etl.id,
                    'geometry': GEOSGeometry(etl.geometry).geojson,
                    'vendor_id': etl.vendor_id,
                    'entity_id': etl.entity_id,
                    'vendor': etl.vendor,
                    'platform': etl.platform,
                    'date': etl.date,
                    'publish_date': etl.publish_date,
                    'pixel_size_x': etl.pixel_size_x,
                    'pixel_size_y': etl.pixel_size_y,
                }
                    for etl in filtered_data
                ]

                #print("\n\nGEOJSON data: ", geojson_data, '\n\n')
                
                return render(request, 'processing_page.html', {'form': form, 'filtered_data': geojson_data})
                
        elif 'process' in request.POST:
            selected_ids = request.POST.getlist('select_images')
            if selected_ids:
                user_email = request.user.email
                task_id = async_task('whale.tasks.process_etl_data', filtered_data)
                return render(request, 'processing_page.html', {'task_id': task_id})
  
    return render(request, 'processing_page.html', {'form': form})

