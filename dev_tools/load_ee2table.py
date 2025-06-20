# ------------------------------------------------------------------------------
#
# Using an Area of Interest (AOI) from the `aoi` SQLite Database, queries the
#      EarthExplorer API for data over a given time period, updates the `ee`
#      table from these results, and then populates the table with these values.
#      Other notebooks should be used for adding additional records to the table.
#
# Written by John Wall (john.wall@noaa.gov)
#
# N.B.: Orignially written as a Jupyter Notebook, limited validation has been done.
#
# ------------------------------------------------------------------------------


# Basic stack
from datetime import datetime

# Web Stack
import json
import requests

# Database stack
import sqlite3

# Data Science stack
import shapely
from shapely.geometry import Polygon
import pandas as pd
import geopandas as gpd
import folium

# Custom stack
import sys; sys.path.append("../../")
from SDB import utilities
from EE import security, search

# User defined variables
dar_id = '6'
datasetName = 'crssp_orderable_w3'
start_date = '2009-10-08'
end_date = '2024-05-31'
db = "C:/gis/gaia/data/databases/gaia.db"

# Log-in to EarthExplorer
session = requests.Session()
session = security.ee_login(session)

# Retreve the Area of Interest record from the `aoi` table corresponding to the supplied DAR ID
gdf_aoi = functions.get_aoi(db, dar_id)

# Create the querying payload for EarthExplorer
### This needs to be handled by search.GEOJSON_FOR_EE
gdf_json = json.loads(gdf_aoi['geometry'].to_json())['features'][0]['geometry']

payload = {}

data_filter = search.build_scene_filter(
    acquisition = search.build_acqusition_filter(start_date, end_date),
    spatial = search.build_spatial_filter(gdf_json),
    cloud = search.build_cloud_cover_filter()
)

max_results = 10_000

params = {"datasetName": datasetName,
          "sceneFilter": data_filter,
          "maxResults": max_results,
          "metadataType": "full",}

data = json.dumps(params)

# Query EarthExplorer for data
url = "https://m2m.cr.usgs.gov/api/api/json/stable/scene-search"

results = session.get(url=url, data=data)
print(results.status_code)

results.json()

# Create a GeoDataFrame from query results
gdf = functions.gdf_from_ee(results, dar_id)
print(gdf.shape)
gdf.head()

# Insert EarthExplorer Entity IDs into `ee` table
functions.insert_pk(db, 'ee', gdf)

# Update `ee` records from EarthExplorer results
gdf[gdf['entity_id'] == 'WV320240527205854M00']

columns = gdf.columns[1:]
for i, row in gdf.iterrows():
    eid = row['entity_id']
    # print("Updating information for Entity ID: {}".format(eid))
    for column in columns:
        if row[column] is None:
            print("\tSkipping updating {} with value {} since it's None".format(column, row[column]))
        else:
            # print("EID: {}; COLUMNS: {}; DATA: {}".format(eid, column, row[column]))
            functions.database_activity(db, 'ee', eid, column, row[column])

# Select newly inserted AOIs, make a GeoDataFrame for validation
gdf = functions.validate_updates(db, 'ee', gdf, dar_id)
# Note that the GDF shape matches that from the above
print(gdf.shape)
gdf.head()

conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

columns_list = list(gdf.columns[:-1])
columns_str = ', '.join(columns_list)
sql_string = "SELECT {}, AsText(bounds) FROM ee WHERE vendor IS NOT NULL AND aoi_id = {}".format(columns_str, dar_id)

df = pd.read_sql_query(sql_string, conn)
df = df.rename(columns={'AsText(bounds)': 'geometry'}, errors='raise')
df['geometry'] = shapely.wkt.loads(df['geometry'])
gdf = gpd.GeoDataFrame(df, geometry='geometry')

conn.commit()
conn.close()

# Note that the GDF shape matches that from the above
print(gdf.shape)
gdf.head()

# Plot Areas of Interest on an Interactive Map
mp = functions.quick_map(gdf, gdf_json)
mp