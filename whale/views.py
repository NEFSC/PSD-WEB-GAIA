# Basic stack
import os
import sys
import json
import requests
import datetime
from datetime import datetime, timedelta
import subprocess
from time import time
from glob import glob
from wsgiref.util import FileWrapper

# Security stack
import hmac
import hashlib
import base64

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
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

# Django stack
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
from .security import ee_login, mgp_login
from .models import AreaOfInterest, PointsOfInterest, EarthExplorer, GEOINTDiscovery, MaxarGeospatialPlatform, ExtractTransformLoad
from .forms import APIQueryForm, ProcessingForm, PointsOfInterestForm
from .tasks import process_etl_data
from .query import build_ee_query_payload, query_mgp
from .download import download_imagery
from .utils import standardize_names, calibrate_image, convert_to_tiles, get_entity_pairs, import_pois, convert_date_or_none


########################################################################################################################
#
#  In Django, a view is what takes a Web request and returns a Web response. The response can be many things, but most
#  of the time it will be a Web page, a redirect, or a document. In this case, the response will almost always be data
#  in JSON format.
#
########################################################################################################################


def login_view(request):
    """ A simple log-in page meeting NOAA OCIO's security requirement for
            a username and password protecting restricted access
            satellite imagery.
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('landing_page')
    else:
        form = AuthenticationForm()
        
    return render(request, 'login.html', {'form': form})

def landing_page(request):
    """ A basic landing page for the WHale Active Learning Environment (WHALE)
            Tasking, Collection, Processing, Exploitation, and Dissimination
            (TCPED) pages. Each TCPED task has its own page linked to this
            one.
    """
    return render(request, 'landing_page.html')

def tasking_page(request):
    """ A simple page to show where Areas of Interest (AOIs) currently loaded
            in the SpatiaLite database are within the world.
    """
    aoi_objects = AreaOfInterest.objects.all()
    aoi_data = serialize('geojson', aoi_objects)
    aoi_data = json.loads(aoi_data)

    flattended_aoi_data = []
    for feature in aoi_data['features']:
        flattended_aoi_data.append({
            'id': feature['id'],
            'name': feature['properties']['name'],
            'requestor': feature['properties']['requestor'],
            'sqkm': feature['properties']['sqkm'],
            'geometry': feature['geometry'],
        })
    
    return render(request, 'tasking_page.html', {
        'aoi_data': flattended_aoi_data,
        'geojson_aoi_data': aoi_data
    })

def collection_page(request):
    """ A page for consolidated review of satellite imagery collected over
            loaded areas of interest and registration of these images into
            the SpatiaLite database for processing.

        Currently supports USGS EarthExplorer, NGA GEOINT Discovery, and
            Maxar Geospatial Platform satellite imagery repositories.

        TODO: Split each data repository into a function (GAIFAGP-55).
    """
    results = None
    message = None
    geometry = None
    results_geojson = None
    aoi_bounds = None

    if request.method == 'POST':
        form = APIQueryForm(request.POST)

        # Print API selected to terminal for troubleshooting
        print("\n\REQUEST API: ", request.POST.get('select_api'), '\n\n')

        # Post back to SpatiaLite database if there were selections
        if 'selected' in request.POST:
            # Create a dictionary from the POST
            row_data = {}
            for key in request.POST:
                if key.startswith('row_data_'):
                    row_id = key.split('_')[2]
                    if row_id not in row_data:
                        row_data[row_id] = []
                    row_data[row_id].append(request.POST[key])

            # Print it to terminal
            print("\n\ROW DATA: ", row_data, '\n\n')

            if request.POST.get('select_api') == 'ee':
                for attributes in row_data.values():
                    attributes = [attribute for attribute in attributes if attribute]
                    EarthExplorer.objects.update_or_create(
                        entity_id = attributes[0],
                        catalog_id = attributes[4],
                        acquisition_date = convert_date_or_none(attributes[1]),
                        vendor = attributes[2],
                        vendor_id = attributes[3],
                        cloud_cover = attributes[5],
                        satellite = attributes[6],
                        sensor = attributes[7],
                        number_of_bands = attributes[8],
                        map_projection = attributes[9],
                        datum = attributes[11],
                        processing_level = attributes[12],
                        file_format = attributes[13],
                        license_id = attributes[14],
                        sun_azimuth = attributes[15],
                        sun_elevation = attributes[16],
                        pixel_size_x = attributes[17],
                        pixel_size_y = attributes[18],
                        license_uplift_update = convert_date_or_none(attributes[19]),
                        event = attributes[20],
                        event_date = convert_date_or_none(attributes[21]),
                        date_entered = convert_date_or_none(attributes[22]),
                        center_latitude_dec = attributes[23],
                        center_longitude_dec = attributes[24],
                        thumbnail = attributes[25],
                        publish_date = attributes[26],
                        bounds = attributes[27],
                        aoi_id = get_object_or_404(AreaOfInterest, id=int(float(attributes[28])))
                    )
                    messages.success(request, f"Image ID {attributes[0]} was registered to the database successfully!")

            elif request.POST.get('select_api') == 'gegd':
                for attributes in row_data.values():
                    attributes = [attribute for attribute in attributes if attribute]

                    [print("\nATT", i , ":", attribute) for i, attribute in enumerate(attributes)]
                    try:
                        GEOINTDiscovery.objects.update_or_create(
                            id = attributes[0],
                            legacy_id = attributes[1],
                            factory_order_number = attributes[2],
                            acquisition_date = convert_date_or_none(attributes[3]),
                            source = attributes[4],
                            source_unit = attributes[5],
                            product_type = attributes[6],
                            cloud_cover = attributes[7],
                            off_nadir_angle = attributes[8],
                            sun_elevation = attributes[9],
                            sun_azimuth = attributes[10],
                            ground_sample_distance = attributes[11],
                            data_layer = attributes[12],
                            legacy_description = attributes[13],
                            color_band_order = attributes[14],
                            asset_name = attributes[15],
                            per_pixel_x = attributes[16],
                            per_pixel_y = attributes[17],
                            crs_from_pixels = attributes[18],
                            age_days = attributes[19],
                            ingest_date = convert_date_or_none(attributes[20]),
                            company_name = attributes[21],
                            copyright = attributes[22],
                            niirs = attributes[23],
                            geometry = attributes[24],
                            aoi_id = get_object_or_404(AreaOfInterest, id=int(float(attributes[25])))
                        )
                        messages.success(request, f"Image ID {attributes[0]} was registered to the database successfully!")
                    
                    except IntegrityError:
                        messages.warning(request, f"Image ID {attributes[0]} failed due to unique constraint violation." + 
                                         f" It has not been added to the database, but likely because some version of the" +
                                         f" record is already there. You should validate that is the case through the Django shell.")

            
            elif request.POST.get('select_api') == 'mgp':
                for attributes in row_data.values():
                    attributes = [attribute for attribute in attributes if attribute]
                    MaxarGeospatialPlatform.objects.update_or_create(
                        id = attributes[0],
                        platform = attributes[1],
                        instruments = attributes[2],
                        gsd = attributes[3],
                        pan_resolution_avg = attributes[4],
                        multi_resolution_avg = attributes[5],
                        datetime = attributes[6],
                        off_nadir = attributes[7],
                        azimuth = attributes[8],
                        sun_azimuth = attributes[9],
                        sun_elevation = attributes[10],
                        bbox = attributes[11],
                        aoi_id = get_object_or_404(AreaOfInterest, id=int(float(attributes[12])))
                    )
                    messages.success(request, f"Image ID {attributes[0]} was registered to the database successfully!")
            else:
                messages.warning(request, "No items were selected!")
        
        elif form.is_valid():
            api = form.cleaned_data['api']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            aoi = form.cleaned_data['aoi']
            start_date = form.cleaned_data['start_date'].strftime('%Y-%m-%d')
            end_date = form.cleaned_data['end_date'].strftime('%Y-%m-%d')

            session = requests.Session()
            geometry = json.loads(aoi.geometry.geojson)            
            aoi_bounds = aoi.geometry.buffer(0.5).extent

            if api == 'ee':
                session = ee_login(session, username, password)
                data = build_ee_query_payload(start_date, end_date, geometry)
                url = "https://m2m.cr.usgs.gov/api/api/json/stable/scene-search"
                response = session.get(url=url, data=data)
                print("Obtained a status code of: {}".format(response))

                if response.status_code == 200:
                    r = response.json()
                    message = f"Your query returned {r['data']['totalHits']} total hits, but, because of your max results threshold, you only have {r['data']['recordsReturned']} to review!\n\tTry shortening your timeframe you are querying."
    
                    # Create table from results
                    results = r['data']['results']
                    columns = [field['fieldName'] for field in results[0]['metadata']]
                    
                    gdf = gpd.GeoDataFrame(columns = columns)
                    
                    for result in results:
                        gdf.loc[gdf.shape[0]] = [field['value'] for field in result['metadata']]
                    
                    gdf['thumbnail'] = pd.Series([result['browse'][0]['thumbnailPath'] for result in results])
                    gdf['publish_date'] = pd.Series([result['publishDate'] for result in results])
                    gdf['bounds'] = gpd.GeoSeries([Polygon(result['spatialBounds']['coordinates'][0]) for result in results])
                    gdf['aoi'] = aoi.id
                    gdf = gdf.set_geometry("bounds").set_crs("EPSG:4326")
                    
                    drop_columns = [column for column in columns if "Corner" in column] + ['Center Latitude', 'Center Longitude']
                    gdf = gdf.drop(drop_columns, axis=1)
                    results_geojson = gdf.to_json()

                    results_html = f'<input type="hidden" id="api-hidden-input" name="select_api" value="{api}">'
                    results_html += '<table class="table table-striped">'
                    results_html += '<thread><tr><th><input type="checkbox" id="select-all"></th>'
                    for col in gdf.columns:
                        results_html += f'<th>{col}</th>'
                    results_html += '</tr></thread><tbody>'
    
                    for index, row in gdf.iterrows():
                        result_id = row['Entity ID']
                        results_html += '<tr>'
                        results_html += f'<td><input type="checkbox" name="selected" value="{result_id}"></td>'
                        for col in gdf.columns:
                            results_html += f'<td>{row[col]}</td>'
                        results_html += '</tr>'
                    results_html += '</tbody></table>'
                    
                    results = mark_safe(results_html)
                else:
                    print(response.status_code)
            
            elif api == 'gegd':
                connect_id = 'eb33ba21-1782-4ffc-8a5c-4854e21effb9'
                
                spatial_filter = "INTERSECTS(geometry, {})".format(aoi.geometry.wkt)
                temporal_filter = "acquisitionDate > {} AND acquisitionDate < {}".format(start_date, end_date) 
                cql_filter = ' AND '.join([spatial_filter, temporal_filter])

                url = 'https://evwhs.digitalglobe.com/catalogservice/wfsaccess'

                params = {
                    'service': 'WFS',
                    'version': '2.0.0',
                    'request': 'GetFeature',
                    'typeName': 'DigitalGlobe:FinishedFeature',
                    'outputFormat': 'application/json',
                    'connectId': connect_id,
                    'cql_filter': cql_filter
                }

                response = requests.get(url=url, params=params, auth=(username, password))
                print("Obtained a status code of: {}".format(response))

                # Error handling is really needed for GEGD more than the other APIs because of the sparse data
                try:
                    response.raise_for_status()
                    
                    r = response.json()
                    print(r)
                    message = f"Your query returned {r['totalFeatures']} total hits, but, because of your max results threshold, you only have {len(r['features'])} to review!\n\tTry shortening your timeframe you are querying."
                    
                    df = pd.DataFrame()
                    
                    for i, record in enumerate(r['features']):
                        df.loc[i, 'id'] = record['id']
                        df.loc[i, 'legacy_id'] = record['properties']['legacyId']
                        df.loc[i, 'factory_order_number'] = record['properties']['factoryOrderNumber']
                        df.loc[i, 'acquisition_date'] = record['properties']['acquisitionDate']
                        df.loc[i, 'source'] = record['properties']['source']
                        df.loc[i, 'source_unit'] = record['properties']['sourceUnit']
                        df.loc[i, 'product_type'] = record['properties']['productType']
                        df.loc[i, 'cloud_cover'] = record['properties']['cloudCover']
                        df.loc[i, 'off_nadir_angle'] = record['properties']['offNadirAngle']
                        df.loc[i, 'sun_elevation'] = record['properties']['sunElevation']
                        df.loc[i, 'sun_azimuth'] = record['properties']['sunAzimuth']
                        df.loc[i, 'ground_sampl_distance'] = record['properties']['groundSampleDistance']
                        df.loc[i, 'data_layer'] = record['properties']['dataLayer']
                        df.loc[i, 'legacy_description'] = record['properties']['legacyDescription']
                        df.loc[i, 'color_band_order'] = record['properties']['colorBandOrder']
                        df.loc[i, 'asset_name'] = record['properties']['assetName']
                        df.loc[i, 'per_pixel_x'] = record['properties']['perPixelX']
                        df.loc[i, 'per_pixel_y'] = record['properties']['perPixelY']
                        df.loc[i, 'crs_from_pixels'] = record['properties']['crsFromPixels']
                        df.loc[i, 'age_days'] = record['properties']['ageDays']
                        df.loc[i, 'ingest_date'] = record['properties']['ingestDate']
                        df.loc[i, 'company_name'] = record['properties']['companyName']
                        df.loc[i, 'copyright'] = record['properties']['copyright']
                        df.loc[i, 'niirs'] = record['properties']['niirs']
                        df.loc[i, 'geometry'] = Polygon([list(reversed(point)) for point in record['geometry']['coordinates'][0]])
                        df.loc[i, 'aoi_id'] = aoi.id
                    gdf = gpd.GeoDataFrame(df, geometry='geometry')
                    gdf = gdf.set_crs(4326)

                    results_geojson = gdf.to_json()

                    results_html = f'<input type="hidden" id="api-hidden-input" name="select_api" value="{api}">'
                    results_html += '<table class="table table-striped">'
                    results_html += '<thread><tr><th><input type="checkbox" id="select-all"></th>'
                    for col in gdf.columns:
                        results_html += f'<th>{col}</th>'
                    results_html += '</tr></thread><tbody>'
    
                    for index, row in gdf.iterrows():
                        result_id = row['id']
                        results_html += '<tr>'
                        results_html += f'<td><input type="checkbox" name="selected" value="{result_id}"></td>'
                        for col in gdf.columns:
                            results_html += f'<td>{row[col]}</td>'
                        results_html += '</tr>'
                    results_html += '</tbody></table>'
                    
                    results = mark_safe(results_html)
                
                except requests.exceptions.RequestException as e:
                    # Handle connection errors or other request-related errors
                    messages.warning(request, f'Error during API request: {e}.')
                    
                except ValueError:
                    # Handle JSON deconding errors
                    messages.warning(request, f'Failed to parse JSON response: {response.json()}')

                except KeyError:
                    # Handle cases where the expected keys are not present in the response
                    messages.warning(request, 'Unexpected API response format.')

                except Exception as e:
                    # Handle any other exceptions that were not anticipated
                    messages.warning(request, f'An unexpected error occured: {e}.')
                    
            elif api == 'mgp':
                request.session['api'] = api
                limit = 100
                response, id_list = query_mgp(
                    username = username,
                    password = password,
                    collections = ['wv02', 'wv03-vnir', 'wv03-swir'],
                    start = start_date,
                    end = end_date,
                    where = "eo:cloud_cover <= 90 and off_nadir_avg <= 90 and view:sun_elevation >= 0 and platform in('worldview-03')",
                    geometry = geometry,
                    limit = limit,
                )

                if response.status_code == 200:
                    columns = ["id", "platform", "instruments", "gsd", "pan_resolution_avg",
                               "multi_resolution_avg", "datetime", "off_nadir", "azimuth",
                               "sun_azimuth", "sun_elevation", "geometry"]
                    gdf = gpd.GeoDataFrame(columns = columns)
                    gdf = gdf.set_geometry("geometry").set_crs("EPSG:4326")

                    r = response.json()
                    message = f"Your query returned {r['numberReturned']} total hits, but your max number of returned images was {limit}. If this is the same, then you might want to limit your query!"
                    
                    for i, feature in enumerate(r["features"]):
                        gdf.loc[i, "id"] = feature["id"]
                        gdf.loc[i, "aoi_id"] = aoi.id # Note this for future development
                        gdf.loc[i, "platform"] = feature["properties"]["platform"]
                        gdf.loc[i, "instruments"] = ', '.join(feature["properties"]["instruments"])
                        gdf.loc[i, "gsd"] = feature["properties"]["gsd"]
                        gdf.loc[i, "pan_resolution_avg"] = feature["properties"]["pan_resolution_avg"]
                        gdf.loc[i, "multi_resolution_avg"] = feature["properties"]["multi_resolution_avg"]
                        gdf.loc[i, "datetime"] = feature["properties"]["datetime"]
                        gdf.loc[i, "off_nadir"] = feature["properties"]["view:off_nadir"]
                        gdf.loc[i, "azimuth"] = feature["properties"]["view:azimuth"]
                        gdf.loc[i, "sun_azimuth"] = feature["properties"]["view:sun_azimuth"]
                        gdf.loc[i, "sun_elevation"] = feature["properties"]["view:sun_elevation"]
                        gdf.loc[i, "geometry"] = box(*feature["bbox"])

                    results_geojson = gdf.to_json()

                    results_html = f'<input type="hidden" id="api-hidden-input" name="select_api" value="{api}">'
                    results_html += '<table class="table table-striped">'
                    results_html += '<thread><tr><th><input type="checkbox" id="select-all"></th>'
                    for col in gdf.columns:
                        results_html += f'<th>{col}</th>'
                    results_html += '</tr></thread><tbody>'
    
                    for index, row in gdf.iterrows():
                        result_id = row['id']
                        results_html += '<tr>'
                        results_html += f'<td><input type="checkbox" name="selected" value="{result_id}"></td>'
                        for col in gdf.columns:
                            results_html += f'<td>{row[col]}</td>'
                        results_html += '</tr>'
                    results_html += '</tbody></table>'
                    
                    results = mark_safe(results_html)
                else:
                    print(response.status_code)


    else:
        form = APIQueryForm()

    return render(request, 'collection_page.html', {'form': form,
                                                    'results': results,
                                                    'message': message,
                                                    'area_of_interest_geojson': json.dumps(geometry) if geometry else None,
                                                    'results_geojson': results_geojson,
                                                    'aoi_bounds': aoi_bounds})


def processing_page(request):
    form = ProcessingForm()
    filtered_data = None

    print("\n\REQUEST API: ", request.POST, '\n\n')        
    
    if request.method == 'POST':
        if 'username' in request.POST and 'password' in request.POST:
            # Handle credentials
            username = request.POST['username']
            password = request.POST['password']
            entity_ids = request.POST.getlist('entity_ids')

            print("\n\nYour USERNAME is: ", username,)
            print("Your PASSWORD is: ", password,)
            print("Entity IDs: ", entity_ids, '\n\n')

            if entity_ids:
                session = requests.Session()
                session = ee_login(session, username, password)

                entities = [get_entity_pairs(entity_id) for entity_id in entity_ids]
                entities = [entity for record_list in entities for entity in record_list]
                print(f"Your entities are: {entities}")
                if len(entities) > len(entity_ids):
                    print(f"Your list of entity ids has increased from {len(entity_ids)}! It is now {len(entities)} records in size. This will increase the processing time")
                    entity_ids = entities
                else:
                    print("No additional entity ids were identified for your list. Proceeding as expected...")
                
                for entity_id in entity_ids:
                    # Only allow WV3 for right now
                    try:
                        print("Test passed?!")
                        start = time()
                        # The new file should be added to the ETL table
                        unzipped_dirs = download_imagery(session, 'crssp_orderable_w3', entity_id)
                        messages.success(request, f'Done downloading {entity_id}')

                        print("\n\nStandardizing name and file type!")
                        standard_name_geotiff = standardize_names(unzipped_dirs)

                        # The calibrated image should be added to the ETL table
                        print("\n\nCalibrating image!")
                        calibrated_image = calibrate_image(standard_name_geotiff)

                        print(f"\n\n IT TOOK: {round(time() - start,2)} SECONDS TO PROCESS {entity_id} \n\n")

                        # CALIBRATION SHOULD BE FOLLOWED BY PANSHARPENING WHICH NEEDS TO BE OUTSIDE OF THIS LOOP
                        #      THE PANSHARPENING WORK SHOULD LEVERAGE MY PIPELINE CODE AND THEN PROCEED TO TILING.

                        # print("\n\nTilling image!")
                        # tile_dir = convert_to_tiles(calibrated_image)
                        # messages.success(request, f'Done pre-processing {entity_id}')
                    except:
                        messages.warning(request, f'Failed downloading or pre-processing {entity_id}!')


                # If we use a database, this section wont be needed
                geotiffs = glob("../data/**/*.tif", recursive=True)
                print(f"Your geotiff list is: {geotiffs}")
                calibrated_geotiffs = [geotiff for geotiff in geotiffs if 'calibrated' in geotiff]
                calibrated_panchromatic_images = [calibrated_geotiff for calibrated_geotiff in calibrated_geotiffs if 'P1BS' in calibrated_geotiff]
                print(f"Your {len(calibrated_panchromatic_images)} calibrated panchromatic image(s) are: {calibrated_panchromatic_images}")

                for pantiff in calibrated_panchromatic_images:
                    try:
                        panfile = pantiff.split('\\')[-1]
                        print(f"Your pan file name is {panfile}")
                        
                        msifile = panfile.replace('P1BS', 'M1BS')
                        print(f"Your msi file name is {msifile}")
                        
                        msitiff = [geotiff for geotiff in geotiffs if msifile in geotiff][0]
                        print(f"Your {len(msitiff)} calibrated multispectral image(s) are: {msitiff}")
                        
                        shrptiff = '../data/' + pantiff.split('\\')[-1].replace('P1BS', 'S1BS')
                        gdal_pansharpen(['' ,'-b', '5', '-b', '3', '-b', '2', '-r', 'cubic', '-threads', 'ALL_CPUS', pantiff, msitiff, shrptiff])
                        print("Pansharpened {}!".format(shrptiff))
                        print(f"\n\n IT TOOK: {round(time() - start,2)} SECONDS TO PROCESS FROM DOWNLOAD TO {shrptiff} \n\n")

                        # Insert GENERTATE SOME INTERESTING POINTS HERE

                        interesting_points = 'C:/gis/apps/libs/generate_interesting_points.py'
                        out_geojson = shrptiff.replace('tif', 'geojson')
                        subprocess.run([sys.executable, interesting_points, '--input_url', shrptiff, '--output_fn', out_geojson, '--method', 'big_window', '--difference_threshold', '20', '--overwrite'])
                        # Create a Shapefile from GeoJSON for heads-up review
                        gdf = gpd.read_file(out_geojson)
                        output_shp = out_geojson.replace('geojson', 'shp')
                        gdf.to_file(output_shp)

                        # Create or update interesting points in database
                        import_pois(out_geojson)

                        # COMMENTED OUT TO MAKE SOME CALIBRATED IMAGES TO CREATE POINTS OF INTEREST
    
                #         ultratiff = '.'.join(shrptiff.split('.')[:-1]) + "_ultra.tif"
                #         options = "-overwrite -multi -wm 80% -tr 0.13 0.13 -ovr 20 -co TILED=YES -co BIGTIFF=IF_SAFER -co COMPRESS=LZW -co NUM_THREADS=ALL_CPUS"
                #         gdal.Warp(ultratiff, shrptiff, format="COG", options=options)
                #         print("Oversampling {}!".format(ultratiff))
                #         print(f"\n\n IT TOOK: {round(time() - start,2)} SECONDS TO PROCESS FROM DOWNLOAD TO {ultratiff} \n\n")
    
                #         tile_dir = '.'.join(ultratiff.split('.')[:-1]) + '_tiles/'
                #         # More than five processes results in errors!!! If oversampled image, no more than three processes!!!
                #         # Set to '4-' levels for right now. 20 takes too long!
                #         subprocess.run([sys.executable, 'C:/Users/john.wall/AppData/Local/anaconda3/envs/gaia/Scripts/gdal2tiles.py',
                #                         '-r', 'cubic', '-z', '4-', '--processes=3', '-w', 'none',
                #                         ultratiff, tile_dir])
                #         print("Tiled {}!".format(tile_dir))
                #         print(f"\n\n IT TOOK: {round(time() - start,2)} SECONDS TO PROCESS FROM DOWNLOAD TO {tile_dir} \n\n")
                    except Exception as e:
                        print(f"FAILED WITH EXCEPTION {e}. Moving along?!...")
                
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

def exploitation_page(request, item_id=None):
    """ The WHALE TCPED Exploidation Page is intended to support the review of
            Points of Interest (POI) from three scenerios:

                 1. An end-user nagivates to the page and is provided with the first
                     point of interest they have not reviewed and which still has not
                     been reviewed by three people.
                 2. An end-user needs to advance and reverse through points of
                     interests they intend to review or have reviewed. In short,
                     they need to be able to use "next" and "previous" buttons.
                 3. An end-user knows exactly the id, catalog_id, vendor_id, and entity_id
                     string they need for a point of interest.
    """
    # Get values passed by front-end
    id = request.GET.get('id')
    catalog_id = request.GET.get('catalog_id')
    vendor_id = request.GET.get('vendor_id')
    entity_id = request.GET.get('entity_id')
    action = request.GET.get('action')

    # Troubleshooting print statements to show action and parameters being passed
    print(f"Action: {action}")
    print(f"URL Paramters - ID: {id}, Catalog ID: {catalog_id}, Vendor ID: {vendor_id}, and Entity ID: {entity_id}")

    # Set the following to none then update as necessairy
    poi = None
    next_id = None
    previous_id = None

    # Convert id to integer if it exists
    try:
        id = int(id) if id else None
    except ValueError:
        id = None

    # Record the user to add to database
    user = request.user

    # Helper functions!
    def get_first_unreviewed_poi(user):
        """ Get the first unreviewed POI for the user with a
                 valid COG in Azure. When a valid COG is found,
                 lock the point of interest within the database.
                 If no unreviewed point of interest is found
                 overlaying any COGs in Azure, return None.

             This supports Scenerio 1.

             USER - The loged-in user making the request
        """
        # Query for all points of interest that the user has not reviewed and are available
        unreviewed_pois = PointsOfInterest.objects.filter(status="Available").exclude(reviewed_by_users=user).order_by('id')

        # Iterate through each unreviewed points of interest until a valid COG is found in Azure
        for poi in unreviewed_pois:
            # Debug statement to see which POIs are being checked
            print(f"Checking POI ID: {poi.id}")
            
            exists, blob_name = cog_exists(poi.vendor_id)

            # If the COG exists, lock it for review
            if exists:
                poi.status = "In Review"
                poi.locked_by = user
                poi.save()
                
                print(f"Found POI with COG - ID: {poi.id}, Vendor ID: {poi.vendor_id}")
                return poi

        print("No available POIs with valid COG found.")
        return None

    def get_next_poi(user):
        """ Get the next unreviewed POI for the user with a
                valid COG in Azure. When a valid COG is found,
                lock the point of interest within the database.
                If no unreviewed point of interest is found
                overlaying any COGs in Azure, return None.

             This supports Scenerio 2.

             USER - The loged-in user making the request
        """
        # Query for all points of interest that the user has not reviewed and are available
        next_pois = PointsOfInterest.objects.filter(status="Available").exclude(reviewed_by_users=user).order_by('id')
        
        # Iterate through each unreviewed points of interest until a valid COG is found in Azure
        for poi in next_pois:
            # Debug statement to see which POIs are being checked
            print(f"Checking POI ID: {poi.id}")
            
            exists, blob_name = cog_exists(poi.vendor_id)

            # If the COG exists, lock it for review
            if exists:
                poi.status = "In Review"
                poi.locked_by = user
                poi.save()
                
                print(f"Found POI with COG - ID: {poi.id}, Vendor ID: {poi.vendor_id}")
                return poi

        print("No available POIs with valid COG found.")
        return None

    def get_previous_poi(user, current_poi_id):
        """ Get the next unreviewed POI for the user with a
                valid COG in Azure. When a valid COG is found,
                lock the point of interest within the database.
                If no unreviewed point of interest is found
                overlaying any COGs in Azure, return None.

             This supports Scenerio 2.

             USER - The loged-in user making the request
        """
        # Query for all previous POIs that the user has not reviewed and are available
        previous_pois = PointsOfInterest.objects.filter(id__lt=current_poi_id, status="Available", reviewed_by=user).order_by('-id')
    
        # Iterate through each previous POI until a valid COG is found
        for poi in previous_pois:
            print(f"Checking previous POI ID: {poi.id}")  # Debug print to see which POIs are being checked
            exists, blob_name = cog_exists(poi.vendor_id)  # Unpack the return values of cog_exists
    
            if exists:
                # Lock and return this POI for the user
                poi.status = "In Review"
                poi.locked_by = user
                poi.save()

                cache_key = f"reviewed_pois_{user.id}"
                reviewed_pois = cache.get(cache_key, [])
                reviewed_pois.append(poi.id)
                cache.set(cache_key, reviewed_pois, timeout=3600)
                
                print(f"Found previous POI with COG - ID: {poi.id}, Vendor ID: {poi.vendor_id}, Blob: {blob_name}")
                return poi
    
        print("No previous POIs with valid COG found.")
        return None  # No previous POIs with valid COG found
    
    def cog_exists(vendor_id):
        """ Checks if a COG exists in Azure when provided with a Vendor ID.
                Really a wrapper function that includes a check cache function.

            VENDOR ID - Vendor ID value
        """
        cached_result = cache.get(f'cog_existence_{vendor_id}')
        if cached_result is not None:
            return cached_result

        # Call real CHECK COG EXISTANCE function
        exists, blob_name = check_cog_existence(vendor_id, directory='cogs/')
        cache.set(f'cog_existence_{vendor_id}', (exists, blob_name), timeout=300)  # Cache COG existence for 5 minutes
        return exists, blob_name

    # Scenario 1:
    #    If no id, catalog_id, vendor_id, and entity_id are provided, find the first unreviewed
    #    point of interest with a valid COG file in Azure.
    if id is None and not (catalog_id and vendor_id and entity_id):
        poi = get_first_unreviewed_poi(user)
        if poi:
            return redirect(f'{request.path}?id={poi.id}&catalog_id={poi.catalog_id}&vendor_id={poi.vendor_id}&entity_id={poi.entity_id}')

        # Error handle for when no available points of interest can be found with a corresponding
        #      COG.
        return render(request, 'exploitation_page.html', {
            'poi': None,
            'poi_form': None,
            'next_id': None,
            'previous_id': None,
            'vendor_id': None,
            'longitude': None,
            'latitude': None,
            'error_message': "No available POIs with valid COG found.",
            'cog_url': f"{blob_name}" if exists else None
        })

    # Scenario 2:
    #      Handle "next" action (get the next unreviewed point of interest with a COG)
    if action == "next":
        next_poi = get_next_poi(user)
        if next_poi:
            return redirect(f'{request.path}?id={next_poi.id}&catalog_id={next_poi.catalog_id}&vendor_id={next_poi.vendor_id}&entity_id={next_poi.entity_id}')

        # Error handling for when there are no more unreviewed point of interest with a valid COG
        return render(request, 'exploitation_page.html', {
            'poi': None,
            'poi_form': None,
            'next_id': None,
            'previous_id': None,
            'vendor_id': None,
            'longitude': None,
            'latitude': None,
            'error_message': "No more unreviewed POIs with valid COG found.",
            'cog_url': f"{blob_name}" if exists else None
        })

    # Handle "previous" action (retrieve previous point of interest)
    if action == "previous":
        print("Handling 'previous' action...")
        if id:
            print("\tAn ID was provided")
            try:
                poi = PointsOfInterest.objects.get(id=id)
            except PointsOfInterest.DoesNotExist:
                poi = None

        if poi:
            print("\tA point of interest object was provided")
            previous_poi = get_previous_poi(user, poi.id)
            if previous_poi:
                return redirect(f'{request.path}?id={previous_poi.id}&catalog_id={previous_poi.catalog_id}&vendor_id={previous_poi.vendor_id}&entity_id={previous_poi.entity_id}')
            else:
                print("No previous points of interest found for the 'previous' action.")
        else:
            print("No current point of interest found; cannot navigate to previous point of interest.")

        # Error handling for when there are no previous points of interest to display
        return render(request, 'exploitation_page.html', {
            'poi': None,
            'poi_form': None,
            'next_id': None,
            'previous_id': None,
            'vendor_id': None,
            'longitude': None,
            'latitude': None,
            'error_message': "No previous POIs to display.",
            'cog_url': None
        })
    
    # Scenario 3:
    #     If parameters (id, catalog_id, vendor_id, and entity_id) are provided,
    #     retrieve the specific point of interest
    if id and catalog_id and vendor_id and entity_id:
        try:
            poi = PointsOfInterest.objects.get(id=id, catalog_id=catalog_id, vendor_id=vendor_id, entity_id=entity_id)
            
        except PointsOfInterest.DoesNotExist:
            poi = None

    # Classification form (i.e., PointsOfInterestForm) handling
    if request.method == "POST":
        form = PointsOfInterestForm(request.POST, instance=poi) if poi else PointsOfInterestForm(request.POST)
        if form.is_valid():
            poi = form.save()
            
            return redirect(f'{request.path}?id={poi.id}&catalog_id={poi.catalog_id}&vendor_id={poi.vendor_id}&entity_id={poi.entity_id}')
    else:
        form = PointsOfInterestForm(instance=poi) if poi else PointsOfInterestForm()

    # Since the points were generated from projected imagery, we need to transform them to
    #      geographic coordinates (i.e., EPSG:4326) to show them.
    if poi and poi.point and poi.epsg_code:
        print(f"Your geometry is: {poi.point} and your EPSG code is: {poi.epsg_code}")
        source_crs = CRS(f"EPSG:{poi.epsg_code}")
        target_crs = CRS("EPSG:4326")
        transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
        easting, northing = poi.point.coords
        longitude, latitude = transformer.transform(easting, northing)
        
    else:
        # Have a fallback location of Fisherman's Wharf, Provincetown, MA.
        longitude, latitude = -70.183762, 42.049081

    # Check if the COG file for the vendor ID exists
    if vendor_id:
        modified_vendor_id = vendor_id.replace("P1BS", "S1BS")
        exists, blob_name = cog_exists(modified_vendor_id)
        if not exists:

            # Error handling for when a point of interest might exist, but no COG
            return render(request, 'exploitation_page.html', {
                'poi': poi,
                'poi_form': form,
                'next_id': next_id,
                'previous_id': previous_id,
                'vendor_id': vendor_id,
                'longitude': longitude,
                'latitude': latitude,
                'error_message': f"COG of vendor id {vendor_id} has not been uploaded to Azure yet. Please check back later.",
                'cog_url': None
            })

    # If everything passes, render the page. Still have some COG error handling.
    return render(request, 'exploitation_page.html', {
        'poi': poi,
        'poi_form': form,
        'next_id': next_id,
        'previous_id': previous_id,
        'vendor_id': vendor_id,
        'longitude': longitude,
        'latitude': latitude,
        'error_message': None,
        'cog_url': f"{blob_name}" if exists else None
    })

def dissemination_page(request):
    return render(request, 'dissemination_page.html')

def check_records_view(request):
    """ AUXILIARY FUNCTION

        This function is for QA/QC
    """
    records_exist = Species.objects.exists()
    return render(request, 'check_records.html', {'records_exist': records_exist})

def generate_sas_token(blob_name):
    try:
        account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
        account_key = settings.AZURE_STORAGE_ACCOUNT_KEY
        container_name = settings.AZURE_CONTAINER_NAME

        blob_path = 'cogs/' + blob_name
        print(f"Your blob path is: {blob_path}")
        
        sas_token = generate_blob_sas(
            account_name = account_name,
            container_name = container_name,
            blob_name = blob_path,
            account_key = account_key,
            permission = BlobSasPermissions(read=True),
            expiry = datetime.utcnow() + timedelta(hours=1)
        )
    
        blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_path}?{sas_token}"
    
        return blob_url

    except Exception as e:
        print(f"Error generating SAS token for blob '{blob_name}': {e}")
        return None

# def generate_authorization_token(blob_name):
#     """ AUXILIARY FUNCTION

#         This function generates an SAS Token
#     """
#     account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
#     account_key = settings.AZURE_STORAGE_ACCOUNT_KEY
#     container_name = "transfer"

#     url_path = f"/{account_name}/{container_name}/{blob_name}"
#     date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

#     string_to_sign = f"GET\n\n\n\n\n\n\n\n\n\n\n\nx-ms-date:{date}\nx-ms-version:2020-06-12\n{url_path}"

#     signature = base64.b64encode(hmac.new(base64.b64decode(account_key), string_to_sign.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')

#     authorization_header = f"SharedKey {account_name}:{signature}"
#     return authorization_header, date

def check_cog_existence(vendor_id, directory=None):
    account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
    account_key = settings.AZURE_STORAGE_ACCOUNT_KEY
    container_name = settings.AZURE_CONTAINER_NAME

    vendor_id = vendor_id.replace('P1BS', 'S1BS')
    
    # print(f"Checking for COG Vendor ID: {vendor_id}")
    
    try:
        credential = AzureNamedKeyCredential(account_name, account_key)
    
        blob_service_client = BlobServiceClient(
            account_url = f"https://{account_name}.blob.core.windows.net/",
            credential=credential
        )
    
        container_client = blob_service_client.get_container_client(container_name)
    
        prefix = directory if directory else ""
        
        blobs = container_client.list_blobs(name_starts_with=prefix)
        for blob in blobs:
            if vendor_id in blob.name:
                print(f"Your validated blob name is: {blob.name}")
                return True, blob.name
    
        return False, None

    except Exception as e:
        print(f"An error occurred: {e}")
        return False, None
        

def cog_view(request, vendor_id=None):
    print(f"\n\nIncoming vendor_id: {vendor_id}")
    
    blob_name = vendor_id
    print(f"YOUR BLOB NAME IS: {blob_name}")

    try:
        blob_url = generate_sas_token(blob_name)
        print(f"Constructed Blob URL with SAS Token: {blob_url}")

        session = requests.Session()
        retries = requests.adapters.Retry(total = 5, backoff_factor = 1, status_forcelist = [500, 502, 503, 504])
        adapter = requests.adapters.HTTPAdapter(max_retries = retries)
        session.mount('https://', adapter)

        range_header = request.META.get('HTTP_RANGE', None)
        headers = {}

        if range_header:
            start, end = range_header.strip().split('=')[1].split('-')
            headers['Range'] = f"bytes={start}-{end}" if end else f"bytes={start}-"

        response = requests.get(blob_url, headers=headers, timeout = 10)

        print(f"Response Status Code: {response.status_code}")
        #print(f"Response Text: {response.text}")
        #print(f"Response Headers: {response.headers}")

        if response.status_code in [200, 206]:
            print("Successful status code {response.status_code}")

            if range_header:
                content_range = response.headers.get('Content-Range')
                tile_response = HttpResponse(response.content, content_type = 'image/tiff', status = 206)
                tile_response['Content-Range'] = content_range
                tile_response['Accept-Ranges'] = 'bytes'
                tile_response['Content-Length'] = len(response.content)
            else:
                tile_response = HttpResponse(response.content, content="image/tiff")
                
            return tile_response
            
        else:
            return HttpResponseForbidden(f"Error fetching COG: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        return HttpResponse(f"Network error: {str(e)}", status = 503)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=403)

def tile_view(request, z, x, y, vendor_id=None):
    # Blob name should be changed to accomodate changes in tiles
    base_tile_path = "21APR24154045-S1BS-506967344060_01_P006_u08mr32619"
    blob_name = f"tiles/{base_tile_path}/{z}/{x}/{y}.png"

    try:
        authorization_header, date = generate_authorization_token(blob_name)
        blob_url = f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{settings.AZURE_CONTAINER_NAME}/{blob_name}"
        print(f"YOUR BLOB URL IS: {blob_url}")

        headers = {
            'Authorization': authorization_header,
            'x-ms-date': date,
            'x-ms-version': '2020-06-12'
        }

        #response = requests.get(blob_url, headers=headers)

        session = requests.Session()
        retries = requests.adapters.Retry(total = 5, backoff_factor = 1, status_forcelist = [500, 502, 503, 504])
        adapter = requests.adapters.HTTPAdapter(max_retries = retries)
        session.mount('https://', adapter)

        response = session.get(blob_url, headers = headers, timeout = 10)
        
        if response.status_code == 200:
            tile_response = HttpResponse(response.content, content_type = 'image/png')
            return tile_response
        else:
            return HttpResponseForbidden(f"Error fetching tile: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        return HttpResponse(f"Network error: {str(e)}", status = 503)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=403)

def get_poi_coordinates(species):
    """
    Retrieves the longitude and latitude coordinates for a given species object.
    If the species has a point geometry and an EPSG code, it will set the correct SRID
    and then transform the coordinates to WGS84 (EPSG:4326) using GeoDjango's transform method.
    Otherwise, it returns default coordinates.
    """
    # Default coordinates (replace with appropriate default if necessary)
    longitude, latitude = -70.183762, 42.049081

    if species and species.point and species.epsg_code:  # Ensure the species has a geometry field and EPSG code
        try:
            # Set the SRID (spatial reference identifier) of the geometry to the EPSG code from the database
            species.point.srid = int(species.epsg_code)

            # Transform the geometry to EPSG:4326 (WGS84)
            geometry_4326 = species.point.transform(4326, clone=True)

            # Extract the transformed coordinates
            longitude, latitude = geometry_4326.coords
        except Exception as e:
            print(f"Error transforming coordinates: {e}")

    return longitude, latitude

def proxy_openlayers_js(request):
    url = "https://cdn.jsdelivr.net/npm/ol@6.15.1/ol.js"
    response = requests.get(url)
    return HttpResponse(response.content, content_type="application/javascript")

def proxy_webgls_js(request):
    url = "https://cdn.jsdelivr.net/npm/ol-webgl/dist/ol-webgl.min.js"
    response = requests.get(url)
    return HttpResponse(response.content, content_type="application/javascript")