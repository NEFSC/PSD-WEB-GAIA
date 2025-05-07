#!/usr/bin/env python
# coding: utf-8

import sqlite3
from glob import glob
import pyproj
from pyproj import CRS
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
import pandas as pd
import geopandas as gpd
import shapely
from shapely.ops import transform

dir_geojson = "../../data/geojson/aois"
db = "../../db.sqlite3"

def update_aoi(c, idd, name, utm, sqkm, geom):
    """ Insert/update the `aois` SQLite Data Table with a new Area of Interest.

        C - A cursor
        AOI ID - The AOI ID
        NAME - The location name
        UTM - The UTM Zone as an EPSG code
        SQKM - Square kilometers
        GEOM - The area of interest's geometry
    """
    sql_string = (f"INSERT INTO aoi(id, name, utm, sqkm, geom) \n"
                     f"VALUES ({idd}, \"{name}\", \"{utm}\", {sqkm}, ST_GeomFromText(\"{geom}\", 4326))")
    c.execute(sql_string)

def utm_and_area(aoi):
    """ Determines the UTM Zone, as an EPSG code, of an Area of Interest
            as well as culates the area, in square kilometers, of this
            Area of Interest.

        AOI - Area of Interest as a Shapely Polygon
    """
    minx, miny, maxx, maxy = aoi.bounds
    
    utm_crs_list = query_utm_crs_info(
        datum_name = "WGS 84",
        area_of_interest=AreaOfInterest(
            west_lon_degree = minx,
            south_lat_degree = miny,
            east_lon_degree = maxx,
            north_lat_degree = maxy,
        ),
    )

    if len(utm_crs_list) == 1:
        print("One zone, {}, was identified and will be used for calculations.".format(utm_crs_list[0].name))
    else:
        print("Multiple zones were identified. {} will be used for calculations.".format(utm_crs_list[0].name))
        alt_utms = [utm_crs.name for utm_crs in utm_crs_list][1:]
        print("\tOther options were: {}".format(alt_utms))
    
    utm_crs = CRS.from_epsg(utm_crs_list[0].code)
    proj_wgs2utm = pyproj.Transformer.from_crs(pyproj.CRS('EPSG:4326'), utm_crs, always_xy=True).transform
    sqkm = transform(proj_wgs2utm, aoi).area / 1_000_000
    return utm_crs, sqkm

def geojson_to_row(geojson):
    """ Creates a GeoDataFrame from a GeoJSON file then adds columns for
            the AOI ID, location name, UTM Zone (as an EPSG code), and
            area in square kilometers.

        Is dependent on the UTM_AND_AREA function above.

        GEOJSON - A GeoJSON file
    """
    try:
        gdf = gpd.read_file(geojson)
        root_name = geojson.split('/')[-1]
        
        if root_name and '-' in root_name:
            gdf['id'] = root_name.split('.')[0].split('-')[0]
            gdf['name'] = root_name.split('.')[0].split('-')[1]
        else:
            raise ValueError("GeoJSON filename does not follow the expected format: 'id-name.geojson'.")
        
        if len(gdf['geometry']) == 0:
            raise ValueError("GeoJSON file contains no geometries.")
        
        utm_crs, sqkm = utm_and_area(gdf['geometry'][0])
        gdf['utm'] = utm_crs.to_epsg()
        gdf['sqkm'] = round(sqkm, 2)
        return gdf
    except Exception as e:
        print("Failed on {} due to: {}".format(geojson, e))
        return None


# ### Read GeoJSONs into GeoDataFrame
# Determine which EPSG, or WKID, cover the Area of Interest the best while reading the GeoJSON file in as a GeoDataFrame. Show if there are any issues with locally projecting to the end user. Reproject all GeoDataFrames from their local, UTM projection to EPSG 4326, better known as WGS84. Concactenate the GeoDataFrames into a single GeoDataFrame. Show the GeoDataFrame's head to the end user.

aoi_geojsons = glob(dir_geojson + "/*.geojson")
aoi_dfs = []
for aoi_geojson in aoi_geojsons:
    print(aoi_geojson)
    try:
        aoi_dfs.append(geojson_to_row(aoi_geojson))
    except Exception as e:
        print(f"Failed on {aoi_geojson} with exception {e}")

aois_4326 = []
for aoi_df in aoi_dfs:
    try:
        aois_4326.append(aoi_df.to_crs("EPSG:4326"))
    except Exception as e:
        print(f"Failed on {aoi_df} with exception {e}")

gdf = pd.concat(aois_4326, ignore_index=True)
corrected_columns = ['id', 'name', 'utm', 'sqkm', 'geometry']
gdf = gdf[corrected_columns]
gdf.head()

# ### Filter to only Polygons, force to just Polygon
# The `aoi` table will have a geometry of Polygon; so we filter to only Polygons, excluding Multi Polygons. Some returned Polygons are veritcally, or Z, enabled. FOrce these to be just Polygons.

print(f"Your initial GeoDataFrame had the shape {gdf.shape}")
gdf = gdf[gdf['geometry'].type == 'Polygon']
gdf['geometry'] = gdf.force_2d()
print(f"Your resulting GeoDataFrame has the shape {gdf.shape}")
gdf.head()

# ### Connect to databse and create `aoi` table
conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS aoi(
        id INTEGER PRIMARY KEY,
        name VARCHAR(50),
        requestor VARCHAR(25),
        utm VARCHAR(10),
        sqkm NUMERIC(10, 2)
    )
''')
c.execute('''SELECT AddGeometryColumn('aoi', 'geom', 4326, 'POLYGON')''')

c = conn.cursor()

for i, row in gdf.iterrows():
    try:
        update_aoi(c, row['id'], row['name'], row['utm'], row['sqkm'], row['geometry'])
    except Exception as e:
        print("Exception: {} was raised for AOI ID {}".format(e, row['id']))
print("Done updating AOI table!")

main_columns = list(gdf.columns)[:-1]
main_columns = ', '.join(main_columns)
df = pd.read_sql_query(f"SELECT {main_columns}, AsText(geom) FROM aoi", conn)
df = df.rename(columns={'AsText(geom)': 'geometry'}, errors='raise')
df['geometry'] = shapely.wkt.loads(df['geometry'])
gdf = gpd.GeoDataFrame(df, geometry='geometry')
gdf.to_csv("../../data/aoi.csv", index=False)

conn.commit()
conn.close()

