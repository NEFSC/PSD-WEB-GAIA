#!/usr/bin/env python
# coding: utf-8

# # Initializer
# Initializes the database and ensures that it is spatially enabled, i.e. SpatiaLite.
# 
# ### Import libraries

# Database stack
import sqlite3

db = "../../db.sqlite3"

conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

c = conn.cursor()
c.execute('''SELECT InitSpatialMetaData();''')
conn.commit()
conn.close()