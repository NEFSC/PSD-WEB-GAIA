# ------------------------------------------------------------------------------
#
# Adds US Goverment Catalog IDs IDs when provide with Vendor IDs as file names
#      of GeoTIFFs.
#
# Written by John Wall (john.wall@noaa.gov)
#
# ------------------------------------------------------------------------------

# ----------------------------
# Import some libraries, configure Django
# ----------------------------
import os
import django
import zipfile
import pandas as pd
from glob import glob
from time import time
import geopandas as gpd
import subprocess
from shapely.wkt import loads
import xml.etree.ElementTree as ET

import sys; sys.path.append('../../')
os.environ['DJANGO_SETTINGS_MODULE'] = 'gaia.settings'
django.setup()

from asgiref.sync import sync_to_async
from django.core.management import call_command
from django.contrib.gis.geos import GEOSGeometry

from animal.models import PointsOfInterest as POI

# ----------------------------
# User defined variables
# ----------------------------
data_dir = "../../../gis/data/"
sub_dir = "imagery/azure/original/"

# ----------------------------
# Locally defined functions
# ----------------------------
def update_poi_from_dataframe(df, dry_run=True):
    ''' Update the Point of Interest table values for Catalog ID and Vendor ID
            based on Vendor ID when provided with a Pandas Dataframe. Allows
            for a dry run prior to executing to ensure values make sense.

        DF - A Pandas Dataframe with Catalog, Entity, and Vendor IDs
        DRY RUN - A boolean (T/F) for testing.
    '''
    for _, row in df.iterrows():
        vendor_id = row['vendor_id']
        catalog_id = row['catalog_id']

        qs = POI.objects.filter(vendor_id=vendor_id)

        if dry_run:
            count = qs.count()
            print(f"[DRY RUN] Would update {count} rows for vendor_id '{vendor_id}' "
                  f"=> catalog_id='{catalog_id}'")
        else:
            updated = qs.update(
                catalog_id=catalog_id,
            )
            print(f"Updated {updated} rows for vendor_id '{vendor_id}'")

def get_catid_from_xml(xml_path):
    ''' When provided with an XML file, searches for the CATID tag returning its
            value.
        
        XML PATH - Path to a local XML file.
    '''
    tree = ET.parse(xml_path)
    root = tree.getroot()

    catid_element = root.find(".//CATID")
    if catid_element is not None:
        return catid_element.text.strip()
    else:
        return None

# ----------------------------
# Prepare a Pandas dataframe
# ----------------------------
pdf = pd.DataFrame(columns=['catalog_id', 'vendor_id'])

# ----------------------------
# Retrieve all GeoTIFF files, build the Pandas dataframe
# ----------------------------
data_dir = os.path.abspath(data_dir)
geotiffs = glob(os.path.join(data_dir, sub_dir, '**', "*.tif"), recursive=True)

for geotiff in geotiffs:
    vendor_id = geotiff.split('\\')[-1].split('.')[0]

    # Note this is redundant since we're doing it for pan and multispectral
    if 'P1BS' in vendor_id:
        vendor_id = vendor_id.replace('P1BS', 'S1BS')
    elif 'M1BS' in vendor_id:
        vendor_id = vendor_id.replace('M1BS', 'S1BS')
    else:
        print(f"Warning, odd structure for Vendor ID returned for {vendor_id}")

    geotiff_dir = '/'.join(geotiff.split('\\')[:-1])
    xmlfiles=  glob(geotiff_dir +'/*.XML')
    xmlfile = [xmlfile for xmlfile in xmlfiles if '.aux.xml' not in xmlfile][0]
    
    cat_id = get_catid_from_xml(xmlfile)

    pdf.loc[len(pdf)] = {
        'catalog_id': cat_id,
        'vendor_id': vendor_id
    }

# ----------------------------
# Drop duplicates due to pan and multispectral
# ----------------------------
pdf = pdf.drop_duplicates(subset='vendor_id', keep='first')

# ----------------------------
# Add Catalog IDs to database
# ----------------------------
update_poi_from_dataframe(pdf, dry_run=False)