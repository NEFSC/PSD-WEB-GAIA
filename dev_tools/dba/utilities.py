import sqlite3
from datetime import datetime
import shapely
from shapely.geometry import box, Polygon
import pandas as pd
import geopandas as gpd
import folium

def quick_map(gdf_imagery, json_aoi):
    """ Creates a folium map to show imagery added to the database.

        GDF IMAGERY - A GeoDataFrame of imagery added to the
            database
        JSON AOI - The area of interest as a GeoJSON string
    """
    def style_function(hex_value):
        return {'color': hex_value, 'fillOpacity': 0}
    
    # Add OpenStreetMap as a basemap
    map = folium.Map()
    folium.TileLayer('openstreetmap').add_to(map)
    
    # Create a GeoJson layer from the response_geojson and add it to the map
    folium.GeoJson(
        gdf_imagery['geometry'].to_json(),
        style_function = lambda x: style_function('#0000FF')
    ).add_to(map)
    
    # AOI
    folium.GeoJson(
        json_aoi,
        style_function = lambda x: style_function('#FF0000')
    ).add_to(map)
    
    # Zoom to collected images
    map.fit_bounds(map.get_bounds(), padding=(100, 100))
    
    # Display the map
    return map

def validate_updates(db, table, gdf, dar_id):
    """ Selects updated records within a database table by DAR ID.

        DB - A database file (.db)
        TABLE - Table to be updated (e.g., ee, mgp, gegd)
        DAR ID - DAR Area of Interest Number
    """
    conn = sqlite3.connect(db)
    conn.enable_load_extension(True)
    conn.execute("SELECT load_extension('mod_spatialite')")
    
    columns_list = list(gdf.columns[:-1])
    columns_str = ', '.join(columns_list)
    
    if table == 'ee':
        sql_string = "SELECT {}, AsText(bounds) FROM ee WHERE entity_id IS NOT NULL AND aoi_id = {}".format(columns_str, dar_id)
    elif table == 'mgp':
        sql_string = "SELECT {}, AsText(bbox) FROM mgp WHERE id IS NOT NULL AND aoi_id = {}".format(columns_str, dar_id)
    elif table == 'gegd':
        sql_string = "SELECT {}, AsText(geometry) FROM gegd WHERE id IS NOT NULL AND aoi_id = {}".format(columns_str, dar_id)
    
    df = pd.read_sql_query(sql_string, conn)
    
    if table == 'ee':
        df = df.rename(columns={'AsText(bounds)': 'geometry'}, errors='raise')
    elif table == 'mgp':
        df = df.rename(columns={'AsText(bbox)': 'geometry'}, errors='raise')
    if table == 'gegd':
        df = df.rename(columns={'AsText(geometry)': 'geometry'}, errors='raise')
        
    df['geometry'] = shapely.wkt.loads(df['geometry'])
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    
    conn.commit()
    conn.close()
    
    return gdf

def update_gegd(c, iid, column_name, column_value):
    """ Updates GEGD table values of a given column with a given value using the 
            ID as the selection criteria for the update.

        C - A cursor
        ENTITY ID - An ID from  Global Enhanced GEOINT Delivery
        COLUMN NAME - A column name within the EE table to be updated
        COLUMN VALUE - A value to update the column
    """
    force_string_list = ['legacy_id', 'factory_order_number', 'source', 'source_unit',
                        'product_type', 'data_layer', 'legacy_description',
                        'color_band_order', 'asset_name', 'crs_from_pixels',
                        'company_name', 'copyright']
    force_date_list = ['acquisition_date', 'ingest_date']
    force_geom_list = ['geometry']
    
    if column_name in force_string_list:
        sql_string = f"UPDATE gegd SET {column_name} = \"{column_value}\" WHERE id = \"{iid}\""
        c.execute(sql_string)

    elif column_name in force_date_list:
        sql_string = f"UPDATE gegd SET {column_name} = "
        sql_string = sql_string + "? WHERE id = ?"
        c.execute(sql_string, (column_value, iid))
    
    elif column_name in force_geom_list:
        sql_string = f"UPDATE gegd SET {column_name} = GeomFromText(\"{column_value}\") WHERE id = \"{iid}\""
        c.execute(sql_string)
    
    else:
        sql_string = f"UPDATE gegd SET {column_name} = {column_value} WHERE id = \"{iid}\""
        c.execute(sql_string)

def update_mgp(c, entity_id, column_name, column_value):
    """ Updates EE table values of a given column with a given value using the 
            ENTITY ID as the selection criteria for the update.

        C - A cursor
        ENTITY ID - An entity id from EarthExplorer
        COLUMN NAME - A column name within the EE table to be updated
        COLUMN VALUE - A value to update the column
    """
    force_string_list = ['platform', 'instruments']
    force_date_list2 = ['datetime']
    force_geom_list = ['bbox']
    
    if column_name in force_string_list:
        sql_string = f"UPDATE mgp SET {column_name} = \"{column_value}\" WHERE id = \"{entity_id}\""
        c.execute(sql_string)
    
    elif column_name in force_date_list2:
        sql_string = f"UPDATE mgp SET {column_name} = "
        sql_string = sql_string + "? WHERE id = ?"
        c.execute(sql_string, (column_value, entity_id))
    
    elif column_name in force_geom_list:
        sql_string = f"UPDATE mgp SET {column_name} = GeomFromText(\"{column_value}\") WHERE id = \"{entity_id}\""
        c.execute(sql_string)
    
    else:
        sql_string = f"UPDATE mgp SET {column_name} = {column_value} WHERE id = \"{entity_id}\""
        c.execute(sql_string)

def update_ee(c, entity_id, column_name, column_value):
    """ Updates EE table values of a given column with a given value using the 
            ENTITY ID as the selection criteria for the update.

        C - A cursor
        ENTITY ID - An entity id from EarthExplorer
        COLUMN NAME - A column name within the EE table to be updated
        COLUMN VALUE - A value to update the column
    """
    force_string_list = ['catalog_id', 'vendor', 'vendor_id', 'satellite', 'sensor',
                            'map_projection', 'datum', 'processing_level', 'file_format',
                            'event', 'thumbnail']
    force_date_list = ['acquisition_date', 'date_entered']
    force_date_list2 = ['publish_date']
    force_geom_list = ['bounds']
    
    if column_name in force_string_list:
        sql_string = f"UPDATE ee SET {column_name} = \"{column_value}\" WHERE entity_id = \"{entity_id}\""
        c.execute(sql_string)
    
    elif column_name in force_date_list:
        # print("\t\tTrying to strip the value: {}".format(column_value))
        date_obj = datetime.strptime(column_value, "%Y/%m/%d")
        column_value = date_obj.strftime("%Y-%m-%d")
        sql_string = f"UPDATE ee SET {column_name} = "
        sql_string = sql_string + "? WHERE entity_id = ?"
        c.execute(sql_string, (column_value, entity_id))
    
    elif column_name in force_date_list2:
        sql_string = f"UPDATE ee SET {column_name} = "
        sql_string = sql_string + "? WHERE entity_id = ?"
        c.execute(sql_string, (column_value, entity_id))
    
    elif column_name in force_geom_list:
        sql_string = f"UPDATE ee SET {column_name} = GeomFromText(\"{column_value}\") WHERE entity_id = \"{entity_id}\""
        c.execute(sql_string)
    
    else:
        sql_string = f"UPDATE ee SET {column_name} = {column_value} WHERE entity_id = \"{entity_id}\""
        c.execute(sql_string)

def database_activity(db, table, entity_id, column_name, column_value, activity='update'):
    """ Wrapper function for activities related to database management.
            Currently only supports UPDATING based on EarthExplorer 
            Entity ID values.

        Is dependent on the UPDATE_EE and UPDATE_MGP functions above.

        DB - A database file (.db)
        TABLE - Table to be updated (e.g., ee, mgp, gegd)
        ENTITY ID - An EarthExplorer Entity ID uniquely identifying
            the record of interest.
        COLUMN NAME - The column to be updated
        COLUMN VALUE - The value of the column to be updated
        ACTIVITY - The activity to be carried out. Currently only
            supports UPDATE.
    """
    conn = sqlite3.connect(db)
    conn.enable_load_extension(True)
    conn.execute("SELECT load_extension('mod_spatialite')")
    c = conn.cursor()

    if activity == 'update':
        try:
            if table == 'ee':
                update_ee(c, entity_id, column_name, column_value)
            elif table == 'mgp':
                update_mgp(c, entity_id, column_name, column_value)
            elif table == 'gegd':
                update_gegd(c, entity_id, column_name, column_value)
        except Exception as e:
            print("Exception: {} was raised for Entity ID {}".format(e, entity_id))
    else:
        print("Your activity method is not currently supported.")
    
    conn.commit()
    conn.close()

def insert_ee(c, entity_id):
    """ Inserts EarthExplorer Entity IDs into the EE Data Table.
            The Entity ID is the Primary Key for the datatable
            since it is unique

        C - A cursor
        ENTITY ID - An Entity ID value from EarthExplorer
    """
    sql_string = f"INSERT INTO ee(entity_id) VALUES (\"{entity_id}\")"
    print(sql_string)
    c.execute(sql_string)

def insert_mgp(c, iid):
    """ Inserts Maxar Geospatial Platform IDs into the MGP Data Table.
            The IDs are the Primary Key for the datatable since it is
            unique

        C - A cursor
        ID - An ID value from Maxar Geospatial Platform
    """
    sql_string = f"INSERT INTO mgp(id) VALUES (\"{iid}\")"
    c.execute(sql_string)

def insert_gegd(c, iid):
    """ Inserts Global Enhanced GEOINT Delivery IDs into the GEGD Data Table.
            The IDs are the Primary Key for the datatable since it is
            unique

        C - A cursor
        ID - An ID value from  Global Enhanced GEOINT Delivery
    """
    sql_string = f"INSERT INTO gegd(id) VALUES (\"{iid}\")"
    c.execute(sql_string)

def insert_pk(db, table, gdf):
    """ Inserts primary key (pk) values into a given table from a
            GeoDataFrame. This could be entity_id values for the
            ee table or ids for the mgp table among other options.

        Is dependent on the INSERT_EE, INSERT_MGP, and INSERT_GEGD
            functions above.
            
        DB - A database (.db) file
        TABLE - Table to be updated (e.g., ee, mgp, gegd)
        GDF - A GeoDataFrame returned from one of the "gdf_*"
            functions such as "gdf_from_ee"
    """
    conn = sqlite3.connect(db)
    conn.enable_load_extension(True)
    conn.execute("SELECT load_extension('mod_spatialite')")
    
    c = conn.cursor()
    
    for i, row in gdf.iterrows():
        try:
            if table == 'ee':
                insert_ee(c, row['entity_id'])
            elif table == 'mgp':
                insert_mgp(c, row['entity_id'])
            elif table == 'gegd':
                insert_gegd(c, row['entity_id'])
        except Exception as e:
            print("Exception: {} was raised for ID {}".format(e, row['entity_id']))
    print("Done inserting Imagery IDs into table!")
    conn.commit()
    conn.close()

def gdf_from_gegd(results, dar_id):
    """ Creates a GeoDataFrame from Global Enhanced GEOINT Delivery (GEGD)
            results with columns ready to be added to the SQLite database

        RESULTS - Results from querying Global Enhanced GEOINT Delivery API
        DAR ID - DAR ID number
    """
    df = pd.DataFrame()
    
    for i, record in enumerate(results['features']):
        df.loc[i, 'id'] = record['id']
        df.loc[i, 'aoi_id'] = dar_id
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
        df.loc[i, 'ground_sample_distance'] = record['properties']['groundSampleDistance']
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
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    return gdf.set_crs(4326)

def gdf_from_mgp(results, dar_id):
    """ Creates a GeoDataFrame from Maxar Geospatial Platform results with columns
            ready to be added to the SQLite database.

        RESULTS - Results from querying the Maxar Geospatial Platform API
        DAR ID - DAR ID number
    """    
    columns = ["id", "platform", "instruments", "gsd", "pan_resolution_avg",
               "multi_resolution_avg", "datetime", "off_nadir", "azimuth",
               "sun_azimuth", "sun_elevation", "bbox"]
    gdf = gpd.GeoDataFrame(columns = columns)
    gdf = gdf.set_geometry("bbox").set_crs("EPSG:4326")
    
    r = results.json()
    for i, feature in enumerate(r["features"]):
        gdf.loc[i, "id"] = feature["id"]
        gdf.loc[i, "aoi_id"] = dar_id
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
        gdf.loc[i, "bbox"] = box(*feature["bbox"])

    return gdf

def gdf_from_ee(results, dar_id):
    """ Creates a GeoDataFrame from EarthExplorer results with columns
            ready to be added to the SQLite database.

        RESULTS - Results from querying the EarthExplorer API
        DAR ID - DAR ID number
    """
    # Create a GeoDataFrame from query results
    r = results.json()
    results_data = r['data']['results']
    columns = [field['fieldName'] for field in results_data[0]['metadata']]
    gdf = gpd.GeoDataFrame(columns = columns)
    
    for result in results_data:
        gdf.loc[gdf.shape[0]] = [field['value'] for field in result['metadata']]
    
    gdf['thumbnail'] = pd.Series([result['browse'][0]['thumbnailPath'] for result in results_data])
    gdf['publish_date'] = pd.Series([result['publishDate'] for result in results_data])
    gdf['bounds'] = gpd.GeoSeries([Polygon(result['spatialBounds']['coordinates'][0]) for result in results_data])
    gdf = gdf.set_geometry("bounds").set_crs("EPSG:4326")
    
    drop_columns = [column for column in columns if "Corner" in column] + ['Center Latitude', 'Center Longitude']
    gdf = gdf.drop(drop_columns, axis=1)

    # Update column names to database-safe version
    column_list = list(gdf.columns)
    column_update = {}
    for column_name in column_list:
        column_update[column_name] = column_name.lower().replace(" ", "_")
    
    gdf = gdf.rename(columns=column_update)

    # Drop some columns, add DAR ID
    #     UTM Zone, License Uplift Update, and Event Date never seem to
    #     have anything useful in them. Just drop them.
    drop_columns = ['utm_zone']
    gdf = gdf.drop(columns=drop_columns)
    gdf.insert(loc = 1, column = 'aoi_id', value = dar_id)

    return gdf

def get_aoi(db, dar_id):
    """ Returns the DAR Area of Interest as a GeoDataFrame when
            provided with the Database and the DAR ID.

        DB - Database (.db) file
        DAR ID - DAR Area of Interest Number
    """
    conn = sqlite3.connect(db)
    conn.enable_load_extension(True)
    conn.execute("SELECT load_extension('mod_spatialite')")
    
    c = conn.cursor()
    
    sql_string = f"SELECT id, name, sqkm, AsText(geometry) FROM animal_areaofinterest WHERE id={dar_id}"
    df = pd.read_sql_query(sql_string, conn)
    df = df.rename(columns={'AsText(geometry)': 'geometry'}, errors='raise')
    df['geometry'] = shapely.wkt.loads(df['geometry'])
    gdf_aoi = gpd.GeoDataFrame(df, geometry='geometry')
    
    conn.commit()
    conn.close()
    
    return gdf_aoi

def select_data(c, columns):
    """ Selects all data from the `aois` table for review

        C - A cursor
        COLUMNS - Columns of interest
    """
    columns = ', '.join(columns)
    sql_string = f"SELECT {columns}, AsText(geom) FROM aois"
    c.execute(sql_string)
    return c.fetchall()

def update_aoi(c, dar_id, name, utm, sqkm, geom):
    """ Insert/update the `aois` SQLite Data Table with a new Area of Interest.

        C - A cursor
        DAR ID - The DAR ID
        NAME - The location name
        UTM - The UTM Zone as an EPSG code
        SQKM - Square kilometers
        GEOM - The area of interest's geometry
    """
    sql_string = (f"INSERT INTO aois(aoi_id, name, utm, sqkm, geom) \n"
                     f"VALUES ({dar_id}, \"{name}\", \"{utm}\", {sqkm}, GeomFromText(\"{geom}\"))")
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
            the DAR ID, location name, UTM Zone (as an EPSG code), and
            area in square kilometers.

        Is dependent on the UTM_AND_AREA function above.

        GEOJSON - A GeoJSON file
    """
    try:
        gdf = gpd.read_file(geojson, crs='EPSG:4326')
        root_name = geojson.split('/')[-1]
        gdf['aoi_id'] = root_name.split('.')[0].split('-')[0]
        gdf['name'] = root_name.split('.')[0].split('-')[1]
        utm_crs, sqkm = utm_and_area(gdf['geometry'][0])
        gdf['utm'] = utm_crs
        gdf['sqkm'] = round(sqkm, 2)
        return gdf
    except Exception as e:
        print("Failed on {} due to: {}".format(geojson, e))
        pass

def kml_to_geojson(kml, out_dir):
    """ Converts a KML file to GeoJSON file.

        KML - KML file
        OUT DIR - Output directory
    """
    supported_drivers['KML'] = 'rw'

    kml_name = kml.split('\\')[-1]
    gdf = gpd.read_file(kml, driver='KML')
    if len(gdf["geometry"]) == 1:
        kml_shape = to_geojson(gdf['geometry'][0])

        root_name = kml_name.split('.')[0]
        geojson_file = "{}/{}.geojson".format(out_dir, root_name)
        with open(geojson_file, "w") as f:
            f.write(kml_shape)
            f.close()
        
        with open(geojson_file, "r") as f:
            aoi = json.loads(f.read())
            f.close()

        return geojson_file
            
    elif len(gdf["geometry"]) > 1:
        print("More than one geometry found in your {} KML. Passing...".format(kml_name))
        pass