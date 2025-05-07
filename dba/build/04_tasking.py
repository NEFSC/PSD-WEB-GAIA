#!/usr/bin/env python
# coding: utf-8

# # Commerical Satellite Imagery Tasking via the CSSP Imagery Derived Requirements Tool
# Builds the `tasking` table from a locally stored Excel spreadsheet that should be created from a Google Drive Sheet created by Meredith Sackett.
# 
# ### Import libraries

# In[1]:


# Basic stack
import os
import shutil
from glob import glob
import warnings

# Web stack
import json

# Database stack
import sqlite3

# Data Science stack
import numpy as np
import pyproj
from pyproj import CRS
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
import utm
import pandas as pd
import geopandas as gpd
import shapely
from shapely import to_geojson
from shapely.ops import transform
from shapely.geometry import Polygon
from fiona.drvsupport import supported_drivers
import folium

# ### Environmental settings

# In[2]:


warnings.filterwarnings("ignore")

# ### User defined variables

# In[3]:


db = "../../db.sqlite3"
dar_spreadsheet = "../../data/databases/Tracking - CIDR Requests - live whales.xlsx"

# ### User defined functions

# In[4]:


def insert_tasking(c, dar_id, aoi_id):
    """ Inserts CIDR DARs into the DARS Data Table. The DAR
            is the Primary Key for the datatable since it is
            unique.

        C - A cursor
        DAR ID - An Entity ID value from EarthExplorer
    """
    sql_string = f"INSERT INTO tasking(dar, aoi) VALUES (\"{dar_id}\", \"{aoi_id}\")"
    c.execute(sql_string)

# ### Read in Excel spreadsheet, show the head

# In[5]:


df = pd.read_excel(dar_spreadsheet, sheet_name = 'Master')
print("Your initial DAR spreadsheet is {} in size".format(df.shape))

df.head(2)

# ### Drop table
# This is for demonstration and troubleshooting purposes.

# In[6]:


conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

c = conn.cursor()
c.execute('''DROP TABLE IF EXISTS tasking''')
conn.commit()
conn.close()

# ### Create `tasking` table

# In[7]:


conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS tasking(
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

# ### Filter to only columns that will be in database

# In[8]:


keep_columns = ['DAR', 'AOI', 'Location', 'Species', 'Submitted by:', 'Date Entered',
                'Acquisition Start', 'Acquisition End', 'ONA Restriction - WV2',
                'ONA Restriction - WV3', 'Tasking Description', 'Comments', 'Status of Tasking',
                'Output Format', 'Processing Level', 'Website link', 'Permission to Share']
df = df[keep_columns]
df.head(2)

# ### Rename columns to those in database

# In[9]:


rename_columns = {'DAR': 'dar', 'AOI': 'aoi', 'Location': 'location', 'Species': 'target',
                  'Submitted by:': 'requestor', 'Date Entered': 'date_entered',
                  'Acquisition Start': 'acquisition_start', 'Acquisition End': 'acquisition_end',
                  'ONA Restriction - WV2': 'ona_wv2', 'ONA Restriction - WV3': 'ona_wv3',
                  'Tasking Description': 'tasking_description', 'Comments': 'comments',
                  'Status of Tasking': 'status', 'Output Format': 'output_format',
                  'Processing Level': 'processing_level', 'Website link': 'website_link',
                  'Permission to Share': 'permission_to_share'}
df = df.rename(columns=rename_columns)
df.head(2)

# ### Insert values from spreadsheet into `tasking` table
# Note that some of the DAR values are `NaN`.

# In[10]:


conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

c = conn.cursor()

for i, row in df.iterrows():
    try:
        dar = row['dar']
        aoi = row['aoi']
        location = row['location']
        target = row['target']
        requestor = row['requestor']
        date_entered = row['date_entered']
        acquisition_start = row['acquisition_start']
        acquisition_end = row['acquisition_end']
        ona_wv2 = row['ona_wv2']
        ona_wv3 = row['ona_wv3']
        tasking_description = row['tasking_description']
        comments = row['comments']
        status = row['status']
        output_format = row['output_format']
        processing_level = row['processing_level']
        website_link = row['website_link']
        permission_to_share = row['permission_to_share']
        try:
            sql_string = f"INSERT INTO tasking(dar, aoi, location, target, requestor," +\
                            f"date_entered, acquisition_start, acquisition_end, ona_wv2," +\
                            f"ona_wv3, tasking_description, comments, status, output_format," +\
                            f"processing_level, website_link, permission_to_share)" +\
                            f"VALUES (\"{dar}\", \"{aoi}\", \"{location}\", \"{target}\"," +\
                                f"\"{requestor}\", \"{date_entered}\", \"{acquisition_start}\"," +\
                                f"\"{acquisition_end}\",\"{ona_wv2}\",\"{ona_wv3}\",\"{tasking_description}\"," +\
                                f"\"{comments}\",\"{status}\",\"{output_format}\",\"{processing_level}\"," +\
                                f"\"{website_link}\",\"{permission_to_share}\")"
            c.execute(sql_string)
        except Exception as e:
            print("\tException: {} was raised for DAR ID {}".format(e, dar))
    except Exception as e:
        print("Exception: {} was raised for iteration {}".format(e, i))
print("Done updating DARS table!")

conn.commit()
conn.close()

# ### Select new information, review it for validation

# In[11]:


conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

df = pd.read_sql_query(f"SELECT * FROM tasking", conn)

conn.commit()
conn.close()

df.head()

# # End
