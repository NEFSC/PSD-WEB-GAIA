#!/usr/bin/env python
# coding: utf-8

# # Initializer
# Initializes the database and ensures that it is spatially enabled, i.e. SpatiaLite.

# 20250507 This document attempts to merge several initialization scripts from Jupyter Notebooks.
# It does build from an empty database but stops short of providing a connective bridge to current database state as of 20250507.

import sqlite3
import pandas as pd

db = "../../db.sqlite3"

targets = "../../data/databases/targets.xlsx"
people = "../../data/databases/people.xlsx"
tasking = "../../data/databases/tasking.xlsx"
aoi = "../../data/databases/aoi.csv"

conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

c = conn.cursor()
c.execute('''SELECT InitSpatialMetaData();''')

# Targets
df_targets = pd.read_excel(targets)
df_targets.to_sql('targets', conn, if_exists='replace', index=True, index_label='id')

# People
df_people = pd.read_excel(people)
df_people.to_sql('people', conn, if_exists='replace', index=True, index_label='id')

# Tasking
df_tasking = pd.read_excel(tasking)
df_tasking['dar'] = df_tasking['dar'].astype('Int64')
df_tasking['aoi'] = df_tasking['aoi'].astype('Int64')
df_tasking['date_entered'] = df_tasking['date_entered'].dt.date
df_tasking['acquisition_start'] = df_tasking['acquisition_start'].dt.date
df_tasking['acquisition_end'] = df_tasking['acquisition_end'].dt.date
df_tasking.to_sql('tasking', conn, if_exists='replace', index=True, index_label='id')

# AOI
df_aoi = pd.read_csv(aoi)
geometry_column = df_aoi.pop('geometry')  # Remove and store geometry column
df_aoi.to_sql('aoi', conn, if_exists='replace', index=False)
c.execute('SELECT AddGeometryColumn("aoi", "geometry", 4326, "POLYGON");')
for idx, geom in enumerate(geometry_column):
	c.execute('UPDATE aoi SET geometry = GeomFromText(?, 4326) WHERE rowid = ?;', (geom, idx + 1))
conn.commit()

# Earth Explorer
c.execute('DROP TABLE IF EXISTS whale_earthexplorer')
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

# GEOINT Discovery
c.execute('DROP TABLE IF EXISTS whale_geointdiscovery')
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

# Maxar Geospatial Platform
c.execute('DROP TABLE IF EXISTS whale_maxargeospatialplatform')
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

# Extracted, transform, and Load
c.execute('DROP TABLE IF EXISTS etl')
c.execute('''
    CREATE TABLE etl AS    
        SELECT 'EE' AS table_name,
               e.aoi_id AS aoi_id,
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
               g.aoi_id AS aoi_id,
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
               m.aoi_id AS aoi_id,
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

