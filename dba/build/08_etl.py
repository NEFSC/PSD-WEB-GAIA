#!/usr/bin/env python
# coding: utf-8

# # Extracted, transform, and Load
# Builds the `etl` table from the `whale_earthexplorer`, `whale_geointdiscovery`, and `whale_maxargeospatialplatform` tables.
# 
# ### Import libraries

# In[1]:


# Basic stack
from datetime import datetime

# Web Stack
import json
import requests

# Database stack
import sqlite3

# Data Science stack
import shapely.wkt
import pandas as pd
import geopandas as gpd
import folium

# ### User defined variables

# In[2]:


db = "../../db.sqlite3"

# ### Drop table
# This is for demonstration and troubleshooting purposes.

# In[3]:


conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

c = conn.cursor()
c.execute('''DROP TABLE IF EXISTS etl''')
conn.commit()
conn.close()

# ### Create `etl` table

# In[6]:


conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

c = conn.cursor()

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

conn.commit()
conn.close()

# # End
