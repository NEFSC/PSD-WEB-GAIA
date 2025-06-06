"""
Utility functions for working with satellite imagery and Azure storage,
including file conversion, standardization, calibration, and tile generation.

Also includes functions for Azure blob storage operations and POI imports.

    Functions:
        get_entity_pairs(entity_id): Gets paired multispectral and panchromatic image IDs.
        convert_ntf_to_tif(ntf): Converts NTF files to GeoTIFF format.
        standardize_names(imgdir): Standardizes image filenames in a directory.
        calibrate_image(tiff): Calibrates Maxar 1B images using PGC method.
        convert_to_tiles(tiff): Converts images to web-friendly tiles.
        import_pois(geojson_path): Imports Points of Interest from GeoJSON.
        upload_to_azure(local_file, azure_dir, content_type): Uploads files to Azure storage.
"""

import os
import sys
import subprocess
from glob import glob

# Geospatial stack
from osgeo import gdal
import geopandas as gpd

# Azure stack
from azure.storage.blob import BlobServiceClient, ContentSettings

# Django stack
from django.conf import settings

# GAIA stack
from .models import ExtractTransformLoad as ETL
from .models import PointsOfInterest as POI

def get_entity_pairs(entity_id):
    if 'M' in entity_id:
        pair_id = entity_id.replace('M', 'P')
    elif 'P' in entity_id:
        pair_id = entity_id.replace('P', 'M')
    else:
        print("Failed to find Multispectral and Panchromatic paring. Returning with none!")
        return []

    records = ETL.objects.filter(entity_id__in=[entity_id, pair_id])
    # print("Object checked!")
    records = [str(record.entity_id) for record in records]
    print(f"Your records: {records}")
    record_key = [record for record in records if 'P' in record][0]
    record_value = [record for record in records if 'M' in record][0]

    return {record_key: record_value}

def convert_ntf_to_tif(ntf):
    try:
        outfile = ntf.replace('NTF', 'TIF')
        ntf_data = gdal.Open(ntf)
        gdal.Translate(outfile, ntf_data, format="GTiff")
        del ntf_data
        print(f"Your converted geotiff is {outfile}")
        os.remove(ntf)
        return outfile
    except Exception as e:
        print(f"Error during conversion: {e}")

def standardize_names(imgdir):
    glob_path_lower = imgdir + "/**/*.tif"
    glob_path_upper = imgdir + "/**/*.TIF"
    print("Trying standarize name glob...")
    geotiff = glob(glob_path_lower, recursive=True) + glob(glob_path_upper, recursive=True)
    print(f"GeoTIFFs results: {geotiff}")
    if not geotiff:
        glob_path_lower = imgdir + "/**/*.ntf"
        glob_path_upper = imgdir + "/**/*.NTF"
        geotiff = glob(glob_path_lower, recursive=True) + glob(glob_path_upper, recursive=True)
        geotiff = geotiff[0]
        print(f"NTF results: {geotiff}")
        if len(geotiff) > 0:
            print("NTF files were found! Converting them to GeoTIFF")
            geotiff = convert_ntf_to_tif(geotiff)
    else:
        geotiff = geotiff[0]
    print(f"Your geotiff is {geotiff}")
    split_name = geotiff.split('-')
    if len(split_name) == 6:
        print("Standardizing file name")
        new_name = '-'.join(split_name[:-1]) + '.tif'
        os.rename(geotiff, new_name)
    else:
        print("File name is standardized already. Moving along...")
        return geotiff
    return glob(imgdir, recursive=True)

def calibrate_image(tiff):
    """ Calibrates a given Maxar 1B image using the Polar Geospatial Center (PGC) method
             (see references). Georeferences the images to the nearest UTM zone, applies
             no stretch to the image, outputs to GeoTIFF format, the image will be
             16-bit Unsigned Integer, and resampled using cubic convolution.
    
        Ref: https://www.pgc.umn.edu/guides/pgc-coding-and-utilities/using-pgc-github-orthorectification/
        Ref: https://github.com/PolarGeospatialCenter/imagery_utils/blob/main/doc/pgc_ortho.txt
    """
    dir_path = os.path.dirname(os.path.realpath(tiff))
    print(f"Your dir_path is: {dir_path}")
    dir_path_new = os.path.join(dir_path, 'calibrated/') # Make LInux style
    print(f"Your new dir_oath is: {dir_path_new}")
    if not os.path.exists(dir_path_new):
        os.makedirs(dir_path_new)

    # Check -c ns versus mr. Lauren might be processing only three bands.
    subprocess.run([sys.executable, 'imagery_utils/pgc_ortho.py', '-p', 'utm',
                    '-c', 'mr', '-f', 'GTiff', '-t', 'Byte', '--resample=cubic',
                    dir_path, dir_path_new])
    try:
        img_out = glob(dir_path_new + "/*.tif")[0]
        print(f"Your image is: {img_out}")
        return img_out
    except:
        print("Failed on: {}".format(tiff))
        pass

def convert_to_tiles(tiff):
    """ Build a Virtual Format (VRT) file to bring images into
             the standards for building tiles. From this VRT
             build tiles using cubic convolution for
             visualization and start at a zoom level of 12.
             Tiles will be built to the maximum level supported
             by the data.
             
         The standards are that images cannot be more than
             four bands and need to be 8-bit.

         Ref: https://gdal.org/programs/gdal2tiles.html
    """
    vrt_name = "{}.vrt".format(tiff.split('.')[0])
    tile_dir_name = "{}_tiles/".format(tiff.split('.')[0])

    # if "P1BS" in tiff:
    #     subprocess.run(['gdal_translate', '-of', 'VRT', '-ot', 'Byte', '-scale', tiff, vrt_name])
    # elif "M1BS" in tiff:
    subprocess.run(['gdal_translate', '-of', 'VRT', '-ot', 'Byte', '-scale',
                    '-b', '5', '-b', '3', '-b', '2', tiff, vrt_name])
    # else:
    #     return "Image does not use the expected convention."

    # Six processes should be about 75% CPU utilization
    subprocess.run([sys.executable, 'C:/Users/USERNAMEHERE/AppData/Local/anaconda3/envs/gaia/Scripts/gdal2tiles.py',
                    '-r', 'cubic', '-z', '4-', '--processes=6', '-w', 'none', vrt_name,
                    tile_dir_name])
    return tile_dir_name

def import_pois(geojson_path):
    """ Synchronous Import Points of Interest function.

        Takes the GeoJSON filepath and converts the file path to Vendor ID
            using the panchromatic image as the basis for this (opposed to
            the multispectral). Queries the ExtractTransformLoad (ETL) table
            in SpatiaLite for the relevant Vendor ID object. Reads the GeoJSON
            file to a GeoDataFrame. Updates or creates the Interesting Points
            records from a combination of the ETL and GeoJSON information.

        Print statements support troubleshooting.
    """
    vid = '_'.join(geojson_path.split('/')[-1:][0].split('.')[0].split('_')[:-1]).replace('S1BS', 'P1BS')
    obj = ETL.objects.get(vendor_id=vid)
    
    gdf = gpd.read_file(geojson_path)

    for index, row in gdf.iterrows():
        poi, created = POI.objects.update_or_create(
            sample_idx = row['id'],
            defaults={
                'catalog_id': obj.id,
                'vendor_id': obj.vendor_id,
                'entity_id': obj.entity_id,
                'area': row['area'],
                'deviation': row['deviation'],
                'point': row['geometry'].wkt
            }
        )
        print(f"\t{'Created' if created else 'Updated'} POI with id: {poi.sample_idx}\n")

    print('Data imported successfully!')

def upload_to_auzre(local_file, azure_dir, content_type):
    """ Uploads a file to Azure from a local machine.

        LOCAL FILE - Local file to be uploaded to Azure
        AZURE DIR - A directory, nor nest of directories,
            to place the file under.
        CONTENT TYPE - Content of the uploaded file
    """
    try:
        account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
        account_key = settings.AZURE_STORAGE_ACCOUNT_KEY
        container_name = settings.AZURE_CONTAINER_NAME

        account_url = f"https://{account_name}.blob.core.windows.net"
        blob_service_client = BlobServiceClient(account_url=account_url, credential=account_key)

        local_file = local_file.replace('\\', '/')
        print(f"YOUR LOCAL FILE IS {local_file}")
        blob = azure_dir + '/' + local_file.split('/')[-1]
        print(f"YOUR BLOB IS: {blob}")
        blob = blob.replace('_cog.tif', '.tif') if 'cog' in blob else blob
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob)
        content_settings = ContentSettings(content_type=content_type)

        with open(local_file, 'rb') as data:
            blob_client.upload_blob(data, content_settings=content_settings)
        print(f"Successfully uploaded {data} to {blob}")

    except Exception as e:
        print(f"An error occured: {e}")
