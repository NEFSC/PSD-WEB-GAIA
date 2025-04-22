# Written by John Wall (john.wall@noaa.gov)
#
# Functions for initializing the SpatiaLite Database for the WHALE system



# Import Libraries
import sqlite3


def initialize_spatialite(db):
    """ When provided with a path to a SQLite database, initializes
            the SpatiaLite components of the database.

        DB - Path to a database 
    """
    
    conn = sqlite3.connect(db)
    conn.enable_load_extension(True)
    conn.execute("SELECT load_extension('mod_spatialite')")
    
    c = conn.cursor()
    c.execute('''SELECT InitSpatialMetaData();''')
    conn.commit()
    conn.close()

def drop_table_if_exists(db, table_name):
    """ When provided with a path to a SpatiaLite database and a table name
            within that database, drop that table from that database so long
            as it exists within that table.

        DB - Path to database
        TABLE NAME - Name of table within DB
    """
    
    try:
        conn = sqlite3.connect(db)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('mod_spatialite')")
        
        c = conn.cursor()
        c.execute(f'''DROP TABLE IF EXISTS {table_name}''')
        conn.commit()
        conn.close()

        print(f"Successfully dropped table {table_name}, if it existed...")
        
    with Exception as e:
        print(f"Failed to drop table with exception: {e}")

def drop_trigger(db, trigger_name):
    """ When provided with a path to a SpatiaLite database and a trigger name
            within that database, drop that trigger from that database so long
            as it exists.

        DB - Path to database
        TRIGGER NAME - Name of trigger within the DB.
    """
    
    try:
        conn = sqlite3.connect(db)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('mod_spatialite')")
        
        c = conn.cursor()
        c.execute(f'''DROP TRIGGER IF EXISTS {trigger_name}''')
        conn.commit()
        conn.close()

        print(f"Successfully dropped trigger {trigger_name}, if it existed...")
        
    with Exception as e:
        print(f"Failed to drop table with exception: {e}")

def create_aois(db):
    """ When provided with a path to a SpatiaLite database, create the
            table WHALE AREASOFINTEREST if it does not exist.

        FIELDS: ID, Name, Requestor, and SqKm

        NOTES:
            - If table does exist, execution will error out.
            - Table is created with EPSG or WKID code 4326, the standard
                projection for spatial data. This code equates to WGS84.
            - This table assumes areas of interest will be polygons opposed
                to other data types like polylines, lines, etc.

        DB - Path to database
    """

    try:
        conn = sqlite3.connect(db)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('mod_spatialite')")
        
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS whale_areaofinterest(
                id INTEGER PRIMARY KEY,
                name VARCHAR(50),
                requestor VARCHAR(25),
                sqkm NUMERIC(10, 2)
            )
        ''')
        
        c.execute('''SELECT AddGeometryColumn('whale_areaofinterest', 'geom', 4326, 'POLYGON')''')
        
        conn.commit()
        conn.close()

        print("Successfully created table WHALE AREASOFINTEREST")
    
    with Exception as e:
        print(f"Failed to create table with exception: {e}")

def create_targets(db):
    """ When provided with a path to a SpatiaLite database, create the
            table WHALE TARGETS if it does not exist. Targets are target
            species.

        FIELDS: ID, Target, and Scientific Name

        DB - Path to database
    """

    try:
        conn = sqlite3.connect(db)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('mod_spatialite')")
        
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS whale_targets(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target VARCHAR(30),
                scientific_name VARCHAR(25),
            )
        ''')
        
        conn.commit()
        conn.close()

        print("Successfully created table WHALE TARGETS")
    
    with Exception as e:
        print(f"Failed to create table with exception: {e}")

def create_people(db):
    """ When provided with a path to a SpatiaLite database, create the
            table WHALE PEOPLE if it does not exist. These are the people
            who are tasking for collection or managing projects within
            WHALE opposed to end users.

        FIELDS: ID, Name, Email, Organization, Sub-Organization,
            and Location.

        DB - Path to database
    """

    try:
        conn = sqlite3.connect(db)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('mod_spatialite')")
        
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS whale_people(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(20),
                email VARCHAR(30),
                organization VARCHAR(25),
                sub_organization VARCHAR(50),
                location VARCHAR(50)
            )
        ''')
        
        conn.commit()
        conn.close()

        print("Successfully created table WHALE PEOPLE")
    
    with Exception as e:
        print(f"Failed to create table with exception: {e}")

def create_tasking(db):
    """ When provided with a path to a SpatiaLite database, create the
            table WHALE TASKING if it does not exist. Taskings represent
            who is tasking where for what collection of what.

        FIELDS: ID, DAR, AOI, Location, Target, Requestor, Vendor,
            Mono or Stero, Date Entered, Aquisition Start, Aquisition
            End, Off Nadir Angle (ONA) for WorldView-2, ONA for
            WorldView-3, Tasking Description, Comments, Status,
            Output Format, Processing Level, Website Link, and
            Permission to Share.
            
        DB - Path to database
    """

    try:
        conn = sqlite3.connect(db)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('mod_spatialite')")
        
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS whale_tasking(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dar INTEGER,
                aoi INTEGER,
                location VARCHAR(12),
                target VARCHAR(30),
                requestor VARCHAR(16),
                vendor VARCHAR(10),            -- Missing from Tracking?
                mono_stereo VARCHAR(6),        -- Missing from Tracking?
                date_entered DATE,
                acquisition_start DATE,
                acquisition_end DATE,
                ona_wv2 VARCHAR(10),
                ona_wv3 VARCHAR(10),
                tasking_description VARCHAR(100),
                comments VARCHAR(250),
                status VARCHAR(8),
                output_format VARCHAR(7),
                processing_level VARCHAR(41),
                website_link VARCHAR(50),
                permission_to_share VARCHAR(500),
                FOREIGN KEY (aoi)
                    REFERENCES aoi(id),
                FOREIGN KEY (target)
                    REFERENCES targets(target),
                FOREIGN KEY (requestor)
                    REFERENCES people(name)
            )
        ''')
        
        conn.commit()
        conn.close()

        print("Successfully created table WHALE TASKING")
    
    with Exception as e:
        print(f"Failed to create table with exception: {e}")

def create_earthexplorer(db):
    """ When provided with a path to a SpatiaLite database, create the
            table WHALE EARTHEXPLORER if it does not exist.

        FIELDS: Entity ID, AOI ID, Catalog ID, Acquisition Date, Vendor
            Vendor ID, Cloud Cover, Satellite, Sensor, Number of Bands,
            Map Projection, Datum, Processing Level, File Format,
            License ID, Sun Azimuth, Sun Elevation, Pixel Size X,
            Pixel Size Y, License Uplift Update, Event, Event Date,
            Date Entered, Center Latitude Decimal Degrees,
            Center Longitude Decimal Degrees, Thumbnail, Publish Date,
            and Bounds.
            
        DB - Path to database
    """

    try:
        conn = sqlite3.connect(db)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('mod_spatialite')")
        
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS whale_earthexplorer(
                entity_id VARCHAR(20) PRIMARY KEY,
                aoi_id VARCHAR(4),
                catalog_id VARCHAR(16),
                acquisition_date DATE,
                vendor VARCHAR(18),
                vendor_id VARCHAR(39),
                cloud_cover NUMERIC(3),
                satellite VARCHAR(11),
                sensor VARCHAR(3),
                number_of_bands NUMERIC(1),
                map_projection VARCHAR(3),
                datum VARCHAR(5),
                processing_level VARCHAR(3),
                file_format VARCHAR(7),
                license_id NUMERIC(1),
                sun_azimuth NUMERIC(3, 2),
                sun_elevation NUMERIC(2, 2),
                pixel_size_x NUMERIC(2, 2),
                pixel_size_y NUMERIC(2, 2),
                license_uplift_update DATE,
                event VARCHAR(5),
                event_date DATE,
                date_entered DATE,
                center_latitude_dec NUMERIC(2, 6),
                center_longitude_dec NUMERIC(3, 6),
                thumbnail VARCHAR(76),
                publish_date DATETIME2,
                bounds POLYGON,
                FOREIGN KEY (aoi_id)
                    REFERENCES aoi(id)
            )
        ''')
        
        conn.commit()
        conn.close()

        print("Successfully created table WHALE EARTHEXPLORER")
    
    with Exception as e:
        print(f"Failed to create table with exception: {e}")

def create_geointdiscovery(db):
    """ When provided with a path to a SpatiaLite database, create the
            table WHALE GEOINTDISCOVERY if it does not exist.

        FIELDS: ID, AOI ID, Legacy ID, Facordy Order Number,
            Acquisition Date, Source, Source Unit, Product Type,
            Cloud Cover, Off Nadir Angle, Sun Elevation, Sun
            Azimuth, Ground Sample Distance, Data Layer,
            Legacy Description, Color Band Order, Asset Name,
            Per Pixel X, Per Pixel Y, Coordinate Reference
            System from Pixels, Age in Days, Ingest Date,
            Company Name, Copyright, NIIRS, and Geometry
            
        DB - Path to database
    """

    try:
        conn = sqlite3.connect(db)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('mod_spatialite')")
        
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS whale_geointdiscovery(
                id VARCHAR(32) PRIMARY KEY,
                aoi_id VARCHAR(4),
                legacy_id VARCHAR(16),
                factory_order_number VARCHAR(12),
                acquisition_date SMALLDATETIME,
                source VARCHAR(9),
                source_unit VARCHAR(5),
                product_type VARCHAR(36),
                cloud_cover NUMERIC(3,2),
                off_nadir_angle NUMERIC(2, 3),
                sun_elevation NUMERIC(3, 3),
                sun_azimuth NUMERIC(3, 3),
                ground_sample_distance NUMERIC(2, 2),
                data_layer VARCHAR(10),
                legacy_description VARCHAR(12),
                color_band_order VARCHAR(3),
                asset_name VARCHAR(8),
                per_pixel_x NUMERIC(2, 2),
                per_pixel_y NUMERIC(2, 2),
                crs_from_pixels VARCHAR(10),
                age_days NUMERIC(4, 1),
                ingest_date SMALLDATETIME,
                company_name VARCHAR(12),
                copyright VARCHAR(37),
                niirs NUMERIC(1, 1),
                geometry POLYGON,
                FOREIGN KEY (aoi_id)
                    REFERENCES aoi(id)
            )
        ''')
        
        conn.commit()
        conn.close()

        print("Successfully created table WHALE EARTHEXPLORER")
    
    with Exception as e:
        print(f"Failed to create table with exception: {e}")

def create_maxargeospatialplatform(db):
    """ When provided with a path to a SpatiaLite database, create the
            table WHALE MAXARGEOSPATIALPLATFORM if it does not exist.

        FIELDS: ID, AOI ID, Platform, Instruments, Ground Sampling Distance,
            Panchromatic Image Resolution (average), Multispectral Image
            Resolution (average), Datetime, Off Nadir, Azimuth, Sun Azimuth,
            Sun Elevation, and Bounding Box.
            
        DB - Path to database
    """

    try:
        conn = sqlite3.connect(db)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('mod_spatialite')")
        
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS whale_maxargeospatialplatform(
                id VARCHAR(16) PRIMARY KEY,
                aoi_id VARCHAR(4),
                platform VARCHAR(11),
                instruments VARCHAR(4),
                gsd NUMERIC(2, 3),
                pan_resolution_avg NUMERIC(2, 3),
                multi_resolution_avg NUMERIC(2, 3),
                datetime DATETIME2,
                off_nadir NUMERIC(2, 3),
                azimuth NUMERIC(3, 3),
                sun_azimuth NUMERIC(3, 3),
                sun_elevation NUMERIC(3, 3),
                bbox POLYGON,
                FOREIGN KEY (aoi_id)
                    REFERENCES aoi(id)
            )
        ''')
        
        conn.commit()
        conn.close()

        print("Successfully created table WHALE MAXARGEOSPATIALPLATFORM")
    
    with Exception as e:
        print(f"Failed to create table with exception: {e}")

def create_etl(db):
    """ When provided with a path to a SpatiaLite database, create the
            table ETL if it does not exist. This is a denormalized table
            which needs to be updated based on triggers created by
            CREATE ETL TRIGGERS. The ETL table represents the initializing
            table for further work within the WHALE application.

        FIELDS: AOI ID, ID, Vendor ID, Entity ID, Vendor, Satellite
            Pixel Size X, Pixel Size Y, Date, Publish Date, Geometry
            Sea State Qualitative, Sea State Quantitative, and
            Sharability.
            
        DB - Path to database
    """

    try:
        conn = sqlite3.connect(db)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('mod_spatialite')")
        
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE etl AS    
                SELECT 'EE' AS table_name,
                       e.aoi_id_id AS aoi_id,
                       e.catalog_id AS id,
                       e.vendor_id AS vendor_id,
                       e.entity_id AS entity_id,
                       e.vendor as vendor,
                       e.satellite AS platform,
                       e.pixel_size_x AS pixel_size_x,
                       e.pixel_size_y AS pixel_size_y,
                       e.acquisition_date AS date,
                       Date(e.publish_date) AS publish_date,
                       AsText(e.bounds) as geometry
                   FROM whale_earthexplorer e
                
                UNION
                
                SELECT 'GEGD' AS table_name,
                       g.aoi_id_id AS aoi_id,
                       g.legacy_id AS id,
                       NULL AS vendor_id,
                       NULL AS entity_id,
                       g.company_name as vendor,
                       g.source AS platform,
                       g.per_pixel_x AS pixel_size_x,
                       g.per_pixel_y AS pixel_size_y,
                       Date(g.acquisition_date) AS date,
                       NULL AS publish_date,
                       AsText(g.geometry) AS geometry
                   FROM whale_geointdiscovery g
                LEFT JOIN whale_earthexplorer e ON g.legacy_id = e.catalog_id
                    WHERE
                        e.catalog_id IS NULL
                
                UNION
        
                SELECT 'MGP' AS table_name,
                       m.aoi_id_id AS aoi_id,
                       m.id AS id,
                       NULL AS vendor_id,
                       NULL AS entity_id,
                       "Maxar" AS vendor,
                       m.platform AS platform,
                       m.gsd AS pixel_size_x,
                       m.gsd AS pixel_size_y,
                       Date(datetime) AS date,
                       NULL AS publish_date,
                       AsText(m.bbox) AS geometry
                   FROM whale_maxargeospatialplatform m
                LEFT JOIN whale_earthexplorer e ON m.id = e.catalog_id
                LEFT JOIN whale_geointdiscovery g ON m.id = g.legacy_id
                    WHERE
                        e.catalog_id IS NULL AND g.legacy_id IS NULL;
        ''')
        
        c.execute('''ALTER TABLE etl ADD COLUMN sea_state_qual VARVHAR(15)''')
        c.execute('''ALTER TABLE etl ADD COLUMN sea_state_quant NUMERIC(2, 2)''')
        c.execute('''ALTER TABLE etl ADD COLUMN shareable VARVHAR(3)''')
        
        conn.commit()
        conn.close()

        print("Successfully created table ETL")
    
    with Exception as e:
        print(f"Failed to create table with exception: {e}")

def create_etl_triggers(db):
    """ When provided with a path to a SpatiaLite database, create the
            ETL table triggers.
            
        DB - Path to database
    """

    try:
        conn = sqlite3.connect(db)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('mod_spatialite')")
        
        c = conn.cursor()
        
        c.execute('''
            CREATE TRIGGER update_etl_after_ee_insert
                AFTER INSERT ON whale_earthexplorer
                    BEGIN
                        INSERT INTO etl (table_name, aoi_id, id, vendor_id, entity_id, vendor, platform, pixel_size_x, pixel_size_y, date, publish_date, geometry)
                        SELECT
                           'EE' AS table_name,
                           NEW.aoi_id_id AS aoi_id,
                           NEW.catalog_id AS id,
                           NEW.vendor_id AS vendor_id,
                           NEW.entity_id AS entity_id,
                           NEW.vendor as vendor,
                           NEW.satellite AS platform,
                           NEW.pixel_size_x AS pixel_size_x,
                           NEW.pixel_size_y AS pixel_size_y,
                           NEW.acquisition_date AS date,
                           Date(NEW.publish_date) AS publish_date,
                           AsText(NEW.bounds) as geometry;
        
                        INSERT INTO trigger_log (trigger_name, action, log_message)
                        VALUES ('update_etl_after_ee_insert', 'INSERT', 'trigger fired after INSERT on whale_earthexplorer');
                    END;
        ''')
        
        conn.commit()
        conn.close()

        print("Successfully created table ETL after EE insert")
    
    with Exception as e:
        print(f"Failed to create ETL after Earth Explorer insert trigger with exception: {e}")

    try:
        conn = sqlite3.connect(db)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('mod_spatialite')")
        
        c = conn.cursor()
        
        c.execute('''
            CREATE TRIGGER update_etl_after_gegd_insert
                AFTER INSERT ON whale_geointdiscovery
                    BEGIN
                        INSERT INTO etl (table_name, aoi_id, id, vendor_id, entity_id, vendor, platform, pixel_size_x, pixel_size_y, date, publish_date, geometry)
                        SELECT
                           'GEGD' AS table_name,
                           NEW.aoi_id_id AS aoi_id,
                           NEW.legacy_id AS id,
                           NULL AS vendor_id,
                           NULL AS entity_id,
                           NEW.company_name as vendor,
                           NEW.source AS platform,
                           NEW.per_pixel_x AS pixel_size_x,
                           NEW.per_pixel_y AS pixel_size_y,
                           Date(NEW.acquisition_date) AS date,
                           NULL AS publish_date,
                           AsText(NEW.geometry) as geometry;
        
                        INSERT INTO trigger_log (trigger_name, action, log_message)
                        VALUES ('update_etl_after_gegd_insert', 'INSERT', 'trigger fired after INSERT on whale_geointdiscovery');
                    END;
        ''')
        
        conn.commit()
        conn.close()

        print("Successfully created table ETL after GEGD insert")
        
    with Exception as e:
        print(f"Failed to create ETL after Global Enhanced GEOINT Delivery insert trigger with exception: {e}")

    try:
        conn = sqlite3.connect(db)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('mod_spatialite')")
        
        c = conn.cursor()
        
        c.execute('''
            CREATE TRIGGER update_etl_after_mgp_insert
                AFTER INSERT ON whale_maxargeospatialplatform
                    BEGIN
                        INSERT INTO etl (table_name, aoi_id, id, vendor_id, entity_id, vendor, platform, pixel_size_x, pixel_size_y, date, publish_date, geometry)
                        SELECT
                           'MGP' AS table_name,
                           NEW.aoi_id_id AS aoi_id,
                           NEW.id AS id,
                           NULL AS vendor_id,
                           NULL AS entity_id,
                           "Maxar" AS vendor,
                           NEW.platform AS platform,
                           NEW.gsd AS pixel_size_x,
                           NEW.gsd AS pixel_size_y,
                           Date(NEW.datetime) AS date,
                           NULL AS publish_date,
                           AsText(NEW.bbox) as geometry;
        
                        INSERT INTO trigger_log (trigger_name, action, log_message)
                        VALUES ('update_etl_after_mgp_insert', 'INSERT', 'trigger fired after INSERT on whale_maxargeospatialplatform');
                    END;
        ''')
        
        conn.commit()
        conn.close()

        print("Successfully created table ETL after MGP insert")
        
    with Exception as e:
        print(f"Failed to create ETL after Maxar Geospatial Platform insert trigger with exception: {e}")

def create_poitnsofinterest(db):
    """ When provided with a path to a SpatiaLite database, create the
            WHALE POINTSOFINTEREST table.

        FIELDS: ID, Vendor ID, Entity ID, CID, DAR, POI, Sample Index,
            Latitude, Longitude, Email, Client IP, Out Time, In Time,
            User Label, Confidence, Species, and Comments.
            
        DB - Path to database
    """

    try:
        conn = sqlite3.connect(db)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('mod_spatialite')")
        
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS exploit(
                id,
                vendor_id,
                entity_id,
                cid  VARCHAR(20),
                dar INTEGER,
                poi INTEGER,
                sample_idx VARCHAR(40),
                latitude NUMERIC(2, 6),
                longitude NUMERIC(3, 6),
                email VARCHAR(35),
                client_ip VARCHAR(13),
                out_time DATE,
                in_time DATE,
                user_label VARCHAR(10),
                confidence VARCHAR(10),
                species VARCHAR(25),
                comments VARCHAR(500),
                FOREIGN KEY (id)
                    REFERENCES etl(id),
                FOREIGN KEY (vendor_id)
                    REFERENCES etl(vendor_id),
                FOREIGN KEY (entity_id)
                    REFERENCES etl(entity_id),
                FOREIGN KEY (cid)
                    REFERENCES tasking(id),
                FOREIGN KEY (dar)
                    REFERENCES tasking(dar)
            )
        ''')
        
        conn.commit()
        conn.close()

        print("Successfully created table WHALE POINTSOFINTEREST")
    
    with Exception as e:
        print(f"Failed to create table with exception: {e}")