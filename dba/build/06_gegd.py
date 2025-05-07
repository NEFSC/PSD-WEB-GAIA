#!/usr/bin/env python
# coding: utf-8

# # Whale GEOINT Discovery
# Builds the `whale_geointdiscovery` table. This table will be populated by pulling in Global Enhanced GEOINT Delivery imagery records from the API.
# 
# ### Import libraries

# In[1]:


# Basic stack
from datetime import datetime

# Web Stack
import json
import requests
import getpass

# Database stack
import sqlite3

# Data Science stack
import shapely
from shapely.geometry import box, Polygon
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
c.execute('''DROP TABLE IF EXISTS whale_geointdiscovery''')
conn.commit()
conn.close()

# ### Create `whale_geointdiscovery` table

# In[4]:


conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")
# conn.execute("")

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

# # End
