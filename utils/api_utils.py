# ------------------------------------------------------------------------------
# ----- api_utils.py -----------------------------------------------------------
# ------------------------------------------------------------------------------
#
#    authors:  John Wall (john.wall@noaa.gov)
#              
#    purpose:  Functions for interacting with the United States Geological
#                   Survey's (USGS's) Earth Explorer (EE) Application
#                   Programming Interface (API) as well as preparing it for use
#                   further within the GAIA application, i.e. standardizing
#                   file names and data types (NTF vs GeoTIFF).
#
#    references: https://m2m.cr.usgs.gov/api/docs/example/download_data-py
#
# ------------------------------------------------------------------------------



# ------------------------------------------------------------------------------
# Import libraries, configure environment
# ------------------------------------------------------------------------------
import os
import re
import time
import json
import shapely
import datetime
import requests
from glob import glob
from osgeo import gdal
from zipfile import ZipFile


# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------
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


def unzip_download(zippedfile):
    """ Unzips downloaded data from EarthExplorer.

        ZIPPEDFILE - Locally stored zipped dataset
    """
    root = '/'.join(zippedfile.split('/')[:-1])
    dirname = zippedfile.split('/')[-1].split('.')[0]
    outdir = root + '/' + dirname
    with ZipFile(zippedfile, 'r') as zObject:
        zObject.extractall(outdir)
    print("Unzipping complete!\n\n")
    os.remove(zippedfile)
    return os.path.abspath(outdir)


def download_zip(session, url, out_dir):
    """ Downloads zipped data from EarthExplorer when provided with
            the URL returning the output name.

        URL - EarthExplorer supplied URL to download data.
    """
    response = session.get(url, stream=True)
    headers = response.headers['content-disposition']
    filename = re.findall("filename=(.+)", headers)[0].replace('"','')
    print("Your files are: {}".format(filename))
    print("Your data are being saved to: {}".format(os.path.abspath(out_dir)))
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    outname = out_dir + filename
    print("Downloading: {}".format(filename))
    with open(outname, "wb") as dst:
        dst.write(response.content)
    return outname


def retrieve_download(session, label):
    """ Retreives download URLs for prepared, or staged, datasets.

        LABEL - Dataset label as provided to the "download-request"
            API endpoint.
    """
    data = {'label': label}
    url = "https://m2m.cr.usgs.gov/api/api/json/stable/download-retrieve"
    response = session.post(url=url, data=json.dumps(data))
    ra = response.json()['data']['available']
    print("Your data had to be retrieved.")
    return [dataset['downloadId'] for dataset in ra]


def request_download(session, entity_id, dataset_id, attempts=0):
    """ Requests the download URL when provided with the Entity ID,
            retrieved by querying against the "scene-search" API
            endpoint, and the Product ID, created from GET PRODUCT
            ID, returning the stagged dataset label and URL. Uses
            recursion to ensure the download is returned where the
            a sleep function of five seconds is applied per attempted
            retreval.

        Is partially dependent on the RETRIEVE DOWNLOAD function to
            retrieve download URLs for prepared, or staged, datasets.

        ENTITY ID - Dataset Entity ID which can be retrieved by querying
            against the "scene-search" API endpoint.
        DATASET ID - A Dataset ID, or Product ID, created by GET PRODUCT
            ID.
        ATTEMPTS - The number of recursive attempts that have been made
            to retreve the download URL for the requested data.
    """
    entity_product = [{'entityId': entity_id, 'productId': dataset_id}]
    label = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    data = {'downloads': entity_product, 'label': label}
    url = "https://m2m.cr.usgs.gov/api/api/json/stable/download-request"
    response = session.post(url=url, data=json.dumps(data))
    #print(f"Your request response looks like {response.json()}\n\n")
    try:
        download_id = response.json()['data']['preparingDownloads'][0]['downloadId']
        print("Your download is being prepared!")
        download_id = retrieve_download(label)
        sleep_time = 5 * attempts
        print("Sleeping for {} seconds.".format(sleep_time))
        time.sleep()
        attempts = attempts + 1
        label, download_id = request_download(session, entity_id, dataset_id, attempts)
    except:
        try:
            download_id = response.json()['data']['availableDownloads'][0]['url']
            print("Your download is available!")
        except Exception as e:
            print("Failed on Product ID {}".format(dataset_id))
            print("\tThe exception is: {}".format(e))
            download_id = 999999999
            raise e
    return label, download_id


def get_product_id(session, dataset_name, entity_id):
    """ Creates a Product ID, or Dataset ID, by querying against the
            "download-options" API endpoint using the Dataset Name,
            retrieved by querying against the "dataset-search" API
            endpoint, and the Entity ID, retrieved by querying
            against the "scene-search" API endpoint.

        DATASETNAME - Dataset Name which can be retrieved by querying
            against the "dataset-search" API endpoint.
        ENTITY ID - Dataset Entity ID which can be retrieved by querying
            against the "scene-search" API endpoint.
    """
    data = {'datasetName': dataset_name, 'entityIds': entity_id}
    # print(f"Your data payload looks like {data}")
    url = "https://m2m.cr.usgs.gov/api/api/json/stable/download-options"
    response = session.post(url=url, data=json.dumps(data))
    print(f"\nObtained a status code of: {response.status_code}\n")
    rd = response.json()['data'][0]
    print("Your data are {} bytes in size!".format(rd['filesize']))
    return rd['id']


def download_imagery(entity_id, *, session, datasetName, out_dir, max_retries=5):
    """ Wrapper function which generates an EarthExplorer product ID,
            requests the download, retrieves the download URL, downloads
            the zip file locally, and then unzips it locally.

        Is dependent on the GET PRODUCT ID, REQUEST DOWNLOAD, RETRIEVE
            DOWNLOAD, DOWNLOAD ZIP, and UNZIP DOWNLOAD functions.

        DATASETNAME - Dataset Name which can be retrieved by querying
            against the "dataset-search" API endpoint.
        ENTITY ID - Dataset Entity ID which can be retrieved by querying
            against the "scene-search" API endpoint.
    """
    for attempt in range(max_retries):
        try:
            dataset_id = get_product_id(session, datasetName, entity_id)
            label, download_id = request_download(session, entity_id, dataset_id)
            if download_id != 999999999:
                ready_download_ids = retrieve_download(session, label)
                zippedfile = download_zip(session, download_id, out_dir)
                # return unzip_download(zippedfile)
                return zippedfile
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            print("\tFailure could have been due to staging\n")
            if attempt < max_retries - 1:
                time.sleep(10)
            else:
                print("Max reties reached. Download failed.\n\n")


def geojson_for_ee(geojson:dict):
    """ Helper function to build the 'geoJson' value payload
            for the BUILD_SPATIAL_FILTER function.

        Ref. https://github.com/yannforget/landsatxplore/blob/master/landsatxplore/api.py#L439-L469
    """
    geojson_payload = {}
    geojson_payload['type'] = geojson['type']
    
    if geojson['type'] == "Polygon":
        geojson_payload['coordinates'] =  geojson['coordinates']
    else:
        print("Your GeoJSON type is not a polygon and therefore is not")
        print("\tsupported at this time. Please supply a polygon!")

    return geojson_payload


def build_cloud_cover_filter(minimum=0, maximum=100, include_unknown=True):
    """ Builds a cloud cover bandpass filter and unknown flag. Include images between
            the minimum and maximum cloud cover percentages as well as those
            where cloud cover has not been precalculated.

        MINIMUM - Minimum cloud cover percentage for your area of interest.
        MAXIMUM - Maximum cloud cover percentage for your area of interest.
        INCLUDE_UNKNON - Include images where cloud cover has not been calculated.

        Ref. https://github.com/yannforget/landsatxplore/blob/master/landsatxplore/api.py#L255-L259
        Ref. https://github.com/yannforget/landsatxplore/blob/master/landsatxplore/api.py#L523-L539
    """
    cc_payload = {}
    cc_payload["min"] = minimum
    cc_payload["max"] = maximum
    cc_payload["includeUnknown"] = include_unknown
    return cc_payload


def build_spatial_filter(geojson:dict):
    """ Builds a spatial filter by converting GeoJSON to an
            EarthExplorer-ready spatial filter. Expects GeoJSON
            to be in EPSG:4326 since it flips latitude and
            longitude to longitude and latitude.

        Is dependent on the GEOJSON_FOR_EE function above.

        *ONLY SUPPORTS POLYGONS AT THIS TIME*
            Future work should include Points.
            Lines are unlikely to be needed for this work.

        PAYLOAD - A request payload dictionary
        GEOJSON - A GeoJSON string likely loaded by reading in a
            geojson file.

        Ref. https://github.com/yannforget/landsatxplore/blob/master/landsatxplore/api.py#L493-L504
        Ref. https://github.com/yannforget/landsatxplore/blob/master/landsatxplore/api.py#L439-L469
    """
    spatial_payload = {}
    spatial_payload['filterType'] = "geojson"
    try:
        spatial_payload['geoJson'] = geojson_for_ee(geojson)
    except:
        print("Something other than a GeoJSON file was provided, assuming geometry")
        spatial_payload['geoJson'] = geojson.__geo_interface__
    
    return spatial_payload


def build_acqusition_filter(start:str, end:str):
    """ Builds a temporal filter using ISO 8601 datetime format.

        START - Start date for data acquisition. At minimum,
            YYYY-MM-DD, but can also be 2020-07-10 15:00:00.000
            which includes hours, minutes, seconds, and milliseconds.
        END - End date in the same format listed for START.

        Ref. https://github.com/yannforget/landsatxplore/blob/master/landsatxplore/api.py#L507-L520
    """
    aq_payload = {}
    aq_payload["start"] = start
    aq_payload["end"] = end
    return aq_payload


def build_dataset_filter(acquisition, spatial):
    """ Wrapper function to build DATASET-SEARCH API query
            from acquisition and spatial filter outputs.
            outputs.

        ACQUSITION - Acquisition filter.
        SPATIAL - Spatial filter.

        Ref. https://github.com/yannforget/landsatxplore/blob/master/landsatxplore/api.py#L563-L597
    """
    payload = {}
    payload['acquisitionFilter'] = acquisition
    payload['spatialFilter'] = spatial
    return payload


def build_scene_filter(acquisition, spatial, cloud):
    """ Wrapper function to build SCENE-SEARCH API query
            from acquisition, spatial, and cloud filter
            outputs.

        ACQUSITION - Acquisition filter.
        SPATIAL - Spatial filter.
        CLOUD - Cloud cover filter.
        MONTHS - Seasonal filter (month numbers from 1 to 12) # Not used

        Ref. https://github.com/yannforget/landsatxplore/blob/master/landsatxplore/api.py#L563-L597
    """
    payload = {}
    payload['acquisitionFilter'] = acquisition
    payload['spatialFilter'] = spatial
    payload['cloudCoverFilter'] = cloud
    return payload


def build_ee_query_payload(start_date, end_date, aoi,
                           max_cc_pct = 100,
                           max_results = 500,
                           imagery_dataset = 'crssp_orderable_w3'):
    payload = {}

    data_filter = build_scene_filter(
        acquisition = build_acqusition_filter(start_date, end_date),
        spatial = build_spatial_filter(aoi),
        cloud = build_cloud_cover_filter(maximum = max_cc_pct)
    )
    
    params = {"datasetName": imagery_dataset,
              "sceneFilter": data_filter,
              "maxResults": max_results,
              "metadataType": "full",}
    
    return json.dumps(params)


def ee_login(session, username, token):
    """ Logs a user into Earth Explorer after they provide
            their username and password. Returns the session
            with their authorization token imbeded in the
            header.

        SESSION - A session

        Ref. https://github.com/yannforget/landsatxplore/blob/master/landsatxplore/api.py#L90-L104
    """
    payload = {"username": username, "token": token}

    url = "https://m2m.cr.usgs.gov/api/api/json/stable/login-token"
    
    r = session.post(url, json.dumps(payload))
    session.headers["X-Auth-Token"] = r.json().get("data")

    return session