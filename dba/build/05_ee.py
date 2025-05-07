#!/usr/bin/env python
# coding: utf-8

# # Whale EarthExplorer
# Builds the `whale_earthexplorer` table. This table will be populated by pulling in USGS EarthExplorer imagery records from the API.
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
import shapely
from shapely.geometry import Polygon
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
c.execute('''DROP TABLE IF EXISTS whale_earthexplorer''')
conn.commit()
conn.close()

# ### Create `whale_earthexplorer` table

# In[4]:


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

# # End
