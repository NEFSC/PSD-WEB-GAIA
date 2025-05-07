#!/usr/bin/env python
# coding: utf-8

# # ETL Table Triggers
# Updates the `etl` table based on updates to `whale_earthexplorer`, `whale_geointdiscovery`, and `whale_maxargeospatialplatform` tables.
# 
# ### Import libraries

# In[1]:


import sqlite3

# ### User defined variables

# In[2]:


db = "../../db.sqlite3"

# ### Drop triggers if they exist

# In[3]:


conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")
c = conn.cursor()

c.execute('''DROP TRIGGER IF EXISTS update_etl_after_ee_insert''')
c.execute('''DROP TRIGGER IF EXISTS update_etl_after_gegd_insert''')
c.execute('''DROP TRIGGER IF EXISTS update_etl_after_mgp_insert''')

conn.commit()
conn.close()

# ### Create triggers

# In[4]:


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

# In[5]:


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

# In[6]:


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

# # End
