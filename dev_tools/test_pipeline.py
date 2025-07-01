# ------------------------------------------------------------------------------
# ----- test_pipeline.py -------------------------------------------------------
# ------------------------------------------------------------------------------
#
#    authors:  John Wall (john.wall@noaa.gov)
#              
#    purpose:  Test evaluation of the imagery processing capabilities within
#                   the GAIA application starting with an Area of Interest,
#                   provided as an ESRI Shapefile, through to a final,
#                   pansharpenend Cloud Optimized GeoTIFF.
#
# ------------------------------------------------------------------------------



# ------------------------------------------------------------------------------
# Import libraries, configure environment
# ------------------------------------------------------------------------------
import os
import sys
import shutil
import zipfile
import requests
import importlib
import pandas as pd
from time import time
import geopandas as gpd
from glob import glob
import multiprocessing as mp
from functools import partial
from shapely.geometry import box, Polygon


# Local, custom methods
project_dir = "../../../gis/PSD-WEB-GAIA"
project_dir = os.path.abspath(project_dir)
sys.path.append(str(project_dir))

import utils.api_utils
import utils.pgc_wrapper
import utils.spatial_ops

# Reload for troubleshooting
importlib.reload(utils.api_utils)
importlib.reload(utils.pgc_wrapper)
importlib.reload(utils.spatial_ops)


# ------------------------------------------------------------------------------
# User defined variables
# ------------------------------------------------------------------------------
username = "johnwallx"
token_file = "../../../gis/security/token.txt"
data_dir = "../../../gis/data/"
# aoi_shp = "shapefiles/UCIPlus.shp"
dem_file = "rasters/dem.tif"
# img_dir = "imagery/belugas/"
aoi_shp = "shapefiles/CCB_Polygon.shp"
img_dir = "imagery/narw/"

imagery_dataset = 'crssp_orderable_w3'
# start_date = '2021-06-01'
# end_date = '2021-06-30'
start_date = '2021-03-01'
end_date = '2021-05-30'

token_file = os.path.abspath(token_file)
data_dir = os.path.abspath(data_dir)
aoi_shp = os.path.join(data_dir, aoi_shp)
dem_file = os.path.join(data_dir, dem_file)
img_dir = os.path.join(data_dir, img_dir)


# ------------------------------------------------------------------------------
# Log in to EE, establish a secure session
# ------------------------------------------------------------------------------
with open(token_file, 'r') as f:
    token = f.read()

session = requests.Session()
secure_session = utils.api_utils.ee_login(session, username, token)


# ------------------------------------------------------------------------------
# Read Area of Interest ESRI shapefile, ensure it is in WGS84 (EPSG 4326)
# ------------------------------------------------------------------------------
gdf = gpd.read_file(aoi_shp)
if gdf.crs != "EPSG:4326":
    gdf = gdf.to_crs("EPSG:4326")
aoi_geometry = gdf['geometry'][0]


# ------------------------------------------------------------------------------
# Search for satellite imagery scenes meeting query criteria
# ------------------------------------------------------------------------------
data_filter = utils.api_utils.build_ee_query_payload(start_date, end_date,
                                                     aoi_geometry,
                                                     imagery_dataset = imagery_dataset)
search_url = "https://m2m.cr.usgs.gov/api/api/json/stable/scene-search"
response = secure_session.get(url=search_url, data=data_filter)
print(f"\nObtained a status code of: {response.status_code}\n")


# ------------------------------------------------------------------------------
# Pull results into a GeoDataFrame for review and assessment
# ------------------------------------------------------------------------------
if response.status_code == 200:
    r = response.json()
    message = print(f"Your query returned {r['data']['totalHits']} total hits," +
                    f" but, because of your max results threshold, you only have" +
                    f" {r['data']['recordsReturned']} to review!\n\tTry shortening" + 
                    f" your timeframe you are querying.")

    results = r['data']['results']
    columns = [field['fieldName'] for field in results[0]['metadata']]
    
    gdf = gpd.GeoDataFrame(columns = columns)
    
    for result in results:
        gdf.loc[gdf.shape[0]] = [field['value'] for field in result['metadata']]
    
    gdf['thumbnail'] = pd.Series([result['browse'][0]['thumbnailPath'] for result in results])
    gdf['publish_date'] = pd.Series([result['publishDate'] for result in results])
    gdf['bounds'] = gpd.GeoSeries([Polygon(result['spatialBounds']['coordinates'][0]) for result in results])
    gdf = gdf.set_geometry("bounds").set_crs("EPSG:4326")
    
    drop_columns = [column for column in columns if "Corner" in column] + ['Center Latitude', 'Center Longitude']
    gdf = gdf.drop(drop_columns, axis=1)

    # Filter to just Level 1, might need to be changed for GeoEye
    gdf = gdf[gdf['Processing Level'] == 'LV1']
    print(f"Your table is now {gdf.shape[0]} records in length to download!")

    results_geojson = gdf.to_json()

else:
    print(f"\nResponse code other than 200 returned, the code is {response.status_code}" +
          f" for troubleshooting!\n")


# ------------------------------------------------------------------------------
# Download imagery to local
#
# TODO: THIS NEEDS TO HANDLE DEDUPLICATION
# ------------------------------------------------------------------------------
entity_ids = gdf['Entity ID'].to_list()

i = 1
while len(entity_ids) > 0:
    
    start = time()
    process_partial = partial(utils.api_utils.download_imagery,
                              session = secure_session,
                              datasetName = imagery_dataset,
                              out_dir = img_dir)
    with mp.Pool(processes=mp.cpu_count()) as pool:
        results = pool.map(process_partial, entity_ids)
    end = round(time() - start, 2)
    print(f"It took {end} seconds to run iteration {i}!")

    downloaded_list = glob(img_dir + "**/*.zip", recursive=True)
    downloaded_ids = [os.path.basename(path).split('.')[0] for path in downloaded_list]
    print(f"Your to download lists looks like: {list(set(entity_ids))}")
    print(f"Your downloaded list looks like: {list(set(downloaded_ids))}")
    print("The difference between the entity list and downloaded list:")
    entity_ids = list(set(entity_ids) - set(downloaded_ids))
    print(entity_ids)

    i = i + 1


# ------------------------------------------------------------------------------
# Organize imagery into Catalog ID directories
# ------------------------------------------------------------------------------
for idx, row in gdf.iterrows():
    catalog_id = row['Catalog ID']
    entity_id = row['Entity ID']

    catalog_dir = os.path.join(img_dir, catalog_id)
    os.makedirs(catalog_dir, exist_ok=True)

    zip_filename = f"{entity_id}.zip"
    source_path = os.path.join(img_dir, zip_filename)
    destination_path = os.path.join(catalog_dir, zip_filename)

    if os.path.exists(source_path):
        shutil.move(source_path, destination_path)

cat_id_dirs = [d for d in os.listdir(img_dir) if os.path.isdir(os.path.join(img_dir, d))]
print(cat_id_dirs)

# ------------------------------------------------------------------------------
# Unzip imagery, organize imagery into USGS loading values
# ------------------------------------------------------------------------------
for cat_id_dir in cat_id_dirs:
    # Unzip directories
    img_cat_dir = os.path.join(img_dir, cat_id_dir)
    img_zips = glob(img_cat_dir + "**/*.zip", recursive=True)
    for img_zip in img_zips:
        with zipfile.ZipFile(img_zip, 'r') as zip_ref:
            zip_ref.extractall(img_cat_dir)
            print(f"Extracted {img_zip} to {img_cat_dir}")

    # Identify Vendor ID named directories
    vendor_id_dirs = []
    for entry in os.listdir(img_cat_dir):
        if os.path.isdir(os.path.join(img_cat_dir, entry)):
            vendor_id_dirs.append(entry)

    # Identify random USGS loading-event values
    random_usgs_values = []
    for vendor_id_dir in vendor_id_dirs:
        random_usgs_values.append(vendor_id_dir.split('-')[-1].split('_')[0])
    random_usgs_values_set = set(random_usgs_values)
    random_usgs_value_digits = []
    for random_usgs_value in random_usgs_values_set:
        if random_usgs_value.isdigit():
            random_usgs_value_digits.append(random_usgs_value)
    
    # Create directories from random USGS loading events,
    #   fill them with imagery from each event
    for random_usgs_value_digit in random_usgs_value_digits:
        random_usgs_value_dir = os.path.join(img_dir,
                                             cat_id_dir,
                                             random_usgs_value_digit)
        os.makedirs(random_usgs_value_dir, exist_ok=True)

        for vendor_id_dir in vendor_id_dirs:
            if random_usgs_value_digit in vendor_id_dir:
                source_path = os.path.join(img_cat_dir, vendor_id_dir)
                destination_path = os.path.join(img_cat_dir,
                                                random_usgs_value_digit,
                                                vendor_id_dir)
                if os.path.exists(source_path):
                    shutil.move(source_path, destination_path)

# ------------------------------------------------------------------------------
# Tidy up the files, ensure there are panchromatic, multispectral pairs
# ------------------------------------------------------------------------------
panchromatic_image_list = []
multispectral_image_list = []
for unzipped_dir in unzipped_dirs:
    print(f"Your unzipped dir looks like: {unzipped_dir}")
    
    start = time()
    # Only use this to get the dir name again
    unzipped_files = glob(unzipped_dir + '/**/*.*', recursive=True)
    print(f"\nSuccessfully executed glob: {unzipped_files}")
    filtered_files = [file for file in unzipped_files if 'license' not in file]
    print("Successfully removed license related files")
    dir_name = filtered_files[0].replace('\\', '/').split('/')[-2].split('.')[0]
    print(f"Successfully found dir name: {dir_name}\n")

    try:
        standard_name_geotiff = utils.api_utils.standardize_names(unzipped_dir)
    except Exception as e:
        standard_name_geotiff = unzipped_dir
        print(f"\n\nFailed standardizing names with Exception: {e}.\n\tTrying to move along...\n\n")

    if 'P1BS' in standard_name_geotiff:
        panchromatic_image_list.append(standard_name_geotiff)
    elif 'M1BS' in standard_name_geotiff:
        multispectral_image_list.append(standard_name_geotiff)
    else:
        print("\n\nYOUR IMAGE DOES NOT FOLLOW THE STANDARD NAMING CONVENTION FOR MAXAR\n\n")

imagery_pairs = {}
no_ms_match = []
no_pan_match = multispectral_image_list.copy()

for panchromatic_image in panchromatic_image_list:
    panchromatic_image_file = os.path.basename(panchromatic_image)
    multispectral_image_guess = panchromatic_image_file.replace('P1BS', 'M1BS')

    match = next(
        (ms_image for ms_image in multispectral_image_list if multispectral_image_guess in ms_image),
        None
    )

    if match:
        imagery_pairs[panchromatic_image] = match
        no_pan_match.remove(match)  # It's matched, so not unmatched
    else:
        no_ms_match.append(panchromatic_image)

# Summary output of missing matches
print("\n--- Panchromatic images with NO multispectral match ---")
for img in no_ms_match:
    print(img)

print("\n--- Multispectral images with NO panchromatic match ---")
for img in no_pan_match:
    print(img)


# ------------------------------------------------------------------------------
# Calibrate imagery, create a pansharpened image, convert it to a Cloud
#   Optimized GeoTIFF (web optimized), and upload it to Azure.
#
# TODO: Needs to be able to handle different types of imagery (e.g. GeoEye)
#
# ------------------------------------------------------------------------------
calibrated_imagery_pairs = {}
for pan, msi in imagery_pairs.items():
    calibrated_pan = utils.pgc_wrapper.calibrate_image(pan, dem_file)
    calibrated_msi = utils.pgc_wrapper.calibrate_image(msi, dem_file)

    pansharpened_image = utils.spatial_ops.pansharpen_imagery(calibrated_pan,
                                                              calibrated_msi)
    
    web_optimized_cog = utils.spatial_ops.create_cog(pansharpened_image)