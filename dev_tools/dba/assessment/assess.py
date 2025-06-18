# ------------------------------------------------------------------------------
#
# Compares and contrasts entries within EE, GEGD, and MGP tables.
#
# Written by John Wall (john.wall@noaa.gov)
#
# N.B.: Orignially written as a Jupyter Notebook, limited validation has been done.
#
# ------------------------------------------------------------------------------

# Import libraries
import sqlite3
import shapely
import pandas as pd
import geopandas as gpd
import folium

import sys; sys.path.append("../../")
from dba import utilities

# User defined variables
db = "../../db.sqlite3"
aoi_id = 6

# Show distinct Area of Interest Identifiers, count Entity Identifiers
conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

sql_string = '''SELECT DISTINCT aoi_id_id, COUNT(entity_id)
                    FROM animal_earthexplorer
                    GROUP BY aoi_id_id
             '''
df = pd.read_sql_query(sql_string, conn)

conn.commit()
conn.close()

df.head()

# Show some Catalog Identifiers from Cape Cod Bay
conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

sql_string = ''' SELECT DISTINCT catalog_id FROM animal_earthexplorer WHERE aoi_id_id = 6'''
df = pd.read_sql_query(sql_string, conn)

conn.commit()
conn.close()

df.head()

# Output the above Cape Cod Bay Catalog Identifiers to a CSV
df.to_csv('../outputs/wv_ccb.csv')

# Illustrate that Catalog Identifiers are non-unique
conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

sql_string = ''' SELECT * FROM animal_earthexplorer WHERE catalog_id = '10400100674B2100' '''
df = pd.read_sql_query(sql_string, conn)

conn.commit()
conn.close()

df.head()

# Export the non-unique Catalog Identifiers to a CSV
df.to_csv('../outputs/wv3_10400100674B2100_ids.csv')

# Display the DataFrame
df

# Select all records associated with a user defined AOI ID, show the table
## Use `ee` as an example
conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

sql_string = '''SELECT * FROM animal_earthexplorer WHERE aoi_id_id = {}'''.format(aoi_id)

df = pd.read_sql_query(sql_string, conn)

conn.commit()
conn.close()

print(df.shape)
df.head()

# Inner Join
## Show images that are in both `ee` and `mgp`. Note that the forgein key for
##      `ee` is catalog_id whereas this value corresponds to the primary key
##      id in `mgp`. There is M:1 relationship between these records.
conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

sql_string = '''SELECT a.id, b.catalog_id, AsText(a.bbox)
                    FROM animal_maxargeospatialplatform AS a
                    INNER JOIN animal_earthexplorer AS b
                    ON b.catalog_id = a.id
                    WHERE (a.aoi_id_id = {})
             '''.format(aoi_id)

df = pd.read_sql_query(sql_string, conn)
df = df.rename(columns={'AsText(a.bbox)': 'geometry'}, errors='raise')
df['geometry'] = shapely.wkt.loads(df['geometry'])
gdf = gpd.GeoDataFrame(df, geometry='geometry')

conn.commit()
conn.close()

print(gdf.shape)
gdf.head()

len(set(gdf['catalog_id']))

# Left Outer Join 1
## Select images that are present in `mgp`, but not `ee`
conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

sql_string = '''SELECT a.id, b.catalog_id, a.platform, AsText(a.bbox), a.datetime
                    FROM animal_maxargeospatialplatform AS a
                    LEFT OUTER JOIN animal_earthexplorer AS b
                    ON a.id = b.catalog_id
                    WHERE b.catalog_id IS NULL
                    AND (a.aoi_id_id = {})
             '''.format(aoi_id)

df = pd.read_sql_query(sql_string, conn)
df = df.rename(columns={'AsText(a.bbox)': 'geometry'}, errors='raise')
df['geometry'] = shapely.wkt.loads(df['geometry'])
gdf_ee = gpd.GeoDataFrame(df, geometry='geometry')

conn.commit()
conn.close()

print(gdf_ee.shape)
gdf_ee.head()

# Left Outer Join 2
## Select images that are present in `ee`, but not `mgp`
conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

sql_string = '''SELECT a.catalog_id, b.id, a.satellite, AsText(a.bounds), a.publish_date
                    FROM animal_earthexplorer AS a
                    LEFT OUTER JOIN animal_maxargeospatialplatform AS b
                    ON a.catalog_id = b.id
                    WHERE b.id IS NULL
                    AND (a.aoi_id_id = {})
             '''.format(aoi_id)

df = pd.read_sql_query(sql_string, conn)
df = df.rename(columns={'AsText(a.bounds)': 'geometry'}, errors='raise')
df['geometry'] = shapely.wkt.loads(df['geometry'])
gdf_mgp = gpd.GeoDataFrame(df, geometry='geometry')

conn.commit()
conn.close()

print(gdf_mgp.shape)
gdf_mgp.head()

# Plot differences
gdf_aoi = functions.get_aoi(db, aoi_id)

def style_function(hex_value):
    return {'color': hex_value, 'fillOpacity': 0}

## Add OpenStreetMap as a basemap
map = folium.Map()
folium.TileLayer('openstreetmap').add_to(map)

## Create a GeoJson layer from the response_geojson and add it to the map
## Blue
folium.GeoJson(
    gdf_ee.to_json(),
    style_function = lambda x: style_function('#0000FF')
).add_to(map)

## Red
folium.GeoJson(
    gdf_mgp.to_json(),
    style_function = lambda x: style_function('#FF0000')
).add_to(map)

## Black
folium.GeoJson(
    gdf_aoi['geometry'].to_json(),
    style_function = lambda x: style_function('#000000')
).add_to(map)

## Zoom to collected images
map.fit_bounds(map.get_bounds(), padding=(100, 100))

## Display the map
map