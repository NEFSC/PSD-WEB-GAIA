# Basic stack
import os
import json
import requests
from datetime import datetime
from shapely.geometry import box, Polygon
import pandas as pd
import geopandas as gpd
import django
from django.contrib import messages
from django.db import IntegrityError
from django.utils.safestring import mark_safe
from django.shortcuts import render, get_object_or_404

def convert_date_or_none(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None
from ..security import ee_login
from ..models import AreaOfInterest, EarthExplorer, GEOINTDiscovery, MaxarGeospatialPlatform
from ..forms import APIQueryForm
from ..query import build_ee_query_payload, query_mgp

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaia.settings')
os.environ["CPL_DEBUG"] = "ON" # Should enable GDAL debuggin
django.setup()

def collection_page(request):
    """ A page for consolidated review of satellite imagery collected over
            loaded areas of interest and registration of these images into
            the SpatiaLite database for processing.

        Currently supports USGS EarthExplorer, NGA GEOINT Discovery, and
            Maxar Geospatial Platform satellite imagery repositories.

        DEPENDENCIES:
            - convert_date_or_none
        
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
        print("\nREQUEST API: ", request.POST.get('select_api'), '\n\n')

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
            print("\nROW DATA: ", row_data, '\n\n')

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
