#!/usr/bin/env python
# coding: utf-8

# # Whale Maxar Geospatial Platform
# Builds the `whale_maxargeospatialplatform` table. This table will be populated by pulling in Maxar Geospatial Platform imagery records from the API.
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
c.execute('''DROP TABLE IF EXISTS whale_maxargeospatialplatform''')
conn.commit()
conn.close()

# ### Create `whale_maxargeospatialplatform` table

# In[4]:


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

# # End
